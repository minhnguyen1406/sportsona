"""Anthropic clients for the picker (question + SQL) and narrator (caption).

Two LLM calls per day, both with prompt caching. After the first call each
day, the system prompts are read at ~0.1× input cost.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date
from typing import Any

import anthropic

from app.core.config import settings
from app.services.stat_of_day.prompts import NARRATOR_PROMPT, PICKER_PROMPT


@dataclass
class PickerResult:
    question: str
    sql: str
    reasoning: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    latency_ms: int


@dataclass
class NarratorResult:
    narration: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    latency_ms: int


def _client() -> anthropic.Anthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY is not configured. Set it in .env to enable stat-of-the-day."
        )
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _extract_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


def pick_stat(today: date, *, client: anthropic.Anthropic | None = None) -> PickerResult:
    cli = client or _client()
    start = time.perf_counter()
    response = cli.messages.create(
        model=settings.RECAP_MODEL,
        max_tokens=800,
        system=[
            {
                "type": "text",
                "text": PICKER_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Today's date: {today.isoformat()}. Pick a stat for today.",
            }
        ],
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    raw = "\n".join(b.text for b in response.content if b.type == "text")
    try:
        parsed = _extract_json(raw)
        sql = parsed["sql"]
        question = parsed["question"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"Picker LLM returned bad JSON: {exc}; got: {raw[:300]}")

    usage = response.usage
    return PickerResult(
        question=question,
        sql=sql.strip(),
        reasoning=parsed.get("reasoning", ""),
        model=response.model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        latency_ms=latency_ms,
    )


def narrate(
    question: str,
    columns: list[str],
    rows: list[list[Any]],
    *,
    client: anthropic.Anthropic | None = None,
) -> NarratorResult:
    cli = client or _client()
    payload = json.dumps(
        {"question": question, "columns": columns, "rows": rows},
        default=str,
    )
    start = time.perf_counter()
    response = cli.messages.create(
        model=settings.RECAP_MODEL,
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": NARRATOR_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": payload}],
    )
    latency_ms = int((time.perf_counter() - start) * 1000)
    text_out = "\n".join(b.text for b in response.content if b.type == "text").strip()

    usage = response.usage
    return NarratorResult(
        narration=text_out,
        model=response.model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        latency_ms=latency_ms,
    )
