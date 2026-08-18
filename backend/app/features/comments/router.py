"""Comment-thread endpoints.

  GET    /api/v1/races/{race_id}/comments   public — the threaded forest
  POST   /api/v1/races/{race_id}/comments   auth   — add a comment / reply
  DELETE /api/v1/comments/{comment_id}       auth   — tombstone your own
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.rate_limit import limiter
from app.common.errors import RATE_LIMITED, UNAUTHORIZED
from app.core.database import get_db
from app.features.comments import service
from app.features.comments.schemas import CommentCreate, CommentNode
from app.models import Race, User


router = APIRouter(prefix="/api/v1", tags=["Comments"])


@router.get("/races/{race_id}/comments", response_model=list[CommentNode])
def list_comments(race_id: int, db: Session = Depends(get_db)) -> list[CommentNode]:
    """The race's comment tree — top-level comments, each with nested replies,
    oldest first. Public: reading the conversation doesn't require an account."""
    return service.build_thread(db, race_id)


@router.post(
    "/races/{race_id}/comments",
    response_model=CommentNode,
    status_code=status.HTTP_201_CREATED,
    responses={**UNAUTHORIZED, **RATE_LIMITED, 404: {"description": "Race or parent not found"}},
)
@limiter.limit("30/minute")
def create_comment(
    request: Request,
    race_id: int,
    payload: CommentCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CommentNode:
    if db.query(Race.id).filter(Race.id == race_id).first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Race not found")

    try:
        comment = service.add_comment(
            db,
            race_id=race_id,
            user_id=user.id,
            body=payload.body,
            parent_id=payload.parent_id,
        )
    except service.CommentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return CommentNode(
        id=comment.id,
        user_id=comment.user_id,
        author=user.username,
        body=comment.body,
        is_deleted=False,
        created_at=comment.created_at,
        replies=[],
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**UNAUTHORIZED, 403: {"description": "Not your comment"}, 404: {"description": "Not found"}},
)
def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """Tombstone your own comment. Replies (if any) survive — the row stays as
    a "[deleted]" placeholder so the subtree isn't orphaned."""
    try:
        service.delete_comment(db, comment_id=comment_id, user_id=user.id)
    except service.CommentError as exc:
        msg = str(exc)
        if "own comments" in msg:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
