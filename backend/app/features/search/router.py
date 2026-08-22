"""GET /api/v1/search/suggest?q=ham — autocomplete suggestions (public)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.search import service
from app.features.search.schemas import SuggestionOut


router = APIRouter(prefix="/api/v1/search", tags=["Search"])


@router.get("/suggest", response_model=list[SuggestionOut])
def suggest(
    q: str = Query(min_length=1, max_length=60),
    limit: int = Query(default=8, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[SuggestionOut]:
    """Drivers and teams whose name (or any word of it) starts with ``q``."""
    return [SuggestionOut(**h._asdict()) for h in service.suggest(db, q, limit=limit)]
