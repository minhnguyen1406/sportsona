"""Assemble a typed RecapContext from the SQL database.

All queries use ``joinedload`` so a single SELECT round-trip pulls the row
plus its FK relationships — no N+1. Each query touches an indexed column,
so the whole assembly is O(R + D + C + F) ≈ O(1) given F1's bounded sizes.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.models import (
    ConstructorStanding,
    DriverStanding,
    QualifyingResult,
    Race,
    RaceResult,
    User,
)
from app.services.recap.context import (
    ChampionshipState,
    NextRaceHint,
    QualifyingRow,
    RaceResultRow,
    RecapContext,
    StandingRow,
)


# Status strings that DON'T warrant a "notable incidents" callout.
_BENIGN_STATUSES = {"Finished", "+1 Lap", "+2 Laps", "+3 Laps", "+4 Laps"}


def _driver_full_name(given: str | None, family: str | None) -> str:
    return " ".join(part for part in (given, family) if part) or "Unknown driver"


def assemble_context(db: Session, user: User, race: Race) -> RecapContext:
    """Pull race, qualifying, results, standings, and next race into a single context.

    Five indexed queries, each returning a bounded number of rows. The
    ``joinedload`` calls are critical — without them this would N+1 on driver
    and constructor lookups.
    """
    # Race results — ordered by finishing position, NULL last for DNFs
    results = (
        db.query(RaceResult)
        .options(joinedload(RaceResult.driver), joinedload(RaceResult.constructor))
        .filter(RaceResult.race_id == race.id)
        .order_by(RaceResult.position.asc().nullslast())
        .all()
    )

    # Qualifying — ordered by qualifying position
    qualifying = (
        db.query(QualifyingResult)
        .options(joinedload(QualifyingResult.driver), joinedload(QualifyingResult.constructor))
        .filter(QualifyingResult.race_id == race.id)
        .order_by(QualifyingResult.position.asc().nullslast())
        .all()
    )

    # Standings AFTER this race (i.e. after this season+round)
    driver_standings = (
        db.query(DriverStanding)
        .options(joinedload(DriverStanding.driver))
        .filter(
            DriverStanding.season == race.season,
            DriverStanding.round == race.round,
        )
        .order_by(DriverStanding.position)
        .all()
    )
    constructor_standings = (
        db.query(ConstructorStanding)
        .options(joinedload(ConstructorStanding.constructor))
        .filter(
            ConstructorStanding.season == race.season,
            ConstructorStanding.round == race.round,
        )
        .order_by(ConstructorStanding.position)
        .all()
    )

    # Next race — soonest race scheduled after this one
    next_race = (
        db.query(Race)
        .options(joinedload(Race.circuit))
        .filter(Race.date > race.date)
        .order_by(Race.date.asc())
        .first()
    )

    # Notable status events — anything that isn't a clean finish
    notable_status_events = [
        f"{_driver_full_name(r.driver.given_name, r.driver.family_name)} — {r.status}"
        for r in results
        if r.status and r.status not in _BENIGN_STATUSES
    ]

    return RecapContext(
        user_username=user.username,
        followed_drivers=[
            _driver_full_name(d.given_name, d.family_name) for d in user.followed_drivers
        ],
        followed_constructors=[c.name for c in user.followed_constructors],
        race_name=race.name,
        race_round=race.round,
        race_season=race.season,
        race_date=race.date,
        circuit_name=race.circuit.name,
        circuit_country=race.circuit.country,
        qualifying=[
            QualifyingRow(
                position=q.position,
                driver_name=_driver_full_name(q.driver.given_name, q.driver.family_name),
                constructor_name=q.constructor.name,
                q3_time=q.q3_time,
            )
            for q in qualifying
        ],
        results=[
            RaceResultRow(
                position=r.position,
                position_text=r.position_text,
                driver_name=_driver_full_name(r.driver.given_name, r.driver.family_name),
                constructor_name=r.constructor.name,
                grid_position=r.grid_position,
                points=r.points,
                laps=r.laps,
                status=r.status,
                time_or_gap=r.time,
            )
            for r in results
        ],
        standings_after=ChampionshipState(
            drivers=[
                StandingRow(
                    position=s.position,
                    name=_driver_full_name(s.driver.given_name, s.driver.family_name),
                    points=s.points,
                    wins=s.wins,
                )
                for s in driver_standings
            ],
            constructors=[
                StandingRow(
                    position=s.position,
                    name=s.constructor.name,
                    points=s.points,
                    wins=s.wins,
                )
                for s in constructor_standings
            ],
        ),
        notable_status_events=notable_status_events,
        next_race=NextRaceHint(
            name=next_race.name,
            season=next_race.season,
            round=next_race.round,
            date=next_race.date,
            circuit=next_race.circuit.name,
        )
        if next_race
        else None,
    )
