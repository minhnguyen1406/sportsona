"""Pydantic schemas for the /ask natural-language stats endpoint."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    question: str
    sql: str
    reasoning: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    model: str
    llm_latency_ms: int
    db_latency_ms: int
    cache_read_tokens: int
    cached: bool = False
    # Slug of the stored snapshot — the shareable /ask/a/{answer_id} link.
    answer_id: str | None = None


class AskAnswerResponse(BaseModel):
    """A stored answer snapshot, fetched by slug (public) or via history."""

    slug: str
    question: str
    sql: str
    reasoning: str
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool
    model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AskHistoryItem(BaseModel):
    """Compact history row — question + link, no payload."""

    slug: str
    question: str
    created_at: datetime

    model_config = {"from_attributes": True}
