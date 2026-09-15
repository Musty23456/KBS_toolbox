import json

from sqlalchemy.orm import Session

from app.models.sync import AuditLog


def log_action(db: Session, actor_id: str | None, action: str, entity_type: str, entity_id: str | None, **details):
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details) if details else None,
    )
    db.add(entry)
    db.commit()
