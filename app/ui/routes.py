from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from pydantic import ValidationError

from app.api.deps import get_db
from app.models.booking import Booking
from app.models.venue import Venue
from app.schemas.booking import BookingCreate
from app.services.booking_service import (
    create_booking,
    BookingConflictError,
    VenueNotFoundError,
)

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    now = datetime.now()

    venue_count = db.scalar(select(func.count()).select_from(Venue)) or 0

    today_booking_count = db.scalar(
        select(func.count()).select_from(Booking).where(
            Booking.start_time >= datetime.combine(today, datetime.min.time()),
            Booking.start_time < datetime.combine(tomorrow, datetime.min.time()),
        )
    ) or 0

    upcoming_booking_count = db.scalar(
        select(func.count()).select_from(Booking).where(
            Booking.start_time >= now
        )
    ) or 0

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "venue_count": venue_count,
            "today_booking_count": today_booking_count,
            "upcoming_booking_count": upcoming_booking_count,
        },
    )


@router.get("/venues", response_class=HTMLResponse)
def list_venues(request: Request, db: Session = Depends(get_db)):
    venues = db.scalars(
        select(Venue).order_by(Venue.name.asc())
    ).all()

    return templates.TemplateResponse(
        "venues/list.html",
        {
            "request": request,
            "venues": venues,
        },
    )


@router.get("/bookings", response_class=HTMLResponse)
def list_bookings(
    request: Request,
    title: str | None = None,
    venue: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(Booking)
        .options(selectinload(Booking.venue))
        .order_by(Booking.start_time.asc())
    )

    if title:
        stmt = stmt.where(Booking.title.ilike(f"%{title}%"))

    if venue:
        stmt = stmt.join(Booking.venue).where(Venue.name.ilike(f"%{venue}%"))

    bookings = db.scalars(stmt).all()

    return templates.TemplateResponse(
        "bookings/list.html",
        {
            "request": request,
            "bookings": bookings,
        },
    )


@router.get("/bookings/new", response_class=HTMLResponse)
def create_booking_form(request: Request, db: Session = Depends(get_db)):
    venues = db.scalars(
        select(Venue).order_by(Venue.name.asc())
    ).all()

    return templates.TemplateResponse(
        "bookings/create.html",
        {
            "request": request,
            "venues": venues,
            "error": None,
            "form_data": {},
        },
    )


@router.post("/bookings/new", response_class=HTMLResponse)
def create_booking_submit(
    request: Request,
    venue_id: int = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    contact_name: str = Form(...),
    contact_email: str = Form(...),
    contact_phone: str | None = Form(None),
    start_time: str = Form(...),
    end_time: str = Form(...),
    db: Session = Depends(get_db),
):
    venues = db.scalars(select(Venue).order_by(Venue.name.asc())).all()

    form_data = {
        "venue_id": venue_id,
        "title": title,
        "description": description or "",
        "contact_name": contact_name,
        "contact_email": contact_email,
        "contact_phone": contact_phone or "",
        "start_time": start_time,
        "end_time": end_time,
    }

    try:
        booking_data = BookingCreate(
            venue_id=venue_id,
            title=title,
            description=description or None,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone or None,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
        )

        booking = create_booking(db, booking_data)

    except ValueError:
        return templates.TemplateResponse(
            "bookings/create.html",
            {
                "request": request,
                "venues": venues,
                "error": "Ogiltigt datumformat.",
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except ValidationError as e:
        error_message = e.errors()[0]["msg"] if e.errors() else "Ogiltiga formulärdata."

        return templates.TemplateResponse(
            "bookings/create.html",
            {
                "request": request,
                "venues": venues,
                "error": error_message,
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except VenueNotFoundError as e:
        return templates.TemplateResponse(
            "bookings/create.html",
            {
                "request": request,
                "venues": venues,
                "error": str(e),
                "form_data": form_data,
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    except BookingConflictError as e:
        return templates.TemplateResponse(
            "bookings/create.html",
            {
                "request": request,
                "venues": venues,
                "error": str(e),
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url=f"/bookings/{booking.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/bookings/{booking_id}", response_class=HTMLResponse)
def booking_detail(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.venue))
        .where(Booking.id == booking_id)
    )

    if not booking:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "message": "Bokningen hittades inte.",
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return templates.TemplateResponse(
        "bookings/detail.html",
        {
            "request": request,
            "booking": booking,
        },
    )

@router.get("/ping")
def ping():
    return {"status": "ok"}