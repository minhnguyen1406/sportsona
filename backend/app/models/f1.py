from sqlalchemy import Column, String, Integer, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.user import user_driver_follows, user_constructor_follows

class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(String, primary_key=True)  # e.g., "max_verstappen"
    given_name = Column(String, nullable=False)
    family_name = Column(String, nullable=False)
    nationality = Column(String)
    number = Column(Integer, unique=True)
    code = Column(String, unique=True)  # e.g., "VER"

    # Relationships
    current_team_id = Column(String, ForeignKey("constructors.constructor_id"))
    current_team = relationship("Constructor", back_populates="drivers")
    followers = relationship("User", secondary=user_driver_follows, back_populates="followed_drivers")

class Constructor(Base):
    __tablename__ = "constructors"

    constructor_id = Column(String, primary_key=True)  # e.g., "red_bull"
    name = Column(String, nullable=False)
    nationality = Column(String)

    # Relationships
    drivers = relationship("Driver", back_populates="current_team")
    followers = relationship("User", secondary=user_constructor_follows, back_populates="followed_constructors")

class Race(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, nullable=False, index=True)
    round = Column(Integer, nullable=False)
    race_name = Column(String, nullable=False)
    circuit_id = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time)

    # Relationships
    results = relationship("RaceResult", back_populates="race")

class RaceResult(Base):
    __tablename__ = "race_results"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    driver_id = Column(String, ForeignKey("drivers.driver_id"), nullable=False)

    position = Column(Integer)
    points = Column(Integer)
    time = Column(String)
    status = Column(String)  # "Finished", "Retired", etc.

    # Relationships
    race = relationship("Race", back_populates="results")
    driver = relationship("Driver")
