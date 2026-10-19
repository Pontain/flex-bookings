from app.core.time import local_now, LOCAL
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.booking import Booking
from app.models.venue import Venue
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.templates import templates

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = local_now()

    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = start_of_today + timedelta(days=1)

    weekday = start_of_today.weekday()  # måndag=0
    start_of_week = start_of_today - timedelta(days=weekday)
    end_of_week = start_of_week + timedelta(days=7)

    bookings_today = db.query(func.count(Booking.id)).filter(
        Booking.organization_id == current_user.organization_id,
        Booking.status != "cancelled",
        Booking.start_time >= start_of_today,
        Booking.start_time < end_of_today,
    ).scalar() or 0

    bookings_this_week = db.query(func.count(Booking.id)).filter(
        Booking.organization_id == current_user.organization_id,
        Booking.status != "cancelled",
        Booking.start_time >= start_of_week,
        Booking.start_time < end_of_week,
    ).scalar() or 0

    active_venues = db.query(func.count(Venue.id)).filter(
        Venue.organization_id == current_user.organization_id,
        Venue.is_active == True,
    ).scalar() or 0

    next_booking = db.query(Booking).filter(
        Booking.organization_id == current_user.organization_id,
        Booking.status != "cancelled",
        Booking.start_time >= now,
    ).order_by(Booking.start_time.asc()).first()

    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {
            "request": request,
            "bookings_today": bookings_today,
            "bookings_this_week": bookings_this_week,
            "active_venues": active_venues,
            "next_booking": next_booking,
            "week_start": start_of_week.strftime("%Y-%m-%d"),
            "week_end": end_of_week.strftime("%Y-%m-%d"),
            "current_user": current_user,
        }
    )