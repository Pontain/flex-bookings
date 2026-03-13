from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VenueCreate(BaseModel):
    organization_id: int
    name: str
    description: str | None = None
    capacity: int | None = None


class VenueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    description: str | None
    capacity: int | None
    is_active: bool
    created_at: datetime