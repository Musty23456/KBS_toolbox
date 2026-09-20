from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.media import MediaKind, SubmissionMedia
from app.models.submission import Submission, SubmissionAnswer
from app.models.user import RoleName, User
from app.services.audit import log_action

router = APIRouter(prefix="/api/media", tags=["media"])
settings = get_settings()

_ALLOWED = {
    "PHOTO": {"image/jpeg", "image/png", "image/webp"},
    "AUDIO": {"audio/mpeg", "audio/mp4", "audio/aac", "audio/x-m4a", "audio/wav", "audio/ogg"},
    "SIGNATURE": {"image/png", "image/jpeg"},
}
_MAX_BYTES = 25 * 1024 * 1024


def _safe_name(name: str) -> str:
    return Path(name or "upload.bin").name[:255]


@router.post("/upload")
async def upload_media(
    submission_id: str = Form(...),
    question_id: str = Form(...),
    kind: MediaKind = Form(...),
    group_instance_index: int | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.submitted_by_id != current_user.id and current_user.role not in (RoleName.ADMINISTRATOR, RoleName.SUPERVISOR):
        raise HTTPException(status_code=403, detail="Not authorized to upload media for this submission")
    if file.content_type not in _ALLOWED[kind.value]:
        raise HTTPException(status_code=415, detail=f"Unsupported {kind.value.lower()} content type")

    answer = db.query(SubmissionAnswer).filter(
        SubmissionAnswer.submission_id == submission_id,
        SubmissionAnswer.question_id == question_id,
        SubmissionAnswer.group_instance_index == group_instance_index,
    ).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Submission answer for media question not found")

    root = Path(settings.MEDIA_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    submission_dir = root / submission_id
    submission_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(_safe_name(file.filename)).suffix.lower()
    storage_name = f"{uuid4().hex}{suffix}"
    destination = submission_dir / storage_name

    size = 0
    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > _MAX_BYTES:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="Media file is too large (max 25 MB)")
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    storage_key = f"{submission_id}/{storage_name}"
    media = SubmissionMedia(
        submission_id=submission_id,
        question_id=question_id,
        group_instance_index=group_instance_index,
        kind=kind,
        original_filename=_safe_name(file.filename),
        storage_key=storage_key,
        content_type=file.content_type,
        size_bytes=size,
    )
    db.add(media)
    db.flush()
    answer.media_reference = f"/api/media/{media.id}"
    db.commit()
    log_action(db, current_user.id, "MEDIA_UPLOADED", "SubmissionMedia", media.id)
    return {"id": media.id, "url": f"/api/media/{media.id}", "kind": kind, "size_bytes": size}


@router.get("/{media_id}")
def get_media(media_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    media = db.query(SubmissionMedia).filter(SubmissionMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    submission = db.query(Submission).filter(Submission.id == media.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.submitted_by_id != current_user.id and current_user.role not in (RoleName.ADMINISTRATOR, RoleName.SUPERVISOR):
        raise HTTPException(status_code=403, detail="Not authorized to view this media")
    path = Path(settings.MEDIA_ROOT) / media.storage_key
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Media file is missing from storage")
    return FileResponse(path, media_type=media.content_type, filename=media.original_filename)
