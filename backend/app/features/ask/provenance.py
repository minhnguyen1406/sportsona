"""Three-state provenance for an /ask answer, derived from its SQL.

Every /ask figure comes from a query we ran against the official record, so
provenance can be computed mechanically instead of asked of the LLM:

  confirmed   — a table in the official record the query read from
  derived     — the query aggregates (COUNT/SUM/AVG/…): the figure is computed
                by us from confirmed rows, not a number that exists in the record
  unavailable — the query is the schema-doc's "not in the database" fallback
                (a literal note), or it touches coverage we don't model

The result renders as the legend the brand guide calls for: teal / amber / sand.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from sqlalchemy.orm import Session


class ProvenanceItem(NamedTuple):
    state: str      # "confirmed" | "derived" | "unavailable"
    label: str      # human line
    source: str     # short tag on the right


_TABLE_LABELS: dict[str, tuple[str, str]] = {
    "race_results": ("Official race results", "FIA classification"),
    "qualifying_results": ("Official qualifying results", "FIA classification"),
    "driver_standings": ("Drivers' championship standings", "Official standings"),
    "constructor_standings": ("Constructors' championship standings", "Official standings"),
    "races": ("Race calendar", "Official schedule"),
    "drivers": ("Driver records", "Official entry lists"),
    "constructors": ("Team records", "Official entry lists"),
    "driver_entries": ("Season entry lists", "Official entry lists"),
    "circuits": ("Circuit records", "Official schedule"),
    "seasons": ("Season list", "Official schedule"),
}

_AGG_RE = re.compile(r"\b(COUNT|SUM|AVG|MIN|MAX|ROUND|PERCENTILE_CONT|STDDEV)\s*\(", re.I)
_TABLE_RE = re.compile(r"\bf1\.(\w+)")
_NOTE_RE = re.compile(r"SELECT\s+'[^']*'::text\s+AS\s+note", re.I)

# Things people ask about that the schema does not model at all.
_UNMODELLED = (
    ("sprint", "Sprint race results aren't in the database yet"),
    ("pit stop", "Pit-stop data isn't in the database"),
    ("pitstop", "Pit-stop data isn't in the database"),
    ("lap time", "Lap-by-lap timing isn't in the database"),
    ("fastest lap", "Fastest-lap data is partial in the record"),
    ("telemetry", "Telemetry isn't in the database"),
    ("weather", "Weather data isn't in the database"),
    ("tyre", "Tyre/strategy data isn't in the database"),
    ("tire", "Tyre/strategy data isn't in the database"),
)

_coverage_cache: dict[str, str] | None = None


def _coverage(db: Session) -> dict[str, str]:
    """Season span we actually hold per core table — cached per process."""
    global _coverage_cache
    if _coverage_cache is None:
        from sqlalchemy import text
        span = {}
        for table in ("race_results", "qualifying_results", "driver_standings"):
            row = db.execute(text(
                f"SELECT MIN(r.season), MAX(r.season) FROM f1.{table} t "
                + ("JOIN f1.races r ON r.id = t.race_id" if table != "driver_standings" else "JOIN f1.races r ON r.season = t.season")
            )).first()
            if row and row[0]:
                span[table] = f"{row[0]}–{row[1]}"
        _coverage_cache = span
    return _coverage_cache


def provenance_for(db: Session, sql: str, question: str) -> list[ProvenanceItem]:
    items: list[ProvenanceItem] = []

    # Schema-doc fallback: the LLM returned an explanatory note, not data.
    if _NOTE_RE.search(sql):
        return [ProvenanceItem("unavailable", "This isn't in the database yet", "Not available")]

    coverage = _coverage(db)
    seen: set[str] = set()
    for table in _TABLE_RE.findall(sql):
        if table in seen or table not in _TABLE_LABELS:
            continue
        seen.add(table)
        label, source = _TABLE_LABELS[table]
        span = coverage.get(table)
        items.append(ProvenanceItem("confirmed", f"{label}{f' · {span}' if span else ''}", source))

    if _AGG_RE.search(sql):
        items.append(ProvenanceItem("derived", "Totals and averages computed by us from the rows above", "Derived by us"))

    q = question.lower()
    for needle, msg in _UNMODELLED:
        if needle in q:
            items.append(ProvenanceItem("unavailable", msg, "Not available"))
            break

    return items
