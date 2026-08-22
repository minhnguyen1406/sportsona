"""Analytics endpoints under /api/v1/f1 (see services/stats.py for the
algorithm behind each one)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.sports.f1.services import stats


router = APIRouter(tags=["F1 stats"])


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except stats.StatsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/drivers/{driver_id}/form")
def form(driver_id: str, k: int = Query(5, ge=2, le=10), db: Session = Depends(get_db)) -> dict:
    """Rolling k-race points average + momentum (sliding window)."""
    return _run(stats.form_guide, db, driver_id, k)


@router.get("/drivers/{driver_id}/streaks")
def streaks_(driver_id: str, db: Session = Depends(get_db)) -> dict:
    """Longest win/podium/points streaks + hottest stretch (Kadane)."""
    return _run(stats.career_streaks, db, driver_id)


@router.get("/drivers/{driver_id}/progression")
def progression(driver_id: str, season: int = Query(...), db: Session = Depends(get_db)) -> dict:
    """Cumulative points per round (prefix sums)."""
    return _run(stats.progression, db, driver_id, season)


@router.get("/careers/overlap")
def overlap(a: str = Query(...), b: str = Query(...), db: Session = Depends(get_db)) -> dict:
    """Did two careers overlap, and for which seasons (intervals)."""
    return _run(stats.career_overlap, db, a, b)


@router.get("/careers/active")
def active(year: int = Query(..., ge=1950, le=2100), db: Session = Depends(get_db)) -> dict:
    """Drivers active in a season + the all-time peak (sweep line)."""
    return _run(stats.active_in, db, year)


@router.get("/seasons/{year}/title-math")
def title_math(year: int, db: Session = Depends(get_db)) -> dict:
    """Who can still mathematically win the championship (greedy bound)."""
    return _run(stats.title_math, db, year)


@router.get("/fantasy/optimize")
def fantasy(
    season: int = Query(...), budget: int = Query(100, ge=1, le=500),
    max_drivers: int = Query(5, ge=1, le=10), db: Session = Depends(get_db),
) -> dict:
    """Best-points roster under a budget (0/1 knapsack)."""
    return _run(stats.fantasy_optimize, db, season, budget, max_drivers)


@router.get("/races/{race_id}/lap-rank")
def lap_rank(race_id: int, time: str = Query(..., max_length=12), db: Session = Depends(get_db)) -> dict:
    """Where a lap time would rank in the race's qualifying field (binary search)."""
    try:
        stats.parse_lap_time(time)
    except ValueError:
        raise HTTPException(status_code=400, detail="time must look like 1:12.051 or 72.051")
    return _run(stats.lap_rank, db, race_id, time)
