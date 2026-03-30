from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.core.templates import templates
from app.models.user import User
from app.models.venue import Venue

router = APIRouter()


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    form_data = {
        "name": name,
        "description": description or "",
        "capacity": capacity or "",
    }

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
    )

    db.add(venue)
    db.commit()

    return RedirectResponse(
        url="/venues",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/venues/{venue_id}/delete")
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venue = db.scalar(
        select(Venue).where(
            Venue.id == venue_id,
            Venue.organization_id == current_user.organization_id,
        )
    )

    if not venue:
        return RedirectResponse(
            url="/venues",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    db.delete(venue)
    db.commit()

    return RedirectResponse(
        url="/venues",
        status_code=status.HTTP_303_SEE_OTHER,
    )