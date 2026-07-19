"""Immutable snapshots of /ask answers — one row per ask, shareable by slug.

Distinct from ask_cache on purpose: the cache is keyed by normalized question
and *expires* (data changes after syncs); a shared link must show exactly what
the asker saw, forever. Snapshot semantics, no TTL.
"""

import secrets

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

# JSONB on Postgres; falls back to plain JSON on the SQLite test harness.
_JSON = JSON().with_variant(JSONB(), "postgresql")


def _new_slug() -> str:
    """URL-safe, unguessable, short enough to share: ~11 chars."""
    return secrets.token_urlsafe(8)


class AskAnswer(Base):
    __tablename__ = "ask_answers"

    slug = Column(String(24), primary_key=True, default=_new_slug)
    # Nullable: anonymous asks are still shareable, they just have no owner.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    question = Column(String, nullable=False)
    sql = Column(String, nullable=False)
    reasoning = Column(String, nullable=False)
    columns = Column(_JSON, nullable=False)
    rows = Column(_JSON, nullable=False)
    truncated = Column(Boolean, nullable=False, default=False)
    model = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
