from pydantic import BaseModel
from datetime import date, time
from typing import Optional

from app.schemas.f1.circuit import CircuitResponse
from app.schemas.f1.driver import DriverResponse
from app.schemas.f1.constructor import ConstructorResponse


class RaceResponse(BaseModel):
    id: int
    season: int
    round: int
    name: str
    date: date
    time: Optional[time] = None
    circuit: CircuitResponse

    model_config = {"from_attributes": True}


class RaceBriefResponse(BaseModel):
    """Race without nested circuit — used when circuit context is already known."""
    id: int
    season: int
    round: int
    name: str
    date: date
    time: Optional[time] = None

    model_config = {"from_attributes": True}


class RaceResultResponse(BaseModel):
    id: int
    position: Optional[int] = None
    position_text: Optional[str] = None
    grid_position: Optional[int] = None
    points: float
    laps: Optional[int] = None
    time: Optional[str] = None
    fastest_lap_time: Optional[str] = None
    fastest_lap_rank: Optional[int] = None
    status: Optional[str] = None
    driver: DriverResponse
    constructor: ConstructorResponse

    model_config = {"from_attributes": True}


class QualifyingResultResponse(BaseModel):
    id: int
    position: Optional[int] = None
    q1_time: Optional[str] = None
    q2_time: Optional[str] = None
    q3_time: Optional[str] = None
    driver: DriverResponse
    constructor: ConstructorResponse

    model_config = {"from_attributes": True}
