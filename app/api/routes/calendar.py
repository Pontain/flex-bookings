from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.booking import Booking
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.time import as_local

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events")
def get_calendar_events(
    start: datetime = Query(...),
    end: datetime = Query(...),
    venue_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try: start, end = as_local(start), as_local(end)
    except ValueError as exc: raise HTTPException(400, str(exc))
    if end <= start or (end - start).days > 93:
        raise HTTPException(400, "Välj ett intervall på högst 93 dagar.")
    query = db.query(Booking).filter(
        Booking.organization_id == current_user.organization_id,
        Booking.status != "cancelled",
        Booking.start_time < end,
        Booking.end_time > start
    )

    if venue_id is not None:
        query = query.filter(Booking.venue_id == venue_id)

    bookings = query.order_by(Booking.start_time).all()

    return [
        {
            "id": booking.id,
            "title": booking.title,
            "start": booking.start_time.isoformat(),
            "end": booking.end_time.isoformat(),
            "venue_id": booking.venue_id,
            "contact_name": booking.contact_name,
            "venue_color": booking.venue.color if booking.venue else "#5f73ff",
        }
        for booking in bookings
    ]