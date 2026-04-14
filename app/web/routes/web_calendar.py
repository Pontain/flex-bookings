from datetime import date, datetime, timedelta
import calendar as py_calendar

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.core.templates import templates
from app.models.booking import Booking
from app.models.user import User

router = APIRouter(tags=["Web Calendar"])


@router.get("/calendar/week", response_class=HTMLResponse)
def calendar_week_view(request: Request):
    return templates.TemplateResponse(
        "calendar/week.html",
        {"request": request}
    )


@router.get("/calendar/month", response_class=HTMLResponse)
def calendar_month(
    request: Request,
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()

    current_year = year or today.year
    current_month = month or today.month

    # Första och sista dagen i vald månad
    month_start = date(current_year, current_month, 1)
    _, days_in_month = py_calendar.monthrange(current_year, current_month)
    month_end = date(current_year, current_month, days_in_month)

    # Kalendern ska börja på måndag och sluta på söndag
    grid_start = month_start - timedelta(days=month_start.weekday())
    grid_end = month_end + timedelta(days=(6 - month_end.weekday()))

    # Datetime-intervall för SQL-frågan
    grid_start_dt = datetime.combine(grid_start, datetime.min.time())
    grid_end_dt = datetime.combine(grid_end + timedelta(days=1), datetime.min.time())

    bookings = db.execute(
        select(Booking)
        .options(selectinload(Booking.venue))
        .where(Booking.organization_id == current_user.organization_id)
        .where(Booking.start_time < grid_end_dt)
        .where(Booking.end_time >= grid_start_dt)
        .order_by(Booking.start_time.asc())
    ).scalars().all()

    bookings_by_day: dict[date, list[Booking]] = {}

    for booking in bookings:
        booking_day = booking.start_time.date()
        bookings_by_day.setdefault(booking_day, []).append(booking)

    weeks = []
    current_day = grid_start

    while current_day <= grid_end:
        week = []

        for _ in range(7):
            week.append(
                {
                    "date": current_day,
                    "day_number": current_day.day,
                    "is_current_month": current_day.month == current_month,
                    "is_today": current_day == today,
                    "bookings": bookings_by_day.get(current_day, []),
                }
            )
            current_day += timedelta(days=1)

        weeks.append(week)

    prev_month_date = month_start - timedelta(days=1)
    next_month_date = month_end + timedelta(days=1)

    return templates.TemplateResponse(
        "calendar/month.html",
        {
            "request": request,
            "current_user": current_user,
            "weeks": weeks,
            "month": current_month,
            "year": current_year,
            "current_year": current_year,
            "current_month": current_month,
            "month_name": py_calendar.month_name[current_month],
            "prev_year": prev_month_date.year,
            "prev_month": prev_month_date.month,
            "next_year": next_month_date.year,
            "next_month": next_month_date.month,
            "today_year": today.year,
            "today_month": today.month,
        },
    )