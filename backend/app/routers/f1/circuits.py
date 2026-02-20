
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.f1 import Circuit
from app.schemas.f1 import CircuitResponse

router = APIRouter()


@router.get("/circuits", response_model=list[CircuitResponse])
def list_circuits(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all circuits with pagination."""
    circuits = (
        db.query(Circuit)
        .order_by(Circuit.name)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return circuits


@router.get("/circuits/{circuit_id}", response_model=CircuitResponse)
def get_circuit(circuit_id: str, db: Session = Depends(get_db)):
    """Get a specific circuit by ID."""
    circuit = db.query(Circuit).filter(Circuit.circuit_id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return circuit
