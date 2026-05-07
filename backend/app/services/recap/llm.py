"""LLM client for recap generation.

Uses Anthropic's prompt caching: the system prompt (style guide + format
rules) is cached with ``cache_control: ephemeral``. After the first call,
the system prompt's ~1500 tokens are read at ~0.1× input cost — a
significant cost reduction at scale, with zero behavioral change for callers.

Caller-facing surface is the ``LLMClient`` Protocol so we can swap in a
stub for tests or, later, A/B a different provider without touching the
service orchestrator.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

import anthropic

from app.core.config import settings
from app.services.recap.prompts import SYSTEM_PROMPT


@dataclass
class GenerationResult:
    """Output of a single LLM call. Captures cost + latency for observability."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    latency_ms: int


class LLMClient(Protocol):
    """Pluggable LLM backend. Implementations must be sync (matches our DB layer)."""

    def generate_recap(self, user_message: str) -> GenerationResult: ...


class AnthropicClient:
    """Anthropic-backed LLM client with prompt caching enabled."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-opus-4-7",
        max_tokens: int = 1500,
    ):
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not configured. Set it in .env to enable recap generation."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def generate_recap(self, user_message: str) -> GenerationResult:
        start = time.perf_counter()
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            # System block as a list with cache_control — the rendered tokens
            # are cached for ~5 minutes on first call, then read at 0.1× cost.
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        # response.content is a list of content blocks; concatenate text blocks.
        content = "\n".join(b.text for b in response.content if b.type == "text")

        usage = response.usage
        return GenerationResult(
            content=content,
            model=response.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            latency_ms=latency_ms,
        )


def get_llm_client() -> LLMClient:
    """Single source of truth for the production LLM client.

    FastAPI dependency-injection target later — for now, callers can use this
    directly to avoid plumbing config through every layer.
    """
    return AnthropicClient(
        api_key=settings.ANTHROPIC_API_KEY,
        model=settings.RECAP_MODEL,
        max_tokens=settings.RECAP_MAX_OUTPUT_TOKENS,
    )
