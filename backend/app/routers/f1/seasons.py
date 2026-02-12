from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.f1 import Season, Race, DriverStanding, ConstructorStanding
from app.schemas.f1 import (
    SeasonResponse,
    RaceResponse,
    DriverStandingResponse,
    ConstructorStandingResponse,
)

router = APIRouter()


@router.get("/seasons", response_model=list[SeasonResponse])
def list_seasons(db: Session = Depends(get_db)):
    """List all available seasons, most recent first."""
    seasons = db.query(Season).order_by(Season.year.desc()).all()
    return seasons


@router.get("/seasons/{year}/races", response_model=list[RaceResponse])
def list_races_by_season(year: int, db: Session = Depends(get_db)):
    """Get the race schedule for a given season, ordered by round."""
    races = (
        db.query(Race)
        .options(joinedload(Race.circuit))
        .filter(Race.season == year)
        .order_by(Race.round)
        .all()
    )
    if not races:
        raise HTTPException(status_code=404, detail=f"No races found for {year}")
    return races


@router.get("/seasons/{year}/standings/drivers", response_model=list[DriverStandingResponse])
def get_driver_standings(
    year: int,
    round: int | None = Query(None, description="Standings after this round (defaults to latest)"),
    db: Session = Depends(get_db),
):
    """Get driver standings for a season. Defaults to the latest available round."""
    if round is None:
        round = (
            db.query(func.max(DriverStanding.round))
            .filter(DriverStanding.season == year)
            .scalar()
        )
        if round is None:
            raise HTTPException(status_code=404, detail=f"No driver standings for {year}")

    standings = (
        db.query(DriverStanding)
        .options(joinedload(DriverStanding.driver))
        .filter(DriverStanding.season == year, DriverStanding.round == round)
        .order_by(DriverStanding.position)
        .all()
    )
    return standings


@router.get("/seasons/{year}/standings/constructors", response_model=list[ConstructorStandingResponse])
def get_constructor_standings(
    year: int,
    round: int | None = Query(None, description="Standings after this round (defaults to latest)"),
    db: Session = Depends(get_db),
):
    """Get constructor standings for a season. Defaults to the latest available round."""
    if round is None:
        round = (
            db.query(func.max(ConstructorStanding.round))
            .filter(ConstructorStanding.season == year)
            .scalar()
        )
        if round is None:
            raise HTTPException(status_code=404, detail=f"No constructor standings for {year}")

    standings = (
        db.query(ConstructorStanding)
        .options(joinedload(ConstructorStanding.constructor))
        .filter(ConstructorStanding.season == year, ConstructorStanding.round == round)
        .order_by(ConstructorStanding.position)
        .all()
    )
    return standings
