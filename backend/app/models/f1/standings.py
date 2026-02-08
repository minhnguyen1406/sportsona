from sqlalchemy import Column, String, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.f1.base import SCHEMA


class DriverStanding(Base):
    __tablename__ = "driver_standings"
    __table_args__ = (
        UniqueConstraint("season", "round", "driver_id", name="uq_driver_standing"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, ForeignKey(f"{SCHEMA}.seasons.year"), nullable=False, index=True)
    round = Column(Integer, nullable=False)  # Standings after this round
    driver_id = Column(String, ForeignKey(f"{SCHEMA}.drivers.driver_id"), nullable=False)

    position = Column(Integer, nullable=False)
    points = Column(Float, nullable=False)
    wins = Column(Integer, default=0)

    # Relationships
    driver = relationship("Driver", back_populates="standings")


class ConstructorStanding(Base):
    __tablename__ = "constructor_standings"
    __table_args__ = (
        UniqueConstraint("season", "round", "constructor_id", name="uq_constructor_standing"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, ForeignKey(f"{SCHEMA}.seasons.year"), nullable=False, index=True)
    round = Column(Integer, nullable=False)  # Standings after this round
    constructor_id = Column(String, ForeignKey(f"{SCHEMA}.constructors.constructor_id"), nullable=False)

    position = Column(Integer, nullable=False)
    points = Column(Float, nullable=False)
    wins = Column(Integer, default=0)

    # Relationships
    constructor = relationship("Constructor", back_populates="standings")
