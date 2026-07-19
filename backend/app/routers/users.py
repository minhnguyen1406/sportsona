"""Endpoints under ``/api/v1/users/me/*`` — profile, follow, and dashboard."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_active_user
from app.auth.security import hash_password, verify_password
from app.core.database import get_db
from app.models import (
    Constructor,
    ConstructorStanding,
    Driver,
    DriverStanding,
    Race,
    RaceResult,
    User,
)
from app.schemas.auth import UserRead
from app.schemas.errors import UNAUTHORIZED
from app.schemas.f1 import ConstructorResponse, DriverResponse
from app.schemas.users import (
    CurrentStanding,
    DashboardRaceResult,
    DashboardResponse,
    FollowedConstructorDashboard,
    FollowedDriverDashboard,
    UserUpdate,
)


# Every endpoint in this router requires authentication, so document 401
# once at the router level instead of repeating it on each operation.
router = APIRouter(prefix="/api/v1/users", tags=["Users"], responses=UNAUTHORIZED)


# Plan caps the MVP at 3 drivers / 2 constructors per user.
MAX_FOLLOWED_DRIVERS = 3
MAX_FOLLOWED_CONSTRUCTORS = 2

# Number of recent race results surfaced per followed driver in the dashboard.
DASHBOARD_RECENT_RESULTS_LIMIT = 3


# ---------------------------------------------------------------------------
# PATCH /me
# ---------------------------------------------------------------------------


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """Update the current user's username and/or password.

    Changing the password requires ``current_password`` for confirmation.
    """
    if payload.new_password is not None:
        if payload.current_password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="current_password is required to change password",
            )
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="current_password is incorrect",
            )
        user.hashed_password = hash_password(payload.new_password)

    if payload.username is not None and payload.username != user.username:
        taken = (
            db.query(User)
            .filter(User.username == payload.username, User.id != user.id)
            .first()
        )
        if taken is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        user.username = payload.username

    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Followed drivers
# ---------------------------------------------------------------------------


@router.get("/me/followed-drivers", response_model=list[DriverResponse])
def list_followed_drivers(user: User = Depends(get_current_active_user)) -> list[Driver]:
    return list(user.followed_drivers)


@router.post("/me/followed-drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def follow_driver(
    driver_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    if driver in user.followed_drivers:
        return  # idempotent

    if len(user.followed_drivers) >= MAX_FOLLOWED_DRIVERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot follow more than {MAX_FOLLOWED_DRIVERS} drivers",
        )

    user.followed_drivers.append(driver)
    db.commit()


@router.delete("/me/followed-drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_driver(
    driver_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    driver = next((d for d in user.followed_drivers if d.driver_id == driver_id), None)
    if driver is None:
        return  # idempotent — not following, nothing to remove

    user.followed_drivers.remove(driver)
    db.commit()


# ---------------------------------------------------------------------------
# Followed constructors
# ---------------------------------------------------------------------------


@router.get("/me/followed-constructors", response_model=list[ConstructorResponse])
def list_followed_constructors(
    user: User = Depends(get_current_active_user),
) -> list[Constructor]:
    return list(user.followed_constructors)


@router.post(
    "/me/followed-constructors/{constructor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def follow_constructor(
    constructor_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    constructor = (
        db.query(Constructor).filter(Constructor.constructor_id == constructor_id).first()
    )
    if constructor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Constructor not found")

    if constructor in user.followed_constructors:
        return

    if len(user.followed_constructors) >= MAX_FOLLOWED_CONSTRUCTORS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot follow more than {MAX_FOLLOWED_CONSTRUCTORS} constructors",
        )

    user.followed_constructors.append(constructor)
    db.commit()


@router.delete(
    "/me/followed-constructors/{constructor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unfollow_constructor(
    constructor_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    constructor = next(
        (c for c in user.followed_constructors if c.constructor_id == constructor_id), None
    )
    if constructor is None:
        return

    user.followed_constructors.remove(constructor)
    db.commit()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Dashboard batch queries.
#
# Naive version was one query per followed entity (classic N+1): O(F) round
# trips for F follows. These helpers fetch ALL follows in one query each
# using a ROW_NUMBER() window ("top-K per group" — the SQL analogue of
# keeping a size-K heap per key), then regroup rows into a hashmap for O(1)
# per-entity lookup while building the response.
# ---------------------------------------------------------------------------


def _latest_driver_standings(db: Session, driver_ids: list[str]) -> dict[str, DriverStanding]:
    """Latest standing per driver, one query. Returns {driver_id: standing}."""
    if not driver_ids:
        return {}
    rn = (
        func.row_number()
        .over(
            partition_by=DriverStanding.driver_id,
            order_by=[DriverStanding.season.desc(), DriverStanding.round.desc()],
        )
        .label("rn")
    )
    ranked = (
        db.query(DriverStanding.id.label("standing_id"), rn)
        .filter(DriverStanding.driver_id.in_(driver_ids))
        .subquery()
    )
    rows = (
        db.query(DriverStanding)
        .join(ranked, DriverStanding.id == ranked.c.standing_id)
        .filter(ranked.c.rn == 1)
        .all()
    )
    return {s.driver_id: s for s in rows}


def _latest_constructor_standings(
    db: Session, constructor_ids: list[str]
) -> dict[str, ConstructorStanding]:
    """Latest standing per constructor, one query. Returns {constructor_id: standing}."""
    if not constructor_ids:
        return {}
    rn = (
        func.row_number()
        .over(
            partition_by=ConstructorStanding.constructor_id,
            order_by=[ConstructorStanding.season.desc(), ConstructorStanding.round.desc()],
        )
        .label("rn")
    )
    ranked = (
        db.query(ConstructorStanding.id.label("standing_id"), rn)
        .filter(ConstructorStanding.constructor_id.in_(constructor_ids))
        .subquery()
    )
    rows = (
        db.query(ConstructorStanding)
        .join(ranked, ConstructorStanding.id == ranked.c.standing_id)
        .filter(ranked.c.rn == 1)
        .all()
    )
    return {s.constructor_id: s for s in rows}


def _recent_results_by_driver(
    db: Session, driver_ids: list[str], limit: int
) -> dict[str, list[RaceResult]]:
    """Most recent `limit` results per driver, one query.

    Returns {driver_id: [results, newest first]}.
    """
    if not driver_ids:
        return {}
    rn = (
        func.row_number()
        .over(
            partition_by=RaceResult.driver_id,
            order_by=[Race.date.desc(), Race.id.desc()],
        )
        .label("rn")
    )
    ranked = (
        db.query(RaceResult.id.label("result_id"), rn)
        .join(Race, RaceResult.race_id == Race.id)
        .filter(RaceResult.driver_id.in_(driver_ids))
        .subquery()
    )
    rows = (
        db.query(RaceResult)
        .options(joinedload(RaceResult.race))
        .join(ranked, RaceResult.id == ranked.c.result_id)
        .filter(ranked.c.rn <= limit)
        .all()
    )
    grouped: dict[str, list[RaceResult]] = {}
    for result in rows:
        grouped.setdefault(result.driver_id, []).append(result)
    # The join loses the window's ordering guarantee — restore newest-first.
    # Each list is ≤ limit items, so this is O(F · limit · log limit) ≈ free.
    for results in grouped.values():
        results.sort(key=lambda r: (r.race.date, r.race.id), reverse=True)
    return grouped


@router.get("/me/dashboard", response_model=DashboardResponse)
def get_dashboard(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Personalized dashboard for the current user.

    Aggregates: followed drivers (with latest standing + recent results),
    followed constructors (with latest standing), and the next upcoming race.
    """
    # Batch: 3 queries total regardless of how many drivers/teams are
    # followed (was 2 per driver + 1 per constructor).
    driver_ids = [d.driver_id for d in user.followed_drivers]
    constructor_ids = [c.constructor_id for c in user.followed_constructors]
    standings_by_driver = _latest_driver_standings(db, driver_ids)
    results_by_driver = _recent_results_by_driver(db, driver_ids, DASHBOARD_RECENT_RESULTS_LIMIT)
    standings_by_constructor = _latest_constructor_standings(db, constructor_ids)

    followed_drivers = []
    for driver in user.followed_drivers:
        latest = standings_by_driver.get(driver.driver_id)
        recent = results_by_driver.get(driver.driver_id, [])
        followed_drivers.append(
            FollowedDriverDashboard(
                driver=DriverResponse.model_validate(driver),
                current_standing=(
                    CurrentStanding.model_validate(latest) if latest else None
                ),
                recent_results=[
                    DashboardRaceResult(
                        race_id=r.race.id,
                        race_name=r.race.name,
                        season=r.race.season,
                        round=r.race.round,
                        date=r.race.date,
                        position=r.position,
                        points=r.points,
                    )
                    for r in recent
                ],
            )
        )

    followed_constructors = []
    for constructor in user.followed_constructors:
        latest = standings_by_constructor.get(constructor.constructor_id)
        followed_constructors.append(
            FollowedConstructorDashboard(
                constructor=ConstructorResponse.model_validate(constructor),
                current_standing=(
                    CurrentStanding.model_validate(latest) if latest else None
                ),
            )
        )

    next_race = (
        db.query(Race)
        .options(joinedload(Race.circuit))
        .filter(Race.date >= date.today())
        .order_by(Race.date.asc())
        .first()
    )

    return DashboardResponse(
        user=UserRead.model_validate(user),
        followed_drivers=followed_drivers,
        followed_constructors=followed_constructors,
        next_race=next_race,
    )
