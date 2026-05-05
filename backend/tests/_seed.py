"""Small helpers for seeding F1 fixtures into the test DB.

Kept intentionally thin — tests stay readable when the seed code is one
function call per concept.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models import (
    Circuit,
    Constructor,
    ConstructorStanding,
    Driver,
    DriverStanding,
    QualifyingResult,
    Race,
    RaceResult,
    Season,
    User,
)


def make_season(db: Session, year: int) -> Season:
    s = Season(year=year)
    db.add(s)
    db.flush()
    return s


def make_circuit(db: Session, circuit_id: str = "monza", name: str = "Monza", country: str | None = "Italy") -> Circuit:
    c = Circuit(circuit_id=circuit_id, name=name, country=country)
    db.add(c)
    db.flush()
    return c


def make_driver(
    db: Session,
    driver_id: str,
    given_name: str = "First",
    family_name: str = "Last",
    nationality: str | None = None,
    dob: date | None = None,
) -> Driver:
    d = Driver(
        driver_id=driver_id,
        given_name=given_name,
        family_name=family_name,
        nationality=nationality,
        date_of_birth=dob,
    )
    db.add(d)
    db.flush()
    return d


def make_constructor(
    db: Session, constructor_id: str, name: str = "Team", nationality: str | None = None
) -> Constructor:
    c = Constructor(constructor_id=constructor_id, name=name, nationality=nationality)
    db.add(c)
    db.flush()
    return c


def make_race(
    db: Session,
    *,
    season: int,
    round_number: int,
    name: str = "Race",
    circuit_id: str = "monza",
    race_date: date | None = None,
) -> Race:
    r = Race(
        season=season,
        round=round_number,
        name=name,
        circuit_id=circuit_id,
        date=race_date or date(season, 9, 1),
    )
    db.add(r)
    db.flush()
    return r


def make_race_result(
    db: Session,
    *,
    race_id: int,
    driver_id: str,
    constructor_id: str,
    position: int | None = 1,
    points: float = 25.0,
    status: str = "Finished",
) -> RaceResult:
    rr = RaceResult(
        race_id=race_id,
        driver_id=driver_id,
        constructor_id=constructor_id,
        position=position,
        position_text=str(position) if position is not None else "R",
        points=points,
        status=status,
    )
    db.add(rr)
    db.flush()
    return rr


def make_qualifying_result(
    db: Session,
    *,
    race_id: int,
    driver_id: str,
    constructor_id: str,
    position: int | None = 1,
) -> QualifyingResult:
    qr = QualifyingResult(
        race_id=race_id,
        driver_id=driver_id,
        constructor_id=constructor_id,
        position=position,
    )
    db.add(qr)
    db.flush()
    return qr


def make_driver_standing(
    db: Session,
    *,
    season: int,
    round_number: int,
    driver_id: str,
    position: int = 1,
    points: float = 25.0,
    wins: int = 1,
) -> DriverStanding:
    ds = DriverStanding(
        season=season,
        round=round_number,
        driver_id=driver_id,
        position=position,
        points=points,
        wins=wins,
    )
    db.add(ds)
    db.flush()
    return ds


def make_user(
    db: Session,
    *,
    email: str = "user@example.com",
    username: str = "user",
    password: str = "correct horse battery staple",
    is_active: bool = True,
    is_superuser: bool = False,
    is_verified: bool = False,
) -> User:
    """Create a User with a real bcrypt-hashed password."""
    from app.auth.security import hash_password

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        is_active=is_active,
        is_superuser=is_superuser,
        is_verified=is_verified,
    )
    db.add(user)
    db.flush()
    return user


def make_constructor_standing(
    db: Session,
    *,
    season: int,
    round_number: int,
    constructor_id: str,
    position: int = 1,
    points: float = 25.0,
    wins: int = 1,
) -> ConstructorStanding:
    cs = ConstructorStanding(
        season=season,
        round=round_number,
        constructor_id=constructor_id,
        position=position,
        points=points,
        wins=wins,
    )
    db.add(cs)
    db.flush()
    return cs
