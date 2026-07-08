"""GET /api/v1/races/{race_id}/recap — personalized, cached race recaps."""

from datetime import datetime

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.core.database import get_db
from app.models import Race, RaceRecap, RaceResult, User
from app.schemas.errors import UNAUTHORIZED
from app.schemas.recap import RecapResponse
from app.services.recap.llm import get_llm_client
from app.services.recap.prompts import PROMPT_VERSION
from app.services.recap.service import RecapService


router = APIRouter(prefix="/api/v1/races", tags=["Recaps"], responses=UNAUTHORIZED)


@router.get(
    "/{race_id}/recap",
    response_model=RecapResponse,
    responses={
        404: {"description": "Race not found or has no results yet"},
        402: {"description": "Anthropic credit balance exhausted"},
        503: {"description": "LLM upstream unavailable"},
    },
)
def get_race_recap(
    race_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> RecapResponse:
    """Personalized recap for a completed race.

    Get-or-generate keyed on (race, user, prompt_version): the first request
    pays the LLM call (~5s); repeats are instant. A prompt-version bump
    naturally invalidates old recaps.
    """
    race = db.query(Race).filter(Race.id == race_id).first()
    if race is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    cached = (
        db.query(RaceRecap)
        .filter(
            RaceRecap.race_id == race_id,
            RaceRecap.user_id == user.id,
            RaceRecap.prompt_version == PROMPT_VERSION,
        )
        .first()
    )
    if cached is not None:
        return _to_response(cached, was_cached=True)

    has_results = db.query(RaceResult.id).filter(RaceResult.race_id == race_id).first()
    if has_results is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No results for this race yet — recaps are generated after the race finishes",
        )

    try:
        generated = RecapService(db, get_llm_client()).generate(user=user, race=race)
    except ValueError as exc:
        if "ANTHROPIC_API_KEY" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"message": "Server is missing ANTHROPIC_API_KEY."},
            )
        raise
    except anthropic.BadRequestError as exc:
        body = getattr(exc, "body", None) or {}
        err = body.get("error") if isinstance(body, dict) else None
        msg = err.get("message", "") if isinstance(err, dict) else ""
        if "credit" in msg.lower() and "balance" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"message": "Anthropic credit balance is too low."},
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": f"LLM rejected the request: {msg or str(exc)[:200]}"},
        )
    except anthropic.RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": "Anthropic API rate limit hit. Try again in a minute."},
        )
    except anthropic.APIError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Anthropic API returned an error. Try again shortly."},
        )

    recap = RaceRecap(
        race_id=race_id,
        user_id=user.id,
        prompt_version=PROMPT_VERSION,
        content=generated.content,
        model=generated.generation.model,
    )
    db.add(recap)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent request generated the same recap first — serve theirs.
        db.rollback()
        recap = (
            db.query(RaceRecap)
            .filter(
                RaceRecap.race_id == race_id,
                RaceRecap.user_id == user.id,
                RaceRecap.prompt_version == PROMPT_VERSION,
            )
            .first()
        )
        if recap is None:  # unexpected — IntegrityError from something else
            raise
        return _to_response(recap, was_cached=True)
    db.refresh(recap)

    return _to_response(recap, was_cached=False)


def _to_response(recap: RaceRecap, *, was_cached: bool) -> RecapResponse:
    return RecapResponse(
        race_id=recap.race_id,
        content=recap.content,
        prompt_version=recap.prompt_version,
        model=recap.model,
        created_at=recap.created_at or datetime.utcnow(),
        cached=was_cached,
    )
