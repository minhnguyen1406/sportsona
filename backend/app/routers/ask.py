"""POST /api/v1/ask — natural-language F1 stats question → SQL → rows.

Also serves stored answer snapshots (public, by slug) and the signed-in
user's ask history.
"""

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user, get_optional_user
from app.auth.rate_limit import limiter
from app.core.database import get_db
from app.models import AskAnswer, User
from app.schemas.ask import AskAnswerResponse, AskHistoryItem, AskRequest, AskResponse
from app.schemas.errors import RATE_LIMITED, UNAUTHORIZED
from app.services.ask import AskFailure, answer_question


router = APIRouter(prefix="/api/v1/ask", tags=["Ask"])

HISTORY_LIMIT = 20


def _http_from_llm_exception(exc: Exception) -> HTTPException | None:
    """Translate Anthropic SDK / LLM failures into a friendly HTTPException.

    Returns None when ``exc`` isn't an LLM error — callers should re-raise
    those so the default 500 handler kicks in with a stack trace logged.
    """
    if isinstance(exc, anthropic.AuthenticationError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "The server's Anthropic API key was rejected. Ask the admin to rotate it."},
        )

    if isinstance(exc, anthropic.BadRequestError):
        body = getattr(exc, "body", None) or {}
        err = body.get("error") if isinstance(body, dict) else None
        msg = err.get("message", "") if isinstance(err, dict) else ""
        # The credit-balance-too-low case is by far the most common in dev
        # — surface it as a payment-required so the page can prompt to top up.
        if "credit" in msg.lower() and "balance" in msg.lower():
            return HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "message": (
                        "Anthropic credit balance is too low. "
                        "Top up at console.anthropic.com → Plans & Billing."
                    )
                },
            )
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": f"LLM rejected the request: {msg or str(exc)[:200]}"},
        )

    if isinstance(exc, anthropic.RateLimitError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": "Anthropic API rate limit hit. Try again in a minute."},
        )

    if isinstance(exc, anthropic.APIConnectionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "Couldn't reach Anthropic. Check the server's network and try again."},
        )

    if isinstance(exc, anthropic.APIStatusError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": f"Anthropic returned an error ({exc.status_code}). Try again shortly."},
        )

    return None


@router.post(
    "",
    response_model=AskResponse,
    responses={
        **RATE_LIMITED,
        400: {"description": "Bad question or LLM produced invalid SQL"},
        402: {"description": "Anthropic credit balance exhausted"},
        502: {"description": "Anthropic API returned an error"},
        503: {"description": "LLM upstream is unavailable"},
    },
)
@limiter.limit("30/hour")
def ask(
    request: Request,
    payload: AskRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> AskResponse:
    """Translate a natural-language F1 stats question into SQL, execute it
    against the read-only ``f1`` schema, and return the rows + the SQL that
    produced them. Calls Claude once per request, so it's rate-limited.

    Every successful answer is stored as an immutable snapshot so it can be
    shared by link; signed-in askers see theirs again in /ask/history.
    """
    try:
        result = answer_question(db, payload.question)
    except AskFailure as exc:
        # Validation failure — bad question, LLM produced unsafe SQL, or
        # the query errored against the DB. Always a 400 with the message.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(exc), "sql": exc.sql},
        )
    except ValueError as exc:
        # ValueError comes from two places in app/services/ask/llm.py:
        # (1) missing ANTHROPIC_API_KEY at client construction, or
        # (2) Claude's response didn't parse as JSON. Both deserve a
        # distinct, user-actionable message — never a raw 500.
        msg = str(exc)
        if "ANTHROPIC_API_KEY" in msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"message": "Server is missing ANTHROPIC_API_KEY. Ask the admin to configure it."},
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Claude returned malformed JSON. Try rephrasing the question."},
        )
    except anthropic.APIError as exc:
        # Catch the SDK base error and translate via the helper.
        http = _http_from_llm_exception(exc)
        if http is not None:
            raise http
        raise

    # Persist the snapshot. Best-effort: a storage hiccup shouldn't cost the
    # user their answer, so failures degrade to an unshareable response.
    answer_id: str | None = None
    try:
        answer = AskAnswer(
            user_id=user.id if user else None,
            question=result.question,
            sql=result.sql,
            reasoning=result.reasoning,
            columns=result.columns,
            rows=result.rows,
            truncated=result.truncated,
            model=result.model,
        )
        db.add(answer)
        db.commit()
        answer_id = answer.slug
    except Exception:
        db.rollback()

    return AskResponse(
        question=result.question,
        sql=result.sql,
        reasoning=result.reasoning,
        columns=result.columns,
        rows=result.rows,
        row_count=result.row_count,
        truncated=result.truncated,
        model=result.model,
        llm_latency_ms=result.llm_latency_ms,
        db_latency_ms=result.db_latency_ms,
        cache_read_tokens=result.cache_read_tokens,
        cached=result.cached,
        answer_id=answer_id,
    )


@router.get(
    "/history",
    response_model=list[AskHistoryItem],
    responses=UNAUTHORIZED,
)
def ask_history(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[AskAnswer]:
    """The signed-in user's most recent asks, newest first."""
    return (
        db.query(AskAnswer)
        .filter(AskAnswer.user_id == user.id)
        .order_by(AskAnswer.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )


@router.get(
    "/answers/{slug}",
    response_model=AskAnswerResponse,
    responses={404: {"description": "No answer with that link"}},
)
def get_answer(slug: str, db: Session = Depends(get_db)) -> AskAnswer:
    """Fetch a stored answer snapshot by its share slug. Public — the slug
    itself is the unguessable capability."""
    answer = db.query(AskAnswer).filter(AskAnswer.slug == slug).first()
    if answer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found")
    return answer
