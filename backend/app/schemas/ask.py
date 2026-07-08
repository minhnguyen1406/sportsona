"""Pydantic schemas for the /ask natural-language stats endpoint."""

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
