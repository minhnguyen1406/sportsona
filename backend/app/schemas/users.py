"""Schemas for ``/api/v1/users/*`` endpoints (PATCH /me, follow, dashboard)."""

from __future__ import annotations

from datetime import date as _date

from pydantic import BaseModel, Field

from app.schemas.auth import UserRead
from app.schemas.f1 import (
    ConstructorResponse,
    DriverResponse,
    RaceResponse,
)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    current_password: str | None = Field(default=None, min_length=8, max_length=72)
    new_password: str | None = Field(default=None, min_length=8, max_length=72)


class CurrentStanding(BaseModel):
    season: int
    round: int
    position: int
    points: float
    wins: int

    model_config = {"from_attributes": True}


class DashboardRaceResult(BaseModel):
    race_id: int
    race_name: str
    season: int
    round: int
    date: _date
    position: int | None = None
    points: float


class FollowedDriverDashboard(BaseModel):
    driver: DriverResponse
    current_standing: CurrentStanding | None = None
    recent_results: list[DashboardRaceResult] = []


class FollowedConstructorDashboard(BaseModel):
    constructor: ConstructorResponse
    current_standing: CurrentStanding | None = None


class DashboardResponse(BaseModel):
    user: UserRead
    followed_drivers: list[FollowedDriverDashboard]
    followed_constructors: list[FollowedConstructorDashboard]
    next_race: RaceResponse | None = None
