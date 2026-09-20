import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SurveyStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


# Many-to-many: which enumerators a survey has been restricted to. An empty
# assignment list means "open to every enumerator" (the historical default
# behaviour), so this table only needs a row per explicit assignment.
survey_assignments = Table(
    "survey_assignments",
    Base.metadata,
    Column("survey_id", String(36), ForeignKey("surveys.id"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
)


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
    assigned_enumerators = relationship("User", secondary=survey_assignments)


class SurveySection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "survey_sections"

    survey_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("survey_versions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    survey_version = relationship("SurveyVersion", back_populates="sections")
    questions = relationship("Question", back_populates="section")
    groups = relationship("QuestionGroup", back_populates="section")


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
    sections = relationship("SurveySection", back_populates="survey_version", order_by="SurveySection.order_index", cascade="all, delete-orphan")
    questions = relationship(
        "Question", back_populates="survey_version", order_by="Question.order_index", cascade="all, delete-orphan"
    )
    submissions = relationship("Submission", back_populates="survey_version")
