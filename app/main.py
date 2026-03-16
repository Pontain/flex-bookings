from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.ui.routes import router as ui_router
from app.api.routes import bookings, venues

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# UI
app.include_router(ui_router)

# API
app.include_router(bookings.router, prefix="/api/bookings")
app.include_router(venues.router, prefix="/api/venues")