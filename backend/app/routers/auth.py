
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
