from datetime import datetime
from pydantic import BaseModel


class AvailabilitySlot(BaseModel):
    start: datetime
    end: datetime