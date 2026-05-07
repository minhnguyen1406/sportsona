"""Race recap orchestration: context → prompt → LLM → result.

Stateless and storage-agnostic by design. Adding persistence later is a
matter of wrapping ``generate()`` in a get-or-generate pattern keyed by
``(race_id, user_id, prompt_version)`` — the building blocks here don't
need to change.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Race, User
from app.services.recap.assembler import assemble_context
from app.services.recap.context import RecapContext
from app.services.recap.llm import GenerationResult, LLMClient
from app.services.recap.prompts import PROMPT_VERSION, render_user_message


@dataclass
class GeneratedRecap:
    """Output of a recap generation. Pairs the prose with the metadata
    needed to persist, observe, and reproduce the call."""

    content: str
    prompt_version: str
    context: RecapContext
    generation: GenerationResult


class RecapService:
    """Generate personalized race recaps.

    Inject ``llm`` so tests can pass a stub and so production can swap models
    by changing ``settings.RECAP_MODEL``.
    """

    def __init__(self, db: Session, llm: LLMClient):
        self._db = db
        self._llm = llm

    def generate(self, *, user: User, race: Race) -> GeneratedRecap:
        ctx = assemble_context(self._db, user, race)
        user_message = render_user_message(ctx)
        result = self._llm.generate_recap(user_message)
        return GeneratedRecap(
            content=result.content,
            prompt_version=PROMPT_VERSION,
            context=ctx,
            generation=result,
        )
