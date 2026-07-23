"""Cache of /ask answers keyed on the normalized question text.

Identical questions are common ("who has the most wins?") and each costs an
LLM call. Entries expire by age — F1 data changes after every race sync, so
a stale answer is worse than a slow one.
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

# JSONB on Postgres; falls back to plain JSON on the SQLite test harness.
_JSON = JSON().with_variant(JSONB(), "postgresql")


class AskCache(Base):
    __tablename__ = "ask_cache"

    id = Column(Integer, primary_key=True)
    question_normalized = Column(String, nullable=False, unique=True, index=True)
    question = Column(String, nullable=False)
    sql = Column(String, nullable=False)
    reasoning = Column(String, nullable=False)
    columns = Column(_JSON, nullable=False)
    rows = Column(_JSON, nullable=False)
    truncated = Column(Boolean, nullable=False, default=False)
    model = Column(String, nullable=False)
    hit_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
