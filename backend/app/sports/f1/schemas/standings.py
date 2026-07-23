from pydantic import BaseModel

from app.sports.f1.schemas.driver import DriverResponse
from app.sports.f1.schemas.constructor import ConstructorResponse


class DriverStandingResponse(BaseModel):
    id: int
    season: int
    round: int
    position: int
    points: float
    wins: int
    driver: DriverResponse

    model_config = {"from_attributes": True}


class ConstructorStandingResponse(BaseModel):
    id: int
    season: int
    round: int
    position: int
    points: float
    wins: int
    constructor: ConstructorResponse

    model_config = {"from_attributes": True}
