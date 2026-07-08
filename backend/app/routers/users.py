"""Endpoints under ``/api/v1/users/me/*`` — profile, follow, and dashboard."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
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


def _latest_driver_standing(db: Session, driver_id: str) -> DriverStanding | None:
    return (
        db.query(DriverStanding)
        .filter(DriverStanding.driver_id == driver_id)
        .order_by(DriverStanding.season.desc(), DriverStanding.round.desc())
        .first()
    )


def _latest_constructor_standing(db: Session, constructor_id: str) -> ConstructorStanding | None:
    return (
        db.query(ConstructorStanding)
        .filter(ConstructorStanding.constructor_id == constructor_id)
        .order_by(ConstructorStanding.season.desc(), ConstructorStanding.round.desc())
        .first()
    )


def _recent_results(db: Session, driver_id: str, limit: int) -> list[RaceResult]:
    return (
        db.query(RaceResult)
        .join(Race, RaceResult.race_id == Race.id)
        .options(joinedload(RaceResult.race))
        .filter(RaceResult.driver_id == driver_id)
        .order_by(Race.date.desc())
        .limit(limit)
        .all()
    )


@router.get("/me/dashboard", response_model=DashboardResponse)
def get_dashboard(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Personalized dashboard for the current user.

    Aggregates: followed drivers (with latest standing + recent results),
    followed constructors (with latest standing), and the next upcoming race.
    """
    followed_drivers = []
    for driver in user.followed_drivers:
        latest = _latest_driver_standing(db, driver.driver_id)
        recent = _recent_results(db, driver.driver_id, DASHBOARD_RECENT_RESULTS_LIMIT)
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
        latest = _latest_constructor_standing(db, constructor.constructor_id)
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
