from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.templates import templates
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.venue import Venue


router = APIRouter()

@router.get("/venues/{venue_id}/edit", response_class=HTMLResponse)
def edit_venue_form(
    venue_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venue = db.get(Venue, venue_id)

    if not venue:
        raise HTTPException(status_code=404, detail="Lokalen finns inte")

    if venue.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    return templates.TemplateResponse(
        "venues/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "venue": venue,
        }
    )


@router.post("/venues/{venue_id}/edit")
def edit_venue(
    venue_id: int,
    name: str = Form(...),
    description: str = Form(""),
    capacity: str = Form(""),
    is_active: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    venue = db.get(Venue, venue_id)

    if not venue:
        raise HTTPException(status_code=404, detail="Lokalen finns inte")

    if venue.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    venue.name = name
    venue.description = description if description.strip() else None
    venue.capacity = int(capacity) if capacity.strip() else None
    venue.is_active = True if is_active else False

    db.commit()

    return RedirectResponse(url="/venues", status_code=303)
