from pydantic import BaseModel

class LocationOut(BaseModel):
    id: str
    name: str
    level: int
    parent_id: str | None = None

    model_config = {"from_attributes": True}

class SubmissionMapPoint(BaseModel):
    id: str
    survey_id: str
    survey_title: str
    submitted_by_id: str
    latitude: float
    longitude: float
    collected_at: str | None = None
    status: str
