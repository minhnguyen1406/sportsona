from sqlalchemy import Column, String, Integer, Date, Time, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.f1.base import SCHEMA


class Race(Base):
    __tablename__ = "races"
    __table_args__ = (
        UniqueConstraint("season", "round", name="uq_race_season_round"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, ForeignKey(f"{SCHEMA}.seasons.year"), nullable=False, index=True)
    round = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    circuit_id = Column(String, ForeignKey(f"{SCHEMA}.circuits.circuit_id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time)

    # Relationships
    season_ref = relationship("Season", back_populates="races")
    circuit = relationship("Circuit")
    results = relationship("RaceResult", back_populates="race")


class RaceResult(Base):
    __tablename__ = "race_results"
    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", name="uq_race_result"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey(f"{SCHEMA}.races.id"), nullable=False)
    driver_id = Column(String, ForeignKey(f"{SCHEMA}.drivers.driver_id"), nullable=False)
    constructor_id = Column(String, ForeignKey(f"{SCHEMA}.constructors.constructor_id"), nullable=False)

    grid_position = Column(Integer)  # Starting position
    position = Column(Integer)  # Finishing position (null if DNF)
    position_text = Column(String)  # "1", "2", "R" (retired), "D" (disqualified)
    points = Column(Float, default=0)
    laps = Column(Integer)
    time = Column(String)  # Race time or gap
    fastest_lap_time = Column(String)
    fastest_lap_rank = Column(Integer)
    status = Column(String)  # "Finished", "+1 Lap", "Collision", etc.

    # Relationships
    race = relationship("Race", back_populates="results")
    driver = relationship("Driver")
    constructor = relationship("Constructor")


class QualifyingResult(Base):
    __tablename__ = "qualifying_results"
    __table_args__ = (
        UniqueConstraint("race_id", "driver_id", name="uq_quali_result"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey(f"{SCHEMA}.races.id"), nullable=False)
    driver_id = Column(String, ForeignKey(f"{SCHEMA}.drivers.driver_id"), nullable=False)
    constructor_id = Column(String, ForeignKey(f"{SCHEMA}.constructors.constructor_id"), nullable=False)

    position = Column(Integer)
    q1_time = Column(String)
    q2_time = Column(String)
    q3_time = Column(String)

    # Relationships
    race = relationship("Race")
    driver = relationship("Driver")
    constructor = relationship("Constructor")
