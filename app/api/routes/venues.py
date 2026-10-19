from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.venue import Venue
from app.schemas.venue import VenueCreate, VenueRead
from app.services.availability_service import get_available_slots
from app.schemas.availability import AvailabilitySlot
router = APIRouter()
@router.get("/", response_model=list[VenueRead])
def get_venues(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Venue).filter(Venue.organization_id == current_user.organization_id).order_by(Venue.id).all()
@router.post("/", response_model=VenueRead, status_code=201)
def create_venue(data: VenueCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser: raise HTTPException(403, "Behörighet saknas")
    if data.organization_id is not None and data.organization_id != current_user.organization_id: raise HTTPException(403, "Behörighet saknas")
    if db.query(Venue).filter(Venue.organization_id == current_user.organization_id, Venue.name == data.name).first(): raise HTTPException(409, "Lokalen finns redan")
    venue = Venue(**data.model_dump(exclude={"organization_id"}), organization_id=current_user.organization_id)
    db.add(venue); db.commit(); db.refresh(venue)
    return venue
@router.get("/{venue_id}/availability", response_model=list[AvailabilitySlot])
def availability(venue_id: int, date: date, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    venue = db.query(Venue).filter(Venue.id == venue_id, Venue.organization_id == current_user.organization_id).first()
    if not venue: raise HTTPException(404, "Lokalen hittades inte")
    return get_available_slots(db, venue_id, date)
