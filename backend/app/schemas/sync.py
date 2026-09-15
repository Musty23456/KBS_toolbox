from pydantic import BaseModel

from app.schemas.submission import SubmissionCreate, SubmissionOut
from app.schemas.survey import SurveyDetailOut


class SyncUploadRequest(BaseModel):
    """The Android app batches its whole pending queue into one call."""

    device_id: str
    submissions: list[SubmissionCreate]


class SyncUploadResultItem(BaseModel):
    client_submission_uuid: str
    accepted: bool
    server_submission_id: str | None = None
    error: str | None = None


class SyncUploadResponse(BaseModel):
    results: list[SyncUploadResultItem]


class SyncDownloadResponse(BaseModel):
    """Published survey definitions the device should have locally, for offline form-filling."""

    surveys: list[SurveyDetailOut]
    server_time: str
