"""Orchestrates the ask flow: generate SQL, validate, execute safely.

The LLM is treated as untrusted: every query passes a deny-list check and
runs inside a read-only transaction with a hard statement timeout. We
never let Claude *invent* a number — it only writes the query; the database
is the source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.services.ask.llm import AskClient, SqlGeneration, get_ask_client
from app.services.sql_safety import (
    SqlSafetyError,
    execute_read_only,
    validate_select,
)


QUERY_TIMEOUT_MS = 5_000
MAX_ROWS = 100


class AskFailure(Exception):
    """Raised when the LLM output fails validation or the query errors."""

    def __init__(self, message: str, *, sql: str | None = None):
        super().__init__(message)
        self.sql = sql


@dataclass
class AskResult:
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


def answer_question(
    db: Session,
    question: str,
    *,
    client: AskClient | None = None,
) -> AskResult:
    if not question or not question.strip():
        raise AskFailure("Question is empty.")
    if len(question) > 500:
        raise AskFailure("Question is too long (max 500 characters).")

    llm = client or get_ask_client()
    gen: SqlGeneration = llm.generate_sql(question.strip())

    try:
        sql = validate_select(gen.sql)
        columns, rows, truncated, db_latency_ms = execute_read_only(
            db, sql, max_rows=MAX_ROWS, timeout_ms=QUERY_TIMEOUT_MS
        )
    except SqlSafetyError as exc:
        # Preserve the AskFailure boundary so the router's 400 mapping
        # keeps working unchanged.
        raise AskFailure(str(exc), sql=exc.sql) from exc

    return AskResult(
        question=question.strip(),
        sql=sql,
        reasoning=gen.reasoning,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
        model=gen.model,
        llm_latency_ms=gen.latency_ms,
        db_latency_ms=db_latency_ms,
        cache_read_tokens=gen.cache_read_tokens,
    )
