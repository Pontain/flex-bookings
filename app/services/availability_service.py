from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking


def get_available_slots(db: Session, venue_id: int, day: date):
    start_of_day = datetime.combine(day, time.min, tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)

    bookings = db.execute(
        select(Booking)
        .where(
            Booking.venue_id == venue_id,
            Booking.status != "cancelled",
            Booking.start_time < end_of_day,
            Booking.end_time > start_of_day,
        )
        .order_by(Booking.start_time)
    ).scalars().all()

    slots = []
    current = start_of_day

    for booking in bookings:
        if booking.start_time > current:
            slots.append({
                "start": current,
                "end": booking.start_time,
            })

        current = max(current, booking.end_time)

    if current < end_of_day:
        slots.append({
            "start": current,
            "end": end_of_day,
        })

    return slots