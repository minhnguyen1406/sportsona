from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.sports.f1.models.base import SCHEMA


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = {"schema": SCHEMA}

    year = Column(Integer, primary_key=True)

    # Relationships
    races = relationship("Race", back_populates="season_ref")
