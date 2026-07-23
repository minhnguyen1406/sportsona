"""Shared SQL safety helpers used by /ask and /stat-of-the-day.

Treats every LLM-emitted SQL string as untrusted:
  - validate it as a single SELECT/WITH with no DDL/DML keywords
  - run inside a read-only transaction with a hard statement timeout
  - coerce result values to JSON-safe Python types
"""

from __future__ import annotations

import re
import time
from datetime import date, datetime, time as dtime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


# Tokens that have no business in a read-only stats query. We match on
# whole words so legitimate identifiers like "creation_date" aren't
# flagged. The transaction is also opened READ ONLY as belt-and-braces.
_FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "grant", "revoke", "comment", "vacuum", "analyze", "reindex", "copy",
    "merge", "call", "do", "execute", "lock", "set", "reset", "savepoint",
    "rollback", "commit", "begin", "start",
)
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(_FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE
)


class SqlSafetyError(Exception):
    """Base class for SQL safety / execution failures."""

    def __init__(self, message: str, *, sql: str | None = None):
        super().__init__(message)
        self.sql = sql


class SqlValidationError(SqlSafetyError):
    """The LLM-emitted SQL failed the safety check."""


class SqlExecutionError(SqlSafetyError):
    """The query errored at the database."""


def validate_select(sql: str) -> str:
    """Reject anything other than a single SELECT/WITH statement."""
    if not sql:
        raise SqlValidationError("LLM returned an empty SQL string.", sql=sql)

    cleaned = sql.strip().rstrip(";").strip()
    if ";" in cleaned:
        raise SqlValidationError("Multiple SQL statements are not allowed.", sql=sql)

    head = cleaned.lstrip("(").lstrip().split(None, 1)[0].lower()
    if head not in ("select", "with"):
        raise SqlValidationError(
            f"Only SELECT/WITH queries are allowed (got {head!r}).", sql=sql
        )

    match = _FORBIDDEN_RE.search(cleaned)
    if match:
        raise SqlValidationError(
            f"Query contains a forbidden keyword: {match.group(0)!r}.", sql=sql
        )

    return cleaned


def jsonable_value(value: Any) -> Any:
    """Coerce Postgres row values to JSON-safe Python types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, dtime)):
        return value.isoformat()
    return str(value)


def execute_read_only(
    db: Session,
    sql: str,
    *,
    max_rows: int = 100,
    timeout_ms: int = 5_000,
) -> tuple[list[str], list[list[Any]], bool, int]:
    """Execute SQL in a rolled-back read-only transaction with a hard timeout.

    Returns (columns, rows, truncated, db_latency_ms). Fetches `max_rows + 1`
    so we can flag truncation without scanning the rest of the result set.
    """
    start = time.perf_counter()
    try:
        db.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
        db.execute(text("SET TRANSACTION READ ONLY"))
        result = db.execute(text(sql))
        columns = list(result.keys())
        fetched = result.fetchmany(max_rows + 1)
    except SQLAlchemyError as exc:
        raise SqlExecutionError(
            f"Database error: {exc.orig if hasattr(exc, 'orig') else exc}",
            sql=sql,
        )
    finally:
        db.rollback()

    truncated = len(fetched) > max_rows
    rows = [[jsonable_value(v) for v in row] for row in fetched[:max_rows]]
    db_latency_ms = int((time.perf_counter() - start) * 1000)
    return columns, rows, truncated, db_latency_ms
