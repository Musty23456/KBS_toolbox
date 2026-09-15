from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class RevokedToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tracks JWT access-token IDs (jti) that were explicitly logged out before
    their natural expiry, so a stolen/leaked token can be invalidated even
    though JWTs are otherwise stateless.
    """

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
