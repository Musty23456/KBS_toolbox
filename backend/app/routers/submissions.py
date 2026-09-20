from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.question import Question
from app.models.submission import Submission, SubmissionAnswer, SubmissionStatus
from app.models.survey import SurveyVersion
from app.models.user import RoleName, User
from app.schemas.submission import SubmissionCreate, SubmissionOut
from app.services.audit import log_action
from app.services.validation import validate_submission_answers

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


def _create_submission(db: Session, payload: SubmissionCreate, user: User) -> Submission:
    existing = db.query(Submission).filter(Submission.client_submission_uuid == payload.client_submission_uuid).first()
    if existing:
        # Idempotent: retried uploads of the same client UUID return the
        # existing record instead of creating a duplicate.
        return existing

    version = db.query(SurveyVersion).options(joinedload(SurveyVersion.questions)).filter(
        SurveyVersion.id == payload.survey_version_id
    ).first()
    if not version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown survey_version_id")

    answers_by_question_id = {a.question_id: a.value_text for a in payload.answers}
    issues = validate_submission_answers(version.questions, answers_by_question_id)
    if issues:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"question": i.question_code, "message": i.message} for i in issues],
        )

    submission = Submission(
        survey_id=payload.survey_id,
        survey_version_id=payload.survey_version_id,
        submitted_by_id=user.id,
        client_submission_uuid=payload.client_submission_uuid,
        status=SubmissionStatus.SYNCED,
        gps_latitude=payload.gps_latitude,
        gps_longitude=payload.gps_longitude,
        collected_at=payload.collected_at,
        synced_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(submission)
    db.flush()

    for answer in payload.answers:
        db.add(
            SubmissionAnswer(
                submission_id=submission.id,
                question_id=answer.question_id,
                value_text=answer.value_text,
                media_reference=answer.media_reference,
                group_instance_index=answer.group_instance_index,
            )
        )

    db.commit()
    db.refresh(submission)
    log_action(db, user.id, "SUBMISSION_CREATED", "Submission", submission.id)
    return submission


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _create_submission(db, payload, current_user)


@router.get("", response_model=list[SubmissionOut])
def list_submissions(
    survey_id: str | None = None,
    status_filter: SubmissionStatus | None = Query(default=None, alias="status"),
    submitted_by_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    query = db.query(Submission).options(joinedload(Submission.answers), joinedload(Submission.reviews))
    if survey_id:
        query = query.filter(Submission.survey_id == survey_id)
    if status_filter:
        query = query.filter(Submission.status == status_filter)
    if submitted_by_id:
        query = query.filter(Submission.submitted_by_id == submitted_by_id)
    return query.order_by(Submission.created_at.desc()).all()


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = (
        db.query(Submission)
        .options(joinedload(Submission.answers), joinedload(Submission.reviews))
        .filter(Submission.id == submission_id)
        .first()
    )
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    is_owner = submission.submitted_by_id == current_user.id
    is_privileged = current_user.role in (RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)
    if not (is_owner or is_privileged):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this submission")

    return submission
