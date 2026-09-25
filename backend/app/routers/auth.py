
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user, oauth2_scheme
from app.models.token import RevokedToken
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode_token,
    verify_password,
)
from app.services.audit import log_action
from app.services.email import send_password_reset_email
router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, user.id, "USER_REGISTERED", "User", user.id)
    return user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Accepts standard OAuth2 password-flow form fields (username, password) so
    it works with FastAPI's interactive docs and any standard OAuth2 client.
    `username` should be the user's email.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token = create_refresh_token(subject=user.id)
    log_action(db, user.id, "USER_LOGIN", "User", user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post("/login-json", response_model=TokenResponse)
def login_json(payload: LoginRequest, db: Session = Depends(get_db)):
    """JSON-body variant of /login, more convenient for the Android/web clients."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token = create_refresh_token(subject=user.id)
    log_action(db, user.id, "USER_LOGIN", "User", user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: str = Depends(oauth2_scheme), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = safe_decode_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti:
        revoked = RevokedToken(jti=jti, expires_at=datetime.fromtimestamp(exp, tz=timezone.utc))
        db.add(revoked)
        db.commit()
    log_action(db, current_user.id, "USER_LOGOUT", "User", current_user.id)
    return None


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Starts the password reset flow.

    The response is intentionally generic so that attackers cannot
    discover whether an email address exists in the system.
    """
    generic_response = {
        "message": "If an account with that email exists, a password reset link has been sent."
    }

    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not user.is_active:
        return generic_response

    now = datetime.now(timezone.utc)

    # Invalidate previous unused reset tokens for this user.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update(
        {"used_at": now},
        synchronize_session=False,
    )

    # Generate a secure random token.
    raw_token = secrets.token_urlsafe(32)

    # Store only the SHA-256 hash in the database.
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        ),
    )

    db.add(reset_token)
    db.commit()

    reset_url = (
        f"{settings.WEB_APP_URL.rstrip('/')}"
        f"/reset-password?token={quote(raw_token, safe='')}"
    )

        try:
        send_password_reset_email(
            to_email=user.email,
            full_name=user.full_name,
            reset_url=reset_url,
        )
    except Exception:
        # Do not expose SMTP errors or account existence to the client.
        # The token is removed if the email could not be sent.
        db.delete(reset_token)
        db.commit()

        return generic_response

    log_action(
        db,
        user.id,
        "PASSWORD_RESET_REQUESTED",
        "User",
        user.id,
    )

    return generic_response


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Resets a user's password using a valid, unused, non-expired token.
    """

    token_hash = hashlib.sha256(
        payload.token.encode("utf-8")
    ).hexdigest()

    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    if reset_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    now = datetime.now(timezone.utc)

    expires_at = reset_token.expires_at

    # SQLite may return timezone-naive datetimes.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user = db.query(User).filter(User.id == reset_token.user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    # Hash the new password using the same password system
    # already used by registration and login.
    user.hashed_password = hash_password(payload.new_password)

    # Make the reset token one-time-use.
    reset_token.used_at = now

    db.commit()

    log_action(
        db,
        user.id,
        "PASSWORD_RESET_COMPLETED",
        "User",
        user.id,
    )

    return {
        "message": "Password reset successful. You can now log in."
    }
