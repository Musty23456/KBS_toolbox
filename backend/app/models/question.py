import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class QuestionType(str, enum.Enum):
    SHORT_TEXT = "SHORT_TEXT"
    LONG_TEXT = "LONG_TEXT"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    DATE = "DATE"
    TIME = "TIME"
    DATETIME = "DATETIME"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    DROPDOWN = "DROPDOWN"
    YES_NO = "YES_NO"
    GPS = "GPS"
    PHOTO = "PHOTO"
    AUDIO = "AUDIO"
    SIGNATURE = "SIGNATURE"
    BARCODE = "BARCODE"


class Question(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "questions"

    survey_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("survey_versions.id"), nullable=False)
    section_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("survey_sections.id"), nullable=True)
    group_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("question_groups.id"), nullable=True)

    code: Mapped[str] = mapped_column(String(100), nullable=False)  # stable machine name, e.g. "gender"
    label: Mapped[str] = mapped_column(Text, nullable=False)  # human-readable prompt
    hint: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Validation
    min_value: Mapped[float] = mapped_column(Float, nullable=True)
    max_value: Mapped[float] = mapped_column(Float, nullable=True)
    min_length: Mapped[int] = mapped_column(Integer, nullable=True)
    max_length: Mapped[int] = mapped_column(Integer, nullable=True)
    regex_pattern: Mapped[str] = mapped_column(String(500), nullable=True)

    # Logic. Expressions use a small safe subset (see app/services/expressions.py),
    # referencing other questions in this survey version by their `code`.
    # Example relevance: "gender == 'FEMALE'"
    # Example calculation: "age_years * 12"
    relevance_expression: Mapped[str] = mapped_column(Text, nullable=True)
    calculation_expression: Mapped[str] = mapped_column(Text, nullable=True)
    default_value: Mapped[str] = mapped_column(String(500), nullable=True)

    # Cascading selection: choices of this question can be filtered by the
    # value picked in a parent question (e.g. LGA choices depend on State).
    cascade_parent_question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id"), nullable=True
    )

    survey_version = relationship("SurveyVersion", back_populates="questions")
    section = relationship("SurveySection", back_populates="questions")
    group = relationship("QuestionGroup", back_populates="questions")
    choices = relationship("Choice", back_populates="question", order_by="Choice.order_index", cascade="all, delete-orphan")


class Choice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "choices"

    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("questions.id"), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # For cascading selects: this choice is only offered when the cascade
    # parent question's answer equals `cascade_parent_value`.
    cascade_parent_value: Mapped[str] = mapped_column(String(255), nullable=True)

    question = relationship("Question", back_populates="choices")
