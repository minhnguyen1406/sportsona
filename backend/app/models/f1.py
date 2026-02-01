from sqlalchemy import Column, String, Integer, Date, Time, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

# All F1 tables live in 'f1' schema
SCHEMA = "f1"


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = {"schema": SCHEMA}

    year = Column(Integer, primary_key=True)

    # Relationships
    races = relationship("Race", back_populates="season_ref")


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


class Constructor(Base):
    __tablename__ = "constructors"
    __table_args__ = {"schema": SCHEMA}

    constructor_id = Column(String, primary_key=True)  # e.g., "red_bull"
    name = Column(String, nullable=False)
    nationality = Column(String)

    # Relationships
    standings = relationship("ConstructorStanding", back_populates="constructor")


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


class Circuit(Base):
    __tablename__ = "circuits"
    __table_args__ = {"schema": SCHEMA}

    circuit_id = Column(String, primary_key=True)  # e.g., "monza"
    name = Column(String, nullable=False)
    locality = Column(String)  # City
    country = Column(String)


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
