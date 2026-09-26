from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user, oauth2_scheme, require_roles
from app.models.token import RevokedToken
from app.models.user import RoleName, User
from app.models.password_reset import PasswordResetRequest, PasswordResetRequestStatus
from app.schemas.auth import (
    AdminResolvePasswordResetRequest,
    ForgotPasswordRequest,
    LoginRequest,
    PasswordResetRequestOut,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode_token,
    verify_password,
)
from app.services.audit import log_action


router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(
        db,
        user.id,
        "USER_REGISTERED",
        "User",
        user.id,
    )

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Standard OAuth2 password-flow login.

    The username field should contain the user's email.
    """

    user = (
        db.query(User)
        .filter(User.email == form_data.username)
        .first()
    )

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
    )

    refresh_token = create_refresh_token(
        subject=user.id,
    )

    log_action(
        db,
        user.id,
        "USER_LOGIN",
        "User",
        user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post("/login-json", response_model=TokenResponse)
def login_json(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    JSON-body login used by the web and Android clients.
    """

    user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if not user or not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
    )

    refresh_token = create_refresh_token(
        subject=user.id,
    )

    log_action(
        db,
        user.id,
        "USER_LOGIN",
        "User",
        user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = safe_decode_token(token)

    jti = payload.get("jti")
    exp = payload.get("exp")

    if jti and exp:
        revoked = RevokedToken(
            jti=jti,
            expires_at=datetime.fromtimestamp(
                exp,
                tz=timezone.utc,
            ),
        )

        db.add(revoked)
        db.commit()

    log_action(
        db,
        current_user.id,
        "USER_LOGOUT",
        "User",
        current_user.id,
    )

    return None


@router.get("/me", response_model=UserOut)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


GENERIC_FORGOT_PASSWORD_RESPONSE = {
    "message": (
        "If an account with that email exists, an administrator has "
        "been notified and will get in touch with a new password."
    )
}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Records a "forgot password" request for an administrator to handle.

    There is no email or token involved: an administrator sees the request
    on the dashboard and hands the user a new password directly (in person,
    by phone, etc). The response is intentionally generic so that an
    attacker cannot discover whether an email address exists.
    """

    user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if not user or not user.is_active:
        return GENERIC_FORGOT_PASSWORD_RESPONSE

    # Avoid piling up duplicate pending requests if the user submits the
    # form more than once before an admin has gotten to it.
    existing_pending = (
        db.query(PasswordResetRequest)
        .filter(
            PasswordResetRequest.user_id == user.id,
            PasswordResetRequest.status == PasswordResetRequestStatus.PENDING,
        )
        .first()
    )

    if not existing_pending:
        reset_request = PasswordResetRequest(
            user_id=user.id,
            status=PasswordResetRequestStatus.PENDING,
        )

        db.add(reset_request)
        db.commit()

        log_action(
            db,
            user.id,
            "PASSWORD_RESET_REQUESTED",
            "User",
            user.id,
        )

    return GENERIC_FORGOT_PASSWORD_RESPONSE


@router.get(
    "/password-reset-requests",
    response_model=list[PasswordResetRequestOut],
)
def list_password_reset_requests(
    status_filter: PasswordResetRequestStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR)),
):
    """
    Lists "forgot password" requests for administrators to act on.
    Defaults to pending requests only; pass ?status_filter=RESOLVED to see
    the history of who was already helped.
    """

    query = db.query(PasswordResetRequest)

    if status_filter is not None:
        query = query.filter(PasswordResetRequest.status == status_filter)
    else:
        query = query.filter(
            PasswordResetRequest.status == PasswordResetRequestStatus.PENDING
        )

    requests = query.order_by(PasswordResetRequest.created_at.desc()).all()

    return [
        PasswordResetRequestOut(
            id=r.id,
            user_id=r.user_id,
            user_full_name=r.user.full_name,
            user_email=r.user.email,
            status=r.status,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
            resolved_by_id=r.resolved_by_id,
            resolved_by_name=r.resolved_by.full_name if r.resolved_by else None,
        )
        for r in requests
    ]


@router.post(
    "/password-reset-requests/{request_id}/resolve",
    response_model=PasswordResetRequestOut,
)
def resolve_password_reset_request(
    request_id: str,
    payload: AdminResolvePasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR)),
):
    """
    Sets the user's password to the value the administrator chose, and
    marks the request as resolved. The administrator is responsible for
    communicating the new password to the user themselves.
    """

    reset_request = (
        db.query(PasswordResetRequest)
        .filter(PasswordResetRequest.id == request_id)
        .first()
    )

    if not reset_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Password reset request not found",
        )

    if reset_request.status == PasswordResetRequestStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This request has already been resolved",
        )

    user = (
        db.query(User)
        .filter(User.id == reset_request.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hashed_password = hash_password(payload.new_password)

    now = datetime.now(timezone.utc)
    reset_request.status = PasswordResetRequestStatus.RESOLVED
    reset_request.resolved_at = now
    reset_request.resolved_by_id = current_user.id

    db.commit()
    db.refresh(reset_request)

    log_action(
        db,
        current_user.id,
        "PASSWORD_RESET_RESOLVED",
        "User",
        user.id,
    )

    return PasswordResetRequestOut(
        id=reset_request.id,
        user_id=reset_request.user_id,
        user_full_name=user.full_name,
        user_email=user.email,
        status=reset_request.status,
        created_at=reset_request.created_at,
        resolved_at=reset_request.resolved_at,
        resolved_by_id=reset_request.resolved_by_id,
        resolved_by_name=current_user.full_name,
    )
