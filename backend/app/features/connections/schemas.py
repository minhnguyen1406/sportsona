from pydantic import BaseModel


class ViaOut(BaseModel):
    season: int
    constructor_id: str
    constructor: str


class HopOut(BaseModel):
    driver_id: str
    name: str
    via: ViaOut | None


class ConnectionOut(BaseModel):
    from_id: str
    to_id: str
    degrees: int
    path: list[HopOut]


class GraphStatsOut(BaseModel):
    drivers: int
    teammate_links: int
