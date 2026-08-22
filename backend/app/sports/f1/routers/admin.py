"""Superuser-only data-hygiene endpoints under /api/v1/f1/admin."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_superuser
from app.core.database import get_db
from app.models import User
from app.sports.f1.services import duplicates


router = APIRouter(prefix="/admin", tags=["F1 admin"])


class ClusterOut(BaseModel):
    ids: list[str]
    suggested_canonical: str
    signals: list[str]


class DuplicatesOut(BaseModel):
    drivers: list[ClusterOut]
    constructors: list[ClusterOut]


@router.get("/duplicates", response_model=DuplicatesOut, responses={403: {"description": "Superuser only"}})
def list_duplicates(
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> DuplicatesOut:
    """Rows that look like the same driver/team under different ids
    (union-find over identity signals). Review, then merge with the cleanup
    script — nothing here mutates data."""
    return DuplicatesOut(
        drivers=[ClusterOut(**c._asdict()) for c in duplicates.find_duplicate_drivers(db)],
        constructors=[ClusterOut(**c._asdict()) for c in duplicates.find_duplicate_constructors(db)],
    )
