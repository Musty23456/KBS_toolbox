import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SurveyStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Survey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "surveys"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[SurveyStatus] = mapped_column(Enum(SurveyStatus), default=SurveyStatus.DRAFT, nullable=False)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    versions = relationship(
        "SurveyVersion", back_populates="survey", order_by="SurveyVersion.version_number", cascade="all, delete-orphan"
    )
    submissions = relationship("Submission", back_populates="survey")


class SurveyVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Every publish of a survey creates a new immutable version. Submissions
    always reference the exact version they were collected against, so
    editing a live survey never corrupts historical data.
    """

    __tablename__ = "survey_versions"

    survey_id: Mapped[str] = mapped_column(String(36), ForeignKey("surveys.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)

    survey = relationship("Survey", back_populates="versions")
    questions = relationship(
        "Question", back_populates="survey_version", order_by="Question.order_index", cascade="all, delete-orphan"
    )
    submissions = relationship("Submission", back_populates="survey_version")
