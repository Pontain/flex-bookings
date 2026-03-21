from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import os
from fastapi.staticfiles import StaticFiles

from app.ui.routes import router as ui_router
from app.ui.routes import router as ui_router
from app.api.routes import bookings
from app.api.routes import venues as api_venues
from app.api.routes import calendar as api_calendar

from app.web.routes import calendar as web_calendar
from app.web.routes import dashboard as web_dashboard
from app.web.routes import auth
from app.web.routes import users
from app.web.routes import venues as web_venues

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "byt-den-har-i-env"),
    same_site="lax",
    https_only=False,  # sätt True i produktion med HTTPS
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# UI
app.include_router(ui_router)

# API
app.include_router(bookings.router, prefix="/api/bookings")
app.include_router(api_venues.router, prefix="/api/venues")
app.include_router(api_calendar.router)

app.include_router(web_calendar.router)
app.include_router(web_dashboard.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(web_venues.router)