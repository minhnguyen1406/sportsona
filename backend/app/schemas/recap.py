"""Response schema for GET /api/v1/races/{race_id}/recap."""

from datetime import datetime

from pydantic import BaseModel


class RecapResponse(BaseModel):
    race_id: int
    content: str
    prompt_version: str
    model: str
    created_at: datetime
    cached: bool
