from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.review import ReviewStatus, SubmissionReview
from app.models.submission import Submission
from app.models.user import RoleName, User
from app.schemas.review import ReviewCreate, ReviewOut
from app.services.audit import log_action

router = APIRouter(prefix="/api/submissions", tags=["submission-reviews"])


@router.get("/{submission_id}/reviews", response_model=list[ReviewOut])
def list_reviews(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if current_user.role == RoleName.ENUMERATOR and submission.submitted_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(SubmissionReview).filter(SubmissionReview.submission_id == submission_id).order_by(SubmissionReview.created_at.desc()).all()


@router.post("/{submission_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def review_submission(
    submission_id: str,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if payload.status == ReviewStatus.RESUBMIT and not payload.comment:
        raise HTTPException(status_code=422, detail="A comment is required when requesting resubmission")

    review = SubmissionReview(
        submission_id=submission.id,
        reviewer_id=current_user.id,
        status=payload.status,
        comment=payload.comment,
    )
    submission.review_status = payload.status
    db.add(review)
    db.commit()
    db.refresh(review)
    log_action(db, current_user.id, f"SUBMISSION_{payload.status.value}", "Submission", submission.id, comment=payload.comment)
    return review
