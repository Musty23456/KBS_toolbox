import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class MediaKind(str, enum.Enum):
    PHOTO = "PHOTO"
    AUDIO = "AUDIO"
    SIGNATURE = "SIGNATURE"


class SubmissionMedia(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "submission_media"

    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("questions.id"), nullable=False, index=True)
    group_instance_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kind: Mapped[MediaKind] = mapped_column(Enum(MediaKind), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    submission = relationship("Submission")
    question = relationship("Question")
