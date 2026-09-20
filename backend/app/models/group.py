from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

class QuestionGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "question_groups"
    survey_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("survey_versions.id"), nullable=False)
    section_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("survey_sections.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    min_repeats: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_repeats: Mapped[int | None] = mapped_column(Integer, nullable=True)
    survey_version = relationship("SurveyVersion", back_populates="groups")
    section = relationship("SurveySection", back_populates="groups")
    questions = relationship("Question", back_populates="group")
