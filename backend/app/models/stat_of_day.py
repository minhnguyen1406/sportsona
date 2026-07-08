"""Daily curated stat shown on the /today page — one row per UTC date."""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class StatOfDay(Base):
    __tablename__ = "stats_of_day"

    date = Column(Date, primary_key=True)
    question = Column(String, nullable=False)
    sql = Column(String, nullable=False)
    columns = Column(JSONB, nullable=False)
    rows = Column(JSONB, nullable=False)
    narration = Column(String, nullable=False)
    model = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.utcnow(),
    )
