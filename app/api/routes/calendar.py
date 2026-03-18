from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.booking import Booking

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events")
def get_calendar_events(
    start: datetime = Query(...),
    end: datetime = Query(...),
    venue_id: int | None = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Booking).filter(
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
        }
        for booking in bookings
    ]