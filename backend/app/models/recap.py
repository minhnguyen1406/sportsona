"""Persisted race recaps — one per (race, user, prompt_version).

Regenerating on every page view would cost an LLM call each time; caching on
prompt_version means a prompt iteration naturally invalidates old recaps
without a migration.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func

from app.core.database import Base
from app.models.f1.base import SCHEMA


class RaceRecap(Base):
    __tablename__ = "race_recaps"
    __table_args__ = (
        UniqueConstraint("race_id", "user_id", "prompt_version", name="uq_race_recap"),
    )

    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey(f"{SCHEMA}.races.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prompt_version = Column(String, nullable=False)
    content = Column(String, nullable=False)
    model = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
