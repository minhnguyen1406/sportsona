from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.f1 import Constructor
from app.schemas.f1 import ConstructorResponse

router = APIRouter()


@router.get("/constructors", response_model=list[ConstructorResponse])
def list_constructors(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all constructors with pagination."""
    constructors = (
        db.query(Constructor)
        .order_by(Constructor.name)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return constructors


@router.get("/constructors/{constructor_id}", response_model=ConstructorResponse)
def get_constructor(constructor_id: str, db: Session = Depends(get_db)):
    """Get a specific constructor by ID."""
    constructor = db.query(Constructor).filter(Constructor.constructor_id == constructor_id).first()
    if not constructor:
        raise HTTPException(status_code=404, detail="Constructor not found")
    return constructor
