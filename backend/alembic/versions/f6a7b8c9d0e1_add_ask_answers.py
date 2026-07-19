"""Add ask_answers table for shareable answer snapshots.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ask_answers",
        sa.Column("slug", sa.String(length=24), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("sql", sa.String(), nullable=False),
        sa.Column("reasoning", sa.String(), nullable=False),
        sa.Column("columns", JSONB(), nullable=False),
        sa.Column("rows", JSONB(), nullable=False),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("slug"),
    )
    op.create_index(op.f("ix_ask_answers_user_id"), "ask_answers", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ask_answers_user_id"), table_name="ask_answers")
    op.drop_table("ask_answers")
