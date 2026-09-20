from datetime import datetime
from pydantic import BaseModel, ConfigDict
class DeviceHeartbeat(BaseModel):
    device_id: str
    app_version: str | None = None
    platform: str = "ANDROID"
class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    device_id: str
    user_id: str
    app_version: str | None
    platform: str
    last_seen_at: datetime | None
    last_sync_at: datetime | None
    last_sync_status: str | None
    failed_sync_count: int
    sync_requested_at: datetime | None
    is_active: bool
    note: str | None
