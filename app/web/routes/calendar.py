from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/calendar/week", response_class=HTMLResponse)
def calendar_week_view(request: Request):
    return templates.TemplateResponse(
        "calendar/week.html",
        {"request": request}
    )