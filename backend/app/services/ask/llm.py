"""LLM client for natural-language → SQL generation.

Mirrors the recap LLM client: a thin Protocol + an Anthropic implementation
with prompt caching on the (large) system prompt so each subsequent call
reads the schema doc at ~0.1× input cost.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Protocol

import anthropic

from app.core.config import settings
from app.services.ask.prompts import SYSTEM_PROMPT


@dataclass
class SqlGeneration:
    sql: str
    reasoning: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    latency_ms: int


class AskClient(Protocol):
    def generate_sql(self, question: str) -> SqlGeneration: ...


class AnthropicAskClient:
    def __init__(self, api_key: str, model: str = "claude-opus-4-7", max_tokens: int = 700):
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not configured. Set it in .env to enable /ask."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def generate_sql(self, question: str) -> SqlGeneration:
        start = time.perf_counter()
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": question}],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        raw = "\n".join(b.text for b in response.content if b.type == "text").strip()
        # Be tolerant of fenced output even though we asked for plain JSON.
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            parsed = json.loads(raw)
            sql = parsed["sql"]
            reasoning = parsed.get("reasoning", "")
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"LLM did not return valid JSON: {exc}; got: {raw[:300]}")

        usage = response.usage
        return SqlGeneration(
            sql=sql.strip(),
            reasoning=reasoning,
            model=response.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            latency_ms=latency_ms,
        )


def get_ask_client() -> AskClient:
    return AnthropicAskClient(
        api_key=settings.ANTHROPIC_API_KEY,
        model=settings.RECAP_MODEL,
    )
