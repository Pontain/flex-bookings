from fastapi import FastAPI
from app.api.routes.venues import router as venues_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.organizations import router as organizations_router

app = FastAPI(title="Flex Bookings")

app.include_router(venues_router, prefix="/venues", tags=["venues"])
app.include_router(bookings_router, prefix="/bookings", tags=["bookings"])
app.include_router(organizations_router, prefix="/organizations", tags=["organizations"])


@app.get("/")
def root():
    return {"message": "Flex Bookings API is running"}