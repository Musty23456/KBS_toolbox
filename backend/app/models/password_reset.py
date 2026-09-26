import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class PasswordResetRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"


class PasswordResetRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tracks a "forgot password" request so an administrator can see it in the
    dashboard and hand the user a new password directly (in person, by
    phone, etc). There is no self-service email/token flow: only an
    administrator can resolve a request, by choosing the new password
    themselves.
    """

    __tablename__ = "password_reset_requests"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[PasswordResetRequestStatus] = mapped_column(
        Enum(PasswordResetRequestStatus),
        nullable=False,
        default=PasswordResetRequestStatus.PENDING,
        index=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="password_reset_requests",
        foreign_keys=[user_id],
    )

    resolved_by = relationship(
        "User",
        foreign_keys=[resolved_by_id],
    )
