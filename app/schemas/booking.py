from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, Field


from app.core.time import as_local

class BookingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_time(cls, value): return as_local(value)

    venue_id: int
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=10000)
    contact_name: str = Field(min_length=1, max_length=120)
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=50)
    start_time: datetime
    end_time: datetime

    @field_validator("end_time")
    @classmethod
    def end_must_be_after_start(cls, end_time: datetime, info):
        start_time = info.data.get("start_time")
        if start_time and end_time.timestamp() <= start_time.timestamp():
            raise ValueError("end_time must be after start_time")
        return end_time


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    venue_id: int
    title: str = Field(min_length=1, max_length=120)
    description: str | None
    contact_name: str = Field(min_length=1, max_length=120)
    contact_email: EmailStr
    contact_phone: str | None
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
    updated_at: datetime