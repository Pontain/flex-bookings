from fastapi import FastAPI

app = FastAPI(title="Flex Bookings")

@app.get("/")
def root():
    return {"message": "Flex Bookings API running"}