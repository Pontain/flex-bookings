from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.api.deps import get_db
from app.models.user import User
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingRead
from app.services.booking_service import (
    create_booking,
    BookingConflictError,
    VenueNotFoundError,
)

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    dependencies=[Depends(get_current_user)]
)


from app.models.user import User

@router.post("/", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking_route(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        booking = create_booking(db, booking_data)
        return booking
    except VenueNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BookingConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/", response_model=list[BookingRead])
def get_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookings = db.execute(
        select(Booking).order_by(Booking.start_time)
    ).scalars().all()
    return bookings