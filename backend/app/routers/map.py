from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import get_current_user
from app.models.submission import Submission
from app.models.user import User
from app.schemas.location import SubmissionMapPoint

router = APIRouter(prefix="/api/map", tags=["map"])

@router.get("/submissions", response_model=list[SubmissionMapPoint])
def submission_points(
    survey_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Submission).options(joinedload(Submission.survey))
    if survey_id:
        q = q.filter(Submission.survey_id == survey_id)
    if status:
        q = q.filter(Submission.status == status)
    rows = q.filter(Submission.gps_latitude.is_not(None), Submission.gps_longitude.is_not(None)).order_by(Submission.created_at.desc()).all()
    return [SubmissionMapPoint(
        id=s.id, survey_id=s.survey_id, survey_title=s.survey.title if s.survey else "Unknown survey",
        submitted_by_id=s.submitted_by_id, latitude=s.gps_latitude, longitude=s.gps_longitude,
        collected_at=s.collected_at, status=s.status.value if hasattr(s.status, "value") else str(s.status)
    ) for s in rows]
