from datetime import datetime, date, time

from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

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
from app.core.templates import templates

router = APIRouter()


@router.get("/bookings", response_class=HTMLResponse)
def list_bookings(
    request: Request,
    title: str | None = None,
    venue: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
def create_booking_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venues = db.scalars(
        select(Venue)
        .where(Venue.organization_id == current_user.organization_id)
        .order_by(Venue.name.asc())
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
    start_date: str = Form(...),
    end_date: str = Form(...),
    start_hour: str = Form(...),
    start_minute: str = Form(...),
    end_hour: str = Form(...),
    end_minute: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venues = db.scalars(
        select(Venue)
        .where(Venue.organization_id == current_user.organization_id)
        .order_by(Venue.name.asc())
    ).all()

    form_data = {
        "venue_id": venue_id,
        "title": title,
        "description": description or "",
        "contact_name": contact_name,
        "contact_email": contact_email,
        "contact_phone": contact_phone or "",
        "start_date": start_date,
        "end_date": end_date,
        "start_hour": start_hour,
        "start_minute": start_minute,
        "end_hour": end_hour,
        "end_minute": end_minute,
    }

    try:
        start_hour = start_hour.strip().zfill(2)
        start_minute = start_minute.strip().zfill(2)
        end_hour = end_hour.strip().zfill(2)
        end_minute = end_minute.strip().zfill(2)

        start_hour_int = int(start_hour)
        start_minute_int = int(start_minute)
        end_hour_int = int(end_hour)
        end_minute_int = int(end_minute)

        if not (0 <= start_hour_int <= 23):
            raise ValueError("Starttimmen måste vara mellan 00 och 23.")

        if not (0 <= start_minute_int <= 59):
            raise ValueError("Startminuten måste vara mellan 00 och 59.")

        if not (0 <= end_hour_int <= 23):
            raise ValueError("Sluttimmen måste vara mellan 00 och 23.")

        if not (0 <= end_minute_int <= 59):
            raise ValueError("Slutminuten måste vara mellan 00 och 59.")

        start_time = datetime.strptime(
            f"{start_date} {start_hour}:{start_minute}",
            "%Y-%m-%d %H:%M",
        )

        end_time = datetime.strptime(
            f"{end_date} {end_hour}:{end_minute}",
            "%Y-%m-%d %H:%M",
        )

        if end_time <= start_time:
            return templates.TemplateResponse(
                "bookings/create.html",
                {
                    "request": request,
                    "venues": venues,
                    "error": "Sluttiden måste vara senare än starttiden.",
                    "form_data": form_data,
                    "current_user": current_user,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        booking_data = BookingCreate(
            venue_id=venue_id,
            title=title,
            description=description or None,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone or None,
            start_time=start_time,
            end_time=end_time,
        )

        booking = create_booking(db, booking_data, current_user.organization_id)

    except ValueError as e:
        error_message = str(e) if str(e) else "Ogiltigt datum eller tid."
        return templates.TemplateResponse(
            "bookings/create.html",
            {
                "request": request,
                "venues": venues,
                "error": error_message,
                "form_data": form_data,
                "current_user": current_user,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except ValidationError as e:
        error_message = (
            e.errors()[0]["msg"] if e.errors() else "Ogiltiga formulärdata."
        )

        return templates.TemplateResponse(
            "bookings/create.html",
            {
                "request": request,
                "venues": venues,
                "error": error_message,
                "form_data": form_data,
                "current_user": current_user,
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
                "current_user": current_user,
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
                "current_user": current_user,
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
    current_user: User = Depends(get_current_user),
):
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.venue))
        .where(
            Booking.id == booking_id,
            Booking.organization_id == current_user.organization_id,
        )
    )

    if not booking:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "message": "Bokningen hittades inte.",
                "current_user": current_user,
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

@router.get("/bookings/{booking_id}/modal", response_class=HTMLResponse)
def booking_details_modal(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db.execute(
        select(Booking)
        .options(selectinload(Booking.venue))
        .where(Booking.id == booking_id)
        .where(Booking.organization_id == current_user.organization_id)
    ).scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Bokningen hittades inte")

    return templates.TemplateResponse(
        "bookings/_booking_modal_content.html",
        {
            "request": request,
            "booking": booking,
            "current_user": current_user,
        },
    )

@router.get("/bookings/{booking_id}/edit", response_class=HTMLResponse)
def edit_booking_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not booking:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "message": "Bokningen kunde inte hittas.",
            },
            status_code=404,
        )

    venues = (
        db.query(Venue)
        .filter(
            Venue.organization_id == current_user.organization_id,
            Venue.is_active == True,
        )
        .order_by(Venue.name)
        .all()
    )

    return templates.TemplateResponse(
        "bookings/edit.html",
        {
            "request": request,
            "booking": booking,
            "venues": venues,
            "current_user": current_user,
        },
    )


@router.post("/bookings/{booking_id}/edit")
def edit_booking(
    booking_id: int,
    title: str = Form(...),
    description: str = Form(""),
    venue_id: int = Form(...),
    contact_name: str = Form(""),
    contact_email: str = Form(""),
    contact_phone: str = Form(""),

    start_date: date = Form(...),
    start_hour: str = Form(...),
    start_minute: str = Form(...),
    end_date: date = Form(...),
    end_hour: str = Form(...),
    end_minute: str = Form(...),

    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Bokningen finns inte")

    venue = (
        db.query(Venue)
        .filter(
            Venue.id == venue_id,
            Venue.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not venue:
        raise HTTPException(status_code=404, detail="Lokalen finns inte")

    start_time = datetime.combine(
        start_date,
        time(int(start_hour), int(start_minute)),
    )

    end_time = datetime.combine(
        end_date,
        time(int(end_hour), int(end_minute)),
    )

    if end_time <= start_time:
        raise HTTPException(
            status_code=400,
            detail="Sluttiden måste vara efter starttiden",
        )

    conflict = (
        db.query(Booking)
        .filter(
            Booking.id != booking_id,
            Booking.venue_id == venue_id,
            Booking.organization_id == current_user.organization_id,
            Booking.status != "cancelled",
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )
        .first()
    )

    if conflict:
        raise HTTPException(
            status_code=400,
            detail="Det finns redan en bokning på vald tid",
        )

    booking.title = title
    booking.description = description
    booking.venue_id = venue_id
    booking.contact_name = contact_name
    booking.contact_email = contact_email
    booking.contact_phone = contact_phone
    booking.start_time = start_time
    booking.end_time = end_time

    db.commit()

    return RedirectResponse(
        url=f"/bookings/{booking.id}",
        status_code=303,
    )