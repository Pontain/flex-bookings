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


def format_booking_time_for_day(booking: Booking, current_day: date) -> str:
    day_start = datetime.combine(
        current_day,
        datetime.min.time(),
        tzinfo=booking.start_time.tzinfo,
    )
    day_end = day_start + timedelta(days=1)

    starts_today = day_start <= booking.start_time < day_end
    ends_today = day_start < booking.end_time <= day_end

    start_text = booking.start_time.strftime("%H:%M")
    end_text = booking.end_time.strftime("%H:%M")

    if starts_today and ends_today:
        return f"{start_text} - {end_text}"

    if starts_today:
        return f"{start_text} - fortsätter"

    if ends_today:
        return f"fortsätter - {end_text}"

    return "fortsätter"


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

    month_start = date(current_year, current_month, 1)
    _, days_in_month = py_calendar.monthrange(current_year, current_month)
    month_end = date(current_year, current_month, days_in_month)

    grid_start = month_start - timedelta(days=month_start.weekday())
    grid_end = month_end + timedelta(days=(6 - month_end.weekday()))

    grid_start_dt = datetime.combine(grid_start, datetime.min.time())
    grid_end_dt = datetime.combine(grid_end + timedelta(days=1), datetime.min.time())

    bookings = db.execute(
        select(Booking)
        .options(selectinload(Booking.venue))
        .where(Booking.organization_id == current_user.organization_id)
        .where(Booking.start_time < grid_end_dt)
        .where(Booking.end_time > grid_start_dt)
        .order_by(Booking.start_time.asc())
    ).scalars().all()

    bookings_by_day: dict[date, list[dict]] = {}

    for booking in bookings:
        first_day = max(booking.start_time.date(), grid_start)
        last_day = min(booking.end_time.date(), grid_end)

        if booking.end_time.time() == datetime.min.time():
            last_day -= timedelta(days=1)

        current_booking_day = first_day

        while current_booking_day <= last_day:
            bookings_by_day.setdefault(current_booking_day, []).append(
                {
                    "booking": booking,
                    "time_label": format_booking_time_for_day(booking, current_booking_day),
                }
            )
            current_booking_day += timedelta(days=1)

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