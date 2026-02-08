from sqlalchemy import Column, String
from app.core.database import Base
from app.models.f1.base import SCHEMA


class Circuit(Base):
    __tablename__ = "circuits"
    __table_args__ = {"schema": SCHEMA}

    circuit_id = Column(String, primary_key=True)  # e.g., "monza"
    name = Column(String, nullable=False)
    locality = Column(String)  # City
    country = Column(String)
