from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.review import ReviewStatus


class ReviewCreate(BaseModel):
    status: ReviewStatus
    comment: str | None = Field(default=None, max_length=5000)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    submission_id: str
    reviewer_id: str
    status: ReviewStatus
    comment: str | None
    created_at: datetime
    updated_at: datetime
