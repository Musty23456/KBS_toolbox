from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Translation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "translations"
    __table_args__ = (UniqueConstraint("survey_id", "entity_type", "entity_id", "field", "language_code", name="uq_translation_target"),)

    survey_id: Mapped[str] = mapped_column(String(36), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)  # SURVEY, SECTION, GROUP, QUESTION, CHOICE
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(50), nullable=False)  # title, description, label, hint
    language_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
