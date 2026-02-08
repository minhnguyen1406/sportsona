from sqlalchemy import Column, String, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.f1.base import SCHEMA


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = {"schema": SCHEMA}

    driver_id = Column(String, primary_key=True)  # e.g., "max_verstappen"
    given_name = Column(String, nullable=False)
    family_name = Column(String, nullable=False)
    date_of_birth = Column(Date)
    nationality = Column(String)

    # Relationships
    standings = relationship("DriverStanding", back_populates="driver")


class DriverEntry(Base):
    """Driver's entry for a specific season (links driver to team per season)"""
    __tablename__ = "driver_entries"
    __table_args__ = (
        UniqueConstraint("season", "driver_id", "constructor_id", name="uq_driver_entry"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, ForeignKey(f"{SCHEMA}.seasons.year"), nullable=False)
    driver_id = Column(String, ForeignKey(f"{SCHEMA}.drivers.driver_id"), nullable=False)
    constructor_id = Column(String, ForeignKey(f"{SCHEMA}.constructors.constructor_id"), nullable=False)
    driver_number = Column(Integer)
    driver_code = Column(String(3))  # e.g., "VER"

    # Relationships
    driver = relationship("Driver")
    constructor = relationship("Constructor")
