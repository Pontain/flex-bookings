from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from pydantic import ValidationError

from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.models.booking import Booking
from app.models.user import User
from app.models.venue import Venue
from app.schemas.booking import BookingCreate
from app.services.booking_service import (
    create_booking,
    BookingConflictError,
    VenueNotFoundError,
)

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")

def format_datetime(value):
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")

templates.env.filters["datetime"] = format_datetime


@router.get("/")
def root_redirect_login():
    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/venues", response_class=HTMLResponse)
def list_venues(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    venues = db.scalars(
    select(Venue)
    .where(Venue.organization_id == current_user.organization_id)
    .order_by(Venue.name.asc())
).all()

    return templates.TemplateResponse(
        "venues/list.html",
        {
            "request": request,
            "venues": venues,
            "current_user": current_user,
        },
    )


@router.get("/venues/new", response_class=HTMLResponse)
def create_venue_form(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "venues/create.html",
        {
            "request": request,
            "error": None,
            "form_data": {},
            "current_user": current_user,
        },
    )


@router.post("/venues/new", response_class=HTMLResponse)
def create_venue_submit(
    request: Request,
    name: str = Form(...),
    description: str | None = Form(None),
    capacity: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_data = {
        "name": name,
        "description": description or "",
        "capacity": capacity or "",
    }

    if not name:
        return templates.TemplateResponse(
            "venues/create.html",
            {
                "request": request,
                "error": "Namn krävs",
                "form_data": form_data,
                "current_user": current_user,
            },
        )

    venue = Venue(
        organization_id=current_user.organization_id,
        name=name,
        description=description or None,
        capacity=capacity,
    )

    db.add(venue)
    db.commit()

    return RedirectResponse(
        url="/venues",
        status_code=303,
    )


@router.post("/venues/{venue_id}/delete")
def delete_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.get(Venue, venue_id)

    if venue:
        db.delete(venue)
        db.commit()

    return RedirectResponse(
        url="/venues",
        status_code=303,
    )


@router.get("/bookings", response_class=HTMLResponse)
def list_bookings(
    request: Request,
    title: str | None = None,
    venue: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(Booking)
        .where(Booking.organization_id == current_user.organization_id)
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
            "current_user": current_user,
        },
    )


@router.get("/bookings/new", response_class=HTMLResponse)
def create_booking_form(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
            "current_user": current_user,
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
    current_user: User = Depends(get_current_user)
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
            "current_user": current_user,
        },
    )

@router.get("/ping")
def ping():
    return {"status": "ok"}