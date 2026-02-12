from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.f1 import Race, RaceResult, QualifyingResult
from app.schemas.f1 import RaceResponse, RaceResultResponse, QualifyingResultResponse

router = APIRouter()


@router.get("/races/{race_id}", response_model=RaceResponse)
def get_race(race_id: int, db: Session = Depends(get_db)):
    """Get a single race by ID, including circuit info."""
    race = (
        db.query(Race)
        .options(joinedload(Race.circuit))
        .filter(Race.id == race_id)
        .first()
    )
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race


@router.get("/races/{race_id}/results", response_model=list[RaceResultResponse])
def get_race_results(race_id: int, db: Session = Depends(get_db)):
    """Get results for a specific race, ordered by finishing position."""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    results = (
        db.query(RaceResult)
        .options(joinedload(RaceResult.driver), joinedload(RaceResult.constructor))
        .filter(RaceResult.race_id == race_id)
        .order_by(RaceResult.position.asc().nullslast())
        .all()
    )
    return results


@router.get("/races/{race_id}/qualifying", response_model=list[QualifyingResultResponse])
def get_qualifying_results(race_id: int, db: Session = Depends(get_db)):
    """Get qualifying results for a specific race."""
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    results = (
        db.query(QualifyingResult)
        .options(joinedload(QualifyingResult.driver), joinedload(QualifyingResult.constructor))
        .filter(QualifyingResult.race_id == race_id)
        .order_by(QualifyingResult.position.asc().nullslast())
        .all()
    )
    return results
