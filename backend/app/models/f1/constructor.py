from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.f1.base import SCHEMA


class Constructor(Base):
    __tablename__ = "constructors"
    __table_args__ = {"schema": SCHEMA}

    constructor_id = Column(String, primary_key=True)  # e.g., "red_bull"
    name = Column(String, nullable=False)
    nationality = Column(String)

    # Relationships
    standings = relationship("ConstructorStanding", back_populates="constructor")
