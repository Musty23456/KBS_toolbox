import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SyncStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class SyncMetadata(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Server-side record of the sync lifecycle of one submission upload."""

    __tablename__ = "sync_metadata"

    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False, unique=True)
    client_device_id: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus), default=SyncStatus.SUCCESS, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_attempt_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    submission = relationship("Submission", back_populates="sync_metadata")


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "SURVEY_PUBLISHED"
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Survey"
    entity_id: Mapped[str] = mapped_column(String(36), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)  # free-form JSON string

    actor = relationship("User", back_populates="audit_logs")
