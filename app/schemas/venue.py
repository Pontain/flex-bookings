from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class VenueCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    organization_id: int | None = None
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=10000)
    capacity: int | None = Field(default=None, ge=1, le=1000000)
    color: str = Field(default="#5f73ff", pattern=r"^#[0-9a-fA-F]{6}$")


class VenueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    description: str | None
    capacity: int | None
    is_active: bool
    created_at: datetime