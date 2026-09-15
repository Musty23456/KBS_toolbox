from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Location(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Generic hierarchical administrative geography (e.g. Country > State > LGA
    > Ward), used to power cascading location selects in surveys.
    """

    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 0 = top-level
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)

    children = relationship("Location", backref="parent", remote_side="Location.id")
