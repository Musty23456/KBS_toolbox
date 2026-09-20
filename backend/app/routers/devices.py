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
