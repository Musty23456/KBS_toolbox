import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class RoleName(str, enum.Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    SUPERVISOR = "SUPERVISOR"
    ENUMERATOR = "ENUMERATOR"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleName] = mapped_column(Enum(RoleName), nullable=False, default=RoleName.ENUMERATOR)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    submissions = relationship("Submission", back_populates="submitted_by", foreign_keys="Submission.submitted_by_id")
    audit_logs = relationship("AuditLog", back_populates="actor")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
