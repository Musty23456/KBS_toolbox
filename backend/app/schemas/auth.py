from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.password_reset import PasswordResetRequestStatus
from app.models.user import RoleName


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: RoleName = RoleName.ENUMERATOR


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class LogoutRequest(BaseModel):
    pass


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class AdminResolvePasswordResetRequest(BaseModel):
    """Payload an administrator submits to hand a user a new password."""

    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    user_full_name: str
    user_email: str
    status: PasswordResetRequestStatus
    created_at: datetime
    resolved_at: datetime | None
    resolved_by_id: str | None
    resolved_by_name: str | None = None
