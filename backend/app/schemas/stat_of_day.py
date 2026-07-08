"""Response schema for GET /api/v1/stat-of-the-day."""

from datetime import date as date_t, datetime
from typing import Any

from pydantic import BaseModel


class StatOfDayResponse(BaseModel):
    date: date_t
    question: str
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    narration: str
    model: str
    created_at: datetime

    model_config = {"from_attributes": True}
