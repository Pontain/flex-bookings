from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlsplit
from app.core.config import APP_DIR, BASE_URL, PRODUCTION, SECRET
from app.core.protection import ProtectionMiddleware
from app.api.routes import bookings, venues as api_venues, calendar as api_calendar
from app.web.routes import web_calendar, dashboard, auth, users, venues, bookings as web_bookings
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.core.database import engine
@asynccontextmanager
async def lifespan(app):
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version FROM modium_migrations WHERE version='20261018_security_v1'")).first()
        if not version: raise RuntimeError("Kör python -m scripts.migrate före uppstart.")
    yield
app = FastAPI(lifespan=lifespan)
app.add_middleware(ProtectionMiddleware)
app.add_middleware(SessionMiddleware, secret_key=SECRET, same_site="lax", https_only=PRODUCTION, max_age=28800)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[urlsplit(BASE_URL).hostname, "localhost", "127.0.0.1"] if not PRODUCTION else [urlsplit(BASE_URL).hostname])
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
app.include_router(bookings.router, prefix="/api/bookings")
app.include_router(api_venues.router, prefix="/api/venues")
app.include_router(api_calendar.router)
for router in (web_calendar.router, dashboard.router, auth.router, users.router, venues.router, web_bookings.router): app.include_router(router)
@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc):
    return JSONResponse({"detail":"Ändringen kunde inte sparas: uppgifterna krockar med befintliga data. Ladda om och försök igen."}, status_code=409)
@app.get("/health")
def health(): return {"status":"ok"}
