from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.core.templates import templates

router = APIRouter()


@router.get("/calendar/week", response_class=HTMLResponse)
def calendar_week_view(request: Request):
    return templates.TemplateResponse(
        "calendar/week.html",
        {"request": request}
    )