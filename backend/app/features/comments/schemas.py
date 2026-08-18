"""Pydantic schemas for comment threads."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
    # NULL/omitted → a new top-level comment; otherwise a reply to this id.
    parent_id: int | None = None


class CommentNode(BaseModel):
    """One node in the rendered tree. ``replies`` nests the same shape, so the
    whole thread serialises as nested JSON the frontend renders with a
    recursive (DFS) component."""

    id: int
    user_id: int
    author: str
    body: str
    is_deleted: bool
    created_at: datetime
    replies: list["CommentNode"] = Field(default_factory=list)


# Self-referential model — finalise the forward reference.
CommentNode.model_rebuild()
