"""Comment model — the tree, encoded as an adjacency list.

Each comment has exactly one parent (the comment it replies to), so the set of
comments on a race is a tree (a forest of root comments). We store that as an
adjacency list: a nullable self-referential ``parent_id`` foreign key. NULL =
a top-level comment (a root); non-NULL = a reply. This is the standard,
write-cheap representation; the whole tree is rebuilt in O(n) at read time
(see ``service.build_thread``) and a single subtree can be fetched with a
Postgres recursive CTE (``service.subtree_ids``).
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.sports.f1.models import SCHEMA as F1_SCHEMA


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)

    # What the thread is attached to.
    race_id = Column(
        Integer, ForeignKey(f"{F1_SCHEMA}.races.id"), nullable=False, index=True
    )

    # THE TREE EDGE. NULL → top-level root; otherwise the comment this replies
    # to. Indexed because the O(n) reconstruction and the recursive CTE both
    # look children up by parent.
    parent_id = Column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    body = Column(String, nullable=False)

    # Soft delete: a node with replies can't be removed without orphaning its
    # subtree, so "delete" tombstones the row (body/author hidden) and the
    # replies live on — exactly how Reddit/HN handle it.
    is_deleted = Column(Boolean, nullable=False, server_default="false", default=False)

    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    author = relationship("User", lazy="joined")
