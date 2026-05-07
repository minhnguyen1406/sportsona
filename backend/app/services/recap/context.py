"""Typed context schema fed to the LLM for race recap generation.

Keeping this strictly typed and provider-agnostic means the prompt-rendering
layer stays a pure function of (Pydantic model → string), which is trivial
to unit test and easy to swap if we ever change LLM providers.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class QualifyingRow(BaseModel):
    position: int | None
    driver_name: str
    constructor_name: str
    q3_time: str | None = None


class RaceResultRow(BaseModel):
    position: int | None
    position_text: str | None
    driver_name: str
    constructor_name: str
    grid_position: int | None = None
    points: float
    laps: int | None = None
    status: str | None = None
    time_or_gap: str | None = None


class StandingRow(BaseModel):
    position: int
    name: str
    points: float
    wins: int


class ChampionshipState(BaseModel):
    drivers: list[StandingRow]
    constructors: list[StandingRow]


class NextRaceHint(BaseModel):
    name: str
    season: int
    round: int
    date: date
    circuit: str


class RecapContext(BaseModel):
    """Everything the LLM needs to generate a personalized race recap.

    Bounded in size: ≤25 race results, ≤30 standings each side, ≤5 follows.
    Total serialized length ≈ 2k tokens — safely well under any context window.
    """

    user_username: str
    followed_drivers: list[str]
    followed_constructors: list[str]

    race_name: str
    race_round: int
    race_season: int
    race_date: date
    circuit_name: str
    circuit_country: str | None = None

    qualifying: list[QualifyingRow]
    results: list[RaceResultRow]
    standings_after: ChampionshipState
    notable_status_events: list[str]
    next_race: NextRaceHint | None = None
