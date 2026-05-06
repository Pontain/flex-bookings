from fastapi import APIRouter, HTTPException, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime
from sqlalchemy import or_

from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.core.templates import templates
from app.models.user import User
from app.models.venue import Venue
from app.models.booking import Booking

router = APIRouter()

def require_admin(current_user: User):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

@router.get("/venues", response_class=HTMLResponse)
def list_venues(
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
        "venues/list.html",
        {
            "request": request,
            "venues": venues,
            "current_user": current_user,
        },
    )


@router.get("/venues/new", response_class=HTMLResponse)
def create_venue_form(
    request: Request,
    current_user: User = Depends(get_current_user),
):
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
    color: str | None = Form("#3b82f6"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_data = {
        "name": name,
        "description": description or "",
        "capacity": capacity or "",
        "color": color or "#3b82f6"}

    if not name.strip():
        return templates.TemplateResponse(
            "venues/create.html",
            {
                "request": request,
                "error": "Namn krävs",
                "form_data": form_data,
                "current_user": current_user,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    venue = Venue(
        organization_id=current_user.organization_id,
        name=name.strip(),
        description=description or None,
        capacity=capacity,
        color=color or "#3b82f6",
    )

    db.add(venue)
    db.commit()

    return RedirectResponse(
        url="/venues",
        status_code=status.HTTP_303_SEE_OTHER,
    )

# =========================
# EDIT (GET)
# =========================
@router.get("/venues/{venue_id}/edit", response_class=HTMLResponse)
def edit_venue_form(
    venue_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    venue = db.scalar(
        select(Venue).where(
            Venue.id == venue_id,
            Venue.organization_id == current_user.organization_id,
        )
    )

    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lokalen hittades inte",
        )

    return templates.TemplateResponse(
        "venues/edit.html",
        {
            "request": request,
            "venue": venue,
            "current_user": current_user,
        },
    )


# =========================
# EDIT (POST)
# =========================
@router.post("/venues/{venue_id}/edit")
def edit_venue_submit(
    venue_id: int,
    request: Request,
    name: str = Form(...),
    description: str | None = Form(None),
    capacity: int | None = Form(None),
    color: str | None = Form("#3b82f6"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    venue = db.scalar(
        select(Venue).where(
            Venue.id == venue_id,
            Venue.organization_id == current_user.organization_id,
        )
    )

    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lokalen hittades inte",
        )

    if not name.strip():
        return templates.TemplateResponse(
            "venues/edit.html",
            {
                "request": request,
                "venue": venue,
                "error": "Namn krävs",
                "current_user": current_user,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    venue.name = name.strip()
    venue.description = description or None
    venue.capacity = capacity
    venue.color = color or "#3b82f6"

    db.commit()

    return RedirectResponse(
        url="/venues",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# =========================
# DELETE
# =========================
@router.post("/venues/{venue_id}/delete")
def delete_venue(
    venue_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    now = datetime.now()

    future_booking_count = (
        db.query(Booking)
        .filter(
            Booking.venue_id == venue.id,
            Booking.organization_id == current_user.organization_id,
            Booking.start_time >= now,
            or_(
                Booking.status.is_(None),
                Booking.status != "cancelled",
            ),
        )
        .count()
    )

    if future_booking_count > 0:
        venues = (
            db.query(Venue)
            .filter(Venue.organization_id == current_user.organization_id)
            .order_by(Venue.name)
            .all()
        )

        return templates.TemplateResponse(
            "venues/list.html",
            {
                "request": request,
                "venues": venues,
                "current_user": current_user,
                "error": f"Lokalen kan inte tas bort eftersom den har {future_booking_count} framtida bokning(ar).",
            },
            status_code=400,
        )

    db.delete(venue)
    db.commit()

    return RedirectResponse(url="/venues", status_code=303)