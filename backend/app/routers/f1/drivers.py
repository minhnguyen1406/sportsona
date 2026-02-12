from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.f1 import Driver
from app.schemas.f1 import DriverResponse

router = APIRouter()


@router.get("/drivers", response_model=list[DriverResponse])
def list_drivers(
    search: str | None = Query(None, description="Search by name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List drivers with optional search and pagination."""
    query = db.query(Driver)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Driver.given_name.ilike(pattern),
                Driver.family_name.ilike(pattern),
                Driver.driver_id.ilike(pattern),
            )
        )

    drivers = (
        query
        .order_by(Driver.family_name, Driver.given_name)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return drivers


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: str, db: Session = Depends(get_db)):
    """Get a specific driver by ID."""
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver
