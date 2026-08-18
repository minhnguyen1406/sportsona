"""Add comments table (adjacency-list comment tree).

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["race_id"], ["f1.races.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comments_race_id"), "comments", ["race_id"])
    op.create_index(op.f("ix_comments_parent_id"), "comments", ["parent_id"])
    op.create_index(op.f("ix_comments_user_id"), "comments", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_comments_user_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_parent_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_race_id"), table_name="comments")
    op.drop_table("comments")
