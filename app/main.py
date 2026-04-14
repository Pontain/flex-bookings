from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import os
from fastapi.staticfiles import StaticFiles


print("Import Bookings")
from app.api.routes import bookings
print("Import Venues")
from app.api.routes import venues as api_venues
print("Import Calendar")
from app.api.routes import calendar as api_calendar

print("Import Web Calendar")
from app.web.routes import web_calendar as web_calendar
print("Import Web Dashboard")
from app.web.routes import dashboard as web_dashboard
print("Import Web Auth")
from app.web.routes import auth
print("Import Web Users")
from app.web.routes import users
print("Import Web Venues")
from app.web.routes import venues as web_venues
print("Import Web Bookings")
from app.web.routes import bookings as web_bookings

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "byt-den-har-i-env"),
    same_site="lax",
    https_only=False,  # sätt True i produktion med HTTPS
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


# API
app.include_router(bookings.router, prefix="/api/bookings")
app.include_router(api_venues.router, prefix="/api/venues")
app.include_router(api_calendar.router)

app.include_router(web_calendar.router)
app.include_router(web_dashboard.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(web_venues.router)
app.include_router(web_bookings.router)