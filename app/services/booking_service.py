from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.venue import Venue
from app.schemas.booking import BookingCreate


class BookingConflictError(Exception):
    pass


class VenueNotFoundError(Exception):
    pass


class InvalidBookingTimeError(Exception):
    pass


def create_booking(db: Session, booking_data: BookingCreate, organization_id: int) -> Booking:
    if booking_data.end_time <= booking_data.start_time:
        raise InvalidBookingTimeError(
            "Sluttiden måste vara senare än starttiden."
        )

    venue = db.scalar(
    select(Venue).where(
        Venue.id == booking_data.venue_id,
        Venue.organization_id == booking_data.organization_id
    )
)
    if not venue:
        raise VenueNotFoundError("Venue not found.")

    overlapping_booking = db.execute(
        select(Booking).where(
            Booking.venue_id == booking_data.venue_id,
            Booking.status != "cancelled",
            booking_data.start_time < Booking.end_time,
            booking_data.end_time > Booking.start_time,
        )
    ).scalar_one_or_none()

    if overlapping_booking:
        raise BookingConflictError(
            "This venue is already booked during the requested time."
        )

    booking = Booking(
        organization_id=organization_id,
        venue_id=booking_data.venue_id,
        title=booking_data.title,
        description=booking_data.description,
        contact_name=booking_data.contact_name,
        contact_email=booking_data.contact_email,
        contact_phone=booking_data.contact_phone,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        status="confirmed",
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking