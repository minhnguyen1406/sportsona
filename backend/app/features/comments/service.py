"""Comment-thread logic: build the tree, add, tombstone, fetch a subtree.

The headline is ``build_thread`` — reconstructing the tree from the flat rows
in O(n) with a hash map, the same move as "build an N-ary tree from a parent
array". ``subtree_ids`` shows the alternative: let Postgres walk the tree with
a recursive CTE (graph traversal in the database).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.features.comments.models import Comment
from app.features.comments.schemas import CommentNode


class CommentError(Exception):
    """Invalid comment operation (bad parent, not found, not the owner)."""


_DELETED_TEXT = "[deleted]"


def _to_node(c: Comment) -> CommentNode:
    """Map a row to a tree node, hiding tombstoned content."""
    hidden = c.is_deleted
    return CommentNode(
        id=c.id,
        user_id=c.user_id,
        author=_DELETED_TEXT if hidden else c.author.username,
        body=_DELETED_TEXT if hidden else c.body,
        is_deleted=hidden,
        created_at=c.created_at,
        replies=[],
    )


def build_thread(db: Session, race_id: int) -> list[CommentNode]:
    """Return the race's comment forest (top-level comments, each with nested
    replies), oldest first.

    Algorithm — O(n) tree reconstruction from an adjacency list:
      1. One query pulls every comment for the race (with its author).
      2. First pass: make a node per row, indexed by id in a dict — O(1) lookup.
      3. Second pass: attach each node to its parent's ``replies`` (dict.get),
         collecting parentless nodes as roots.
    Two passes so link order never depends on insert order. Total O(n) time and
    space, one SQL round-trip — versus the naive "recurse and re-query per
    level" which is O(depth) queries.
    """
    rows = (
        db.query(Comment)
        .filter(Comment.race_id == race_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    nodes: dict[int, CommentNode] = {c.id: _to_node(c) for c in rows}

    roots: list[CommentNode] = []
    for c in rows:
        node = nodes[c.id]
        parent = nodes.get(c.parent_id) if c.parent_id is not None else None
        if parent is not None:
            parent.replies.append(node)
        else:
            roots.append(node)
    return roots


def add_comment(
    db: Session, *, race_id: int, user_id: int, body: str, parent_id: int | None
) -> Comment:
    """Insert a comment. If it's a reply, the parent must exist in the same
    race — this is what keeps every thread a single well-formed tree."""
    if parent_id is not None:
        parent = (
            db.query(Comment.id)
            .filter(Comment.id == parent_id, Comment.race_id == race_id)
            .first()
        )
        if parent is None:
            raise CommentError("Parent comment not found in this race.")

    comment = Comment(race_id=race_id, user_id=user_id, body=body, parent_id=parent_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, *, comment_id: int, user_id: int) -> None:
    """Tombstone a comment (soft delete). We never hard-delete a node that may
    have replies — that would orphan the subtree — so we hide the content and
    keep the row, and the children live on. Only the author may delete."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment is None:
        raise CommentError("Comment not found.")
    if comment.user_id != user_id:
        raise CommentError("You can only delete your own comments.")
    comment.is_deleted = True
    db.commit()


def subtree_ids(db: Session, root_id: int) -> list[int]:
    """Every comment id in the subtree rooted at ``root_id`` (inclusive),
    via a Postgres recursive CTE — the tree walked inside the database.

    This is the SQL counterpart to a DFS/BFS: the anchor selects the root, the
    recursive term repeatedly joins children onto the frontier until it's empty.
    Useful for a permalink view (a comment + all its descendants) without
    pulling the whole race thread.
    """
    sql = text(
        """
        WITH RECURSIVE descendants AS (
            SELECT id FROM comments WHERE id = :root
            UNION ALL
            SELECT c.id
            FROM comments c
            JOIN descendants d ON c.parent_id = d.id
        )
        SELECT id FROM descendants
        """
    )
    return [row[0] for row in db.execute(sql, {"root": root_id})]
