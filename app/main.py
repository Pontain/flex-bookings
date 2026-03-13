from fastapi import FastAPI
from app.api.routes.venues import router as venues_router
from app.api.routes.bookings import router as bookings_router

app = FastAPI(title="Flex Bookings")

app.include_router(venues_router, prefix="/venues", tags=["venues"])
app.include_router(bookings_router, prefix="/bookings", tags=["bookings"])


@app.get("/")
def root():
    return {"message": "Flex Bookings API is running"}