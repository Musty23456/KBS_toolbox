from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.question import Question
from app.models.survey import Survey, SurveyStatus, SurveyVersion
from app.models.sync import SyncMetadata, SyncStatus
from app.models.user import RoleName, User
from app.models.device import Device
from app.routers.submissions import _create_submission
from app.routers.surveys import _to_detail
from app.schemas.sync import SyncDownloadResponse, SyncUploadRequest, SyncUploadResponse, SyncUploadResultItem

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/upload", response_model=SyncUploadResponse)
def sync_upload(
    payload: SyncUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a batch of offline submissions and record device sync telemetry."""
    results: list[SyncUploadResultItem] = []
    for item in payload.submissions:
        try:
            submission = _create_submission(db, item, current_user)
            sync_meta = db.query(SyncMetadata).filter(SyncMetadata.submission_id == submission.id).first()
            if sync_meta:
                sync_meta.attempt_count += 1
                sync_meta.last_attempt_at = datetime.now(timezone.utc)
                sync_meta.status = SyncStatus.SUCCESS
                sync_meta.client_device_id = payload.device_id
            else:
                db.add(SyncMetadata(
                    submission_id=submission.id,
                    client_device_id=payload.device_id,
                    status=SyncStatus.SUCCESS,
                    attempt_count=1,
                    last_attempt_at=datetime.now(timezone.utc),
                ))
            db.commit()
            results.append(SyncUploadResultItem(client_submission_uuid=item.client_submission_uuid, accepted=True, server_submission_id=submission.id))
        except HTTPException as exc:
            db.rollback()
            results.append(SyncUploadResultItem(client_submission_uuid=item.client_submission_uuid, accepted=False, error=str(exc.detail)))
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            results.append(SyncUploadResultItem(client_submission_uuid=item.client_submission_uuid, accepted=False, error=f"Unexpected error: {exc}"))

    now = datetime.now(timezone.utc)
    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if not device:
        device = Device(device_id=payload.device_id, user_id=current_user.id)
        db.add(device)
    elif device.user_id != current_user.id and current_user.role == RoleName.ENUMERATOR:
        raise HTTPException(status_code=403, detail="Device belongs to another user")
    device.last_seen_at = now
    device.last_sync_at = now
    device.last_sync_status = "PARTIAL" if any(not r.accepted for r in results) else "SUCCESS"
    device.failed_sync_count += sum(1 for r in results if not r.accepted)
    db.commit()
    return SyncUploadResponse(results=results)


@router.get("/download", response_model=SyncDownloadResponse)
def sync_download(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns every currently PUBLISHED survey with its full current-version
    question/choice tree, so the Android app can cache complete form
    definitions locally and render + fill them with zero network calls.
    """
    surveys = (
        db.query(Survey)
        .options(joinedload(Survey.versions).joinedload(SurveyVersion.questions).joinedload(Question.choices))
        .filter(Survey.status == SurveyStatus.PUBLISHED)
        .all()
    )
    return SyncDownloadResponse(
        surveys=[_to_detail(s) for s in surveys],
        server_time=datetime.now(timezone.utc).isoformat(),
    )
