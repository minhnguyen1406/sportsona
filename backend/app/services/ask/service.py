"""Orchestrates the ask flow: generate SQL, validate, execute safely.

The LLM is treated as untrusted: every query passes a deny-list check and
runs inside a read-only transaction with a hard statement timeout. We
never let Claude *invent* a number — it only writes the query; the database
is the source of truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.ask_cache import AskCache
from app.services.ask.llm import AskClient, SqlGeneration, get_ask_client
from app.services.sql_safety import (
    SqlSafetyError,
    execute_read_only,
    validate_select,
)


QUERY_TIMEOUT_MS = 5_000
MAX_ROWS = 100

# Answers go stale when new race data syncs in, so cache entries expire by
# age rather than living forever.
CACHE_TTL = timedelta(hours=24)


def _normalize_question(q: str) -> str:
    """Collapse trivially-different phrasings onto one cache key."""
    q = q.strip().lower()
    q = re.sub(r"\s+", " ", q)
    return q.rstrip("?!. ")


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
    cached: bool = False


def _from_cache(db: Session, normalized: str) -> AskCache | None:
    entry = (
        db.query(AskCache)
        .filter(AskCache.question_normalized == normalized)
        .first()
    )
    if entry is None:
        return None
    if datetime.utcnow() - entry.created_at > CACHE_TTL:
        # Expired — delete so the fresh answer can take its slot.
        db.delete(entry)
        db.commit()
        return None
    return entry


def _store_cache(db: Session, normalized: str, result: AskResult) -> None:
    """Best-effort insert; a concurrent identical ask losing the unique race
    is fine — the answer already exists."""
    entry = AskCache(
        question_normalized=normalized,
        question=result.question,
        sql=result.sql,
        reasoning=result.reasoning,
        columns=result.columns,
        rows=result.rows,
        truncated=result.truncated,
        model=result.model,
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


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

    normalized = _normalize_question(question)

    hit = _from_cache(db, normalized)
    if hit is not None:
        hit.hit_count += 1
        db.commit()
        return AskResult(
            question=question.strip(),
            sql=hit.sql,
            reasoning=hit.reasoning,
            columns=list(hit.columns),
            rows=[list(r) for r in hit.rows],
            row_count=len(hit.rows),
            truncated=hit.truncated,
            model=hit.model,
            llm_latency_ms=0,
            db_latency_ms=0,
            cache_read_tokens=0,
            cached=True,
        )

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

    result = AskResult(
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
        cached=False,
    )
    _store_cache(db, normalized, result)
    return result
