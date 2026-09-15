from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.submission import SubmissionStatus


class AnswerIn(BaseModel):
    question_id: str
    value_text: str | None = None
    media_reference: str | None = None


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    question_id: str
    value_text: str | None
    media_reference: str | None


class SubmissionCreate(BaseModel):
    """Payload the Android app posts, either live or from its offline queue."""

    client_submission_uuid: str = Field(description="UUID generated on-device at capture time; used for dedup")
    survey_id: str
    survey_version_id: str
    collected_at: str | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    answers: list[AnswerIn] = []


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    survey_id: str
    survey_version_id: str
    submitted_by_id: str
    client_submission_uuid: str
    status: SubmissionStatus
    gps_latitude: float | None
    gps_longitude: float | None
    collected_at: str | None
    synced_at: str | None
    created_at: datetime
    answers: list[AnswerOut] = []
