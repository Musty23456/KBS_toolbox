import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ReviewStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    UNDER_REVIEW = "UNDER_REVIEW"
    HAS_ISSUES = "HAS_ISSUES"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESUBMIT = "RESUBMIT"


class SubmissionReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "submission_reviews"

    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False, index=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    submission = relationship("Submission", back_populates="reviews")
    reviewer = relationship("User")
