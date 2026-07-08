"""GET /api/v1/stat-of-the-day — auth-required, one stat per UTC date."""

from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.core.database import get_db
from app.models import User
from app.schemas.errors import UNAUTHORIZED
from app.schemas.stat_of_day import StatOfDayResponse
from app.services.stat_of_day import StatOfDayFailure, get_or_generate


router = APIRouter(
    prefix="/api/v1/stat-of-the-day",
    tags=["Stat of the day"],
    responses=UNAUTHORIZED,
)


@router.get(
    "",
    response_model=StatOfDayResponse,
    responses={
        402: {"description": "Anthropic credit balance exhausted"},
        502: {"description": "LLM returned malformed output"},
        503: {"description": "LLM upstream unavailable"},
    },
)
def read_stat_of_day(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> StatOfDayResponse:
    """Return today's curated F1 stat. First call of the day generates and
    caches; subsequent calls fetch from the cache. UTC date is the key.
    """
    today = datetime.now(timezone.utc).date()
    try:
        stat = get_or_generate(db, today)
    except StatOfDayFailure as exc:
        # Picker SQL didn't validate or errored against the DB. Surface as
        # 502 — the LLM's fault, not the user's.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": str(exc)},
        )
    except ValueError as exc:
        msg = str(exc)
        if "ANTHROPIC_API_KEY" in msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"message": "Server is missing ANTHROPIC_API_KEY. Ask the admin to configure it."},
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Claude returned malformed JSON. Try again later."},
        )
    except anthropic.BadRequestError as exc:
        body = getattr(exc, "body", None) or {}
        err = body.get("error") if isinstance(body, dict) else None
        msg = err.get("message", "") if isinstance(err, dict) else ""
        if "credit" in msg.lower() and "balance" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={"message": "Anthropic credit balance is too low. Top up to keep stat-of-the-day running."},
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": f"LLM rejected the request: {msg or str(exc)[:200]}"},
        )
    except anthropic.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "Server's Anthropic API key was rejected."},
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

    return StatOfDayResponse.model_validate(stat)
