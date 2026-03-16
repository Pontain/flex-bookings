from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class BookingCreate(BaseModel):
    venue_id: int
    title: str
    description: str | None = None
    contact_name: str
    contact_email: EmailStr
    contact_phone: str | None = None
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def end_must_be_after_start(cls, end_time: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    venue_id: int
    title: str
    description: str | None
    contact_name: str
    contact_email: EmailStr
    contact_phone: str | None
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
    updated_at: datetime