import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_roles
from app.models.sync import AuditLog
from app.models.user import RoleName, User

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _parse_details(raw: str | None):
    if not raw:
        return {}
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"value": value}
    except (TypeError, ValueError):
        return {"raw": raw}


@router.get("/summary")
def audit_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    q = db.query(AuditLog)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)

    total = q.count()
    actions = (
        q.with_entities(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(12)
        .all()
    )
    entities = (
        q.with_entities(AuditLog.entity_type, func.count(AuditLog.id))
        .group_by(AuditLog.entity_type)
        .order_by(func.count(AuditLog.id).desc())
        .all()
    )
    actors = (
        q.join(User, User.id == AuditLog.actor_id, isouter=True)
        .with_entities(User.id, User.full_name, func.count(AuditLog.id))
        .group_by(User.id, User.full_name)
        .order_by(func.count(AuditLog.id).desc())
        .limit(10)
        .all()
    )
    daily = (
        q.with_entities(func.date(AuditLog.created_at), func.count(AuditLog.id))
        .group_by(func.date(AuditLog.created_at))
        .order_by(func.date(AuditLog.created_at))
        .all()
    )
    return {
        "total_events": total,
        "actions": [{"name": name, "value": count} for name, count in actions],
        "entities": [{"name": name, "value": count} for name, count in entities],
        "actors": [{"user_id": uid, "name": name or "System", "events": count} for uid, name, count in actors],
        "daily": [{"date": str(day), "count": count} for day, count in daily],
    }


@router.get("/logs")
def audit_logs(
    action: str | None = None,
    entity_type: str | None = None,
    actor_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    q = db.query(AuditLog, User).join(User, User.id == AuditLog.actor_id, isouter=True)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if actor_id:
        q = q.filter(AuditLog.actor_id == actor_id)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)
    if search:
        needle = f"%{search}%"
        q = q.filter(
            AuditLog.action.ilike(needle)
            | AuditLog.entity_type.ilike(needle)
            | AuditLog.entity_id.ilike(needle)
            | User.full_name.ilike(needle)
            | User.email.ilike(needle)
        )

    total = q.count()
    rows = (
        q.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [
            {
                "id": log.id,
                "created_at": log.created_at.isoformat() if isinstance(log.created_at, datetime) else str(log.created_at),
                "actor_id": log.actor_id,
                "actor_name": user.full_name if user else "System",
                "actor_email": user.email if user else None,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": _parse_details(log.details),
            }
            for log, user in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/filters")
def audit_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    actions = [row[0] for row in db.query(AuditLog.action).distinct().order_by(AuditLog.action).all()]
    entities = [row[0] for row in db.query(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type).all()]
    users = (
        db.query(User.id, User.full_name, User.email)
        .join(AuditLog, AuditLog.actor_id == User.id)
        .distinct()
        .order_by(User.full_name)
        .all()
    )
    return {
        "actions": actions,
        "entities": entities,
        "users": [{"id": uid, "name": name, "email": email} for uid, name, email in users],
    }
