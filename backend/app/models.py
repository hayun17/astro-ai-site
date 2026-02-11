from __future__ import annotations

from pydantic import BaseModel


class BirthData(BaseModel):
    name: str = ""
    year: int
    month: int
    day: int
    hour: int
    minute: int
    latitude: float
    longitude: float
    tz_offset_hours: float = 3.0
