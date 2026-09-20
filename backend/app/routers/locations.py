from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.location import Location
from app.models.user import User
from app.schemas.location import LocationOut

router = APIRouter(prefix="/api/locations", tags=["locations"])

@router.get("", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Location).order_by(Location.level.asc(), Location.name.asc()).all()
