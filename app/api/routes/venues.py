from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.venue import Venue
from app.schemas.venue import VenueCreate, VenueRead

router = APIRouter()


@router.post("/", response_model=VenueRead, status_code=status.HTTP_201_CREATED)
def create_venue(venue_data: VenueCreate, db: Session = Depends(get_db)):
    existing_venue = db.execute(
        select(Venue).where(
            Venue.organization_id == venue_data.organization_id,
            Venue.name == venue_data.name
        )
    ).scalar_one_or_none()

    if existing_venue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A venue with that name already exists in this organization."
        )

    venue = Venue(
        organization_id=venue_data.organization_id,
        name=venue_data.name,
        description=venue_data.description,
        capacity=venue_data.capacity,
    )

    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


@router.get("/", response_model=list[VenueRead])
def get_venues(db: Session = Depends(get_db)):
    venues = db.execute(
        select(Venue).order_by(Venue.id)
    ).scalars().all()
    return venues