from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.device import Device
from app.models.user import RoleName, User
from app.schemas.device import DeviceHeartbeat, DeviceOut

router = APIRouter(prefix="/api/devices", tags=["devices"])

def _touch(db, current_user, payload):
    now = datetime.now(timezone.utc)
    d = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if not d:
        d = Device(device_id=payload.device_id, user_id=current_user.id)
        db.add(d)
    elif d.user_id != current_user.id and current_user.role == RoleName.ENUMERATOR:
        raise HTTPException(status_code=403, detail="Device belongs to another user")
    d.app_version = payload.app_version or d.app_version
    d.platform = payload.platform
    d.last_seen_at = now
    d.is_active = True
    db.commit(); db.refresh(d)
    return d

@router.post("/heartbeat", response_model=DeviceOut)
def heartbeat(payload: DeviceHeartbeat, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _touch(db, current_user, payload)

@router.get("", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db), current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR))):
    return db.query(Device).options(joinedload(Device.user)).order_by(Device.last_seen_at.desc().nullslast()).all()

@router.post("/{device_id}/request-sync", response_model=DeviceOut)
def request_sync(device_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR))):
    d = db.query(Device).filter(Device.device_id == device_id).first()
    if not d: raise HTTPException(status_code=404, detail="Device not found")
    d.sync_requested_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(d)
    return d

@router.post("/{device_id}/deactivate", response_model=DeviceOut)
def deactivate(device_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR))):
    d = db.query(Device).filter(Device.device_id == device_id).first()
    if not d: raise HTTPException(status_code=404, detail="Device not found")
    d.is_active = False
    db.commit(); db.refresh(d)
    return d


# ---------------------------------------------------------------------------
# Online enumerators (live presence) — additive; nothing above is changed.
# An enumerator is ONLINE if their app pinged us in the last 3 minutes,
# AWAY if in the last 30 minutes, otherwise OFFLINE.
# ---------------------------------------------------------------------------
ONLINE_WINDOW_SECONDS = 180
AWAY_WINDOW_SECONDS = 1800


def _aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@router.get("/online-enumerators")
def online_enumerators(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.ADMINISTRATOR, RoleName.SUPERVISOR)),
):
    now = datetime.now(timezone.utc)

    enumerators = (
        db.query(User)
        .filter(User.role == RoleName.ENUMERATOR, User.is_active == True)  # noqa: E712
        .all()
    )
    devices = (
        db.query(Device)
        .filter(Device.is_active == True)  # noqa: E712
        .all()
    )

    # Most recently seen device per user
    latest = {}
    for d in devices:
        seen = _aware(d.last_seen_at)
        current = latest.get(d.user_id)
        if current is None or (seen and (_aware(current.last_seen_at) is None or seen > _aware(current.last_seen_at))):
            latest[d.user_id] = d

    rows = []
    for u in enumerators:
        d = latest.get(u.id)
        seen = _aware(d.last_seen_at) if d else None
        seconds = int((now - seen).total_seconds()) if seen else None
        if seconds is None:
            state = "OFFLINE"
        elif seconds <= ONLINE_WINDOW_SECONDS:
            state = "ONLINE"
        elif seconds <= AWAY_WINDOW_SECONDS:
            state = "AWAY"
        else:
            state = "OFFLINE"
        rows.append({
            "user_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "device_id": d.device_id if d else None,
            "app_version": d.app_version if d else None,
            "last_seen_at": seen.isoformat() if seen else None,
            "last_sync_at": _aware(d.last_sync_at).isoformat() if d and d.last_sync_at else None,
            "last_sync_status": d.last_sync_status if d else None,
            "seconds_since_seen": seconds,
            "status": state,
        })

    order = {"ONLINE": 0, "AWAY": 1, "OFFLINE": 2}
    rows.sort(key=lambda r: (order[r["status"]], r["seconds_since_seen"] if r["seconds_since_seen"] is not None else 10**12))

    return {
        "server_time": now.isoformat(),
        "counts": {
            "online": sum(1 for r in rows if r["status"] == "ONLINE"),
            "away": sum(1 for r in rows if r["status"] == "AWAY"),
            "offline": sum(1 for r in rows if r["status"] == "OFFLINE"),
            "total": len(rows),
        },
        "enumerators": rows,
    }
