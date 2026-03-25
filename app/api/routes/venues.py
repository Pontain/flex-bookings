from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.venue import Venue
from app.models.user import User
from app.core.dependencies import get_current_user
from app.schemas.venue import VenueCreate, VenueRead
from app.services.availability_service import get_available_slots
from app.schemas.availability import AvailabilitySlot

router = APIRouter()

def require_admin(current_user: User):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")


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
        color=venue_data.color or "#5f73ff"
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

@router.get("/{venue_id}/availability", response_model=list[AvailabilitySlot])
def venue_availability(
    venue_id: int,
    date: date,
    db: Session = Depends(get_db)
):
    return get_available_slots(db, venue_id, date)

@router.get("/venues/{venue_id}/edit", response_class=HTMLResponse)
def edit_venue_form(
    venue_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    venue = db.get(Venue, venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Lokalen hittades inte")

    return templates.TemplateResponse(
        "venues/edit.html",
        {
            "request": request,
            "venue": venue,
            "current_user": current_user,
        }
    )


@router.post("/venues/{venue_id}/edit")
def edit_venue(
    venue_id: int,
    name: str = Form(...),
    description: str = Form(""),
    capacity: int = Form(...),
    color: str = Form("#5f73ff"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    venue = db.get(Venue, venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Lokalen hittades inte")

    venue.name = name
    venue.description = description if description else None
    venue.capacity = capacity
    venue.color = color

    db.commit()

    return RedirectResponse(url="/venues", status_code=303)