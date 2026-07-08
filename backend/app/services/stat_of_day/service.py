"""Orchestrates stat-of-the-day: pick angle + SQL, execute, narrate, cache.

One row per UTC date. The first authed user to hit /today on a given day
pays the ~5-8s LLM round-trip; subsequent requests fetch the cached row.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.stat_of_day import StatOfDay
from app.services.sql_safety import (
    SqlSafetyError,
    execute_read_only,
    validate_select,
)
from app.services.stat_of_day.llm import narrate, pick_stat


# Caps tuned for a curated card. Anything bigger than this isn't a "stat" anymore.
_MAX_ROWS = 20
_QUERY_TIMEOUT_MS = 5_000


class StatOfDayFailure(Exception):
    """Picker SQL failed validation or the query errored."""


def get_or_generate(db: Session, today: date) -> StatOfDay:
    existing = db.query(StatOfDay).filter(StatOfDay.date == today).first()
    if existing is not None:
        return existing

    picker = pick_stat(today)

    try:
        sql = validate_select(picker.sql)
        columns, rows, _truncated, _db_latency_ms = execute_read_only(
            db, sql, max_rows=_MAX_ROWS, timeout_ms=_QUERY_TIMEOUT_MS
        )
    except SqlSafetyError as exc:
        raise StatOfDayFailure(
            f"Generated SQL failed: {exc}"
        ) from exc

    narrator = narrate(picker.question, columns, rows)

    stat = StatOfDay(
        date=today,
        question=picker.question,
        sql=sql,
        columns=columns,
        rows=rows,
        narration=narrator.narration,
        model=narrator.model,
    )
    db.add(stat)
    db.commit()
    db.refresh(stat)
    return stat
