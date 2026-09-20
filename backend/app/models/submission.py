import enum

from sqlalchemy import Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.review import ReviewStatus


class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class Submission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "submissions"
    __table_args__ = (
        # The client-generated UUID is the idempotency key: replaying the same
        # upload (e.g. after a dropped connection) never creates a duplicate.
        UniqueConstraint("client_submission_uuid", name="uq_submission_client_uuid"),
    )

    survey_id: Mapped[str] = mapped_column(String(36), ForeignKey("surveys.id"), nullable=False)
    survey_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("survey_versions.id"), nullable=False)
    submitted_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    # Generated on-device at capture time; used to deduplicate retried uploads.
    client_submission_uuid: Mapped[str] = mapped_column(String(36), nullable=False)

    review_status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.RECEIVED, nullable=False)

    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus), default=SubmissionStatus.UPLOADED, nullable=False
    )

    gps_latitude: Mapped[float] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[float] = mapped_column(Float, nullable=True)

    collected_at: Mapped[str] = mapped_column(String(64), nullable=True)  # ISO timestamp captured on-device
    synced_at: Mapped[str] = mapped_column(String(64), nullable=True)  # ISO timestamp when server confirmed

    survey = relationship("Survey", back_populates="submissions")
    survey_version = relationship("SurveyVersion", back_populates="submissions")
    submitted_by = relationship("User", back_populates="submissions", foreign_keys=[submitted_by_id])
    answers = relationship("SubmissionAnswer", back_populates="submission", cascade="all, delete-orphan")
    sync_metadata = relationship("SyncMetadata", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("SubmissionReview", back_populates="submission", cascade="all, delete-orphan", order_by="SubmissionReview.created_at.desc()")


class SubmissionAnswer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "submission_answers"

    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("questions.id"), nullable=False)

    # A flexible single text column keeps this normalized and simple: numbers,
    # dates, choice values and JSON-encoded multi-select arrays are all stored
    # as their canonical string form and interpreted using the question type.
    value_text: Mapped[str] = mapped_column(Text, nullable=True)

    # For media answers (photo/audio/signature), this stores a reference
    # (object storage key or file path) rather than the binary itself.
    media_reference: Mapped[str] = mapped_column(String(1000), nullable=True)
    group_instance_index: Mapped[int] = mapped_column(nullable=True)

    submission = relationship("Submission", back_populates="answers")
    question = relationship("Question")
