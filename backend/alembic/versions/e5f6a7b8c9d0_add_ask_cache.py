"""Add ask_cache table for /ask answer caching.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ask_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_normalized", sa.String(), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("sql", sa.String(), nullable=False),
        sa.Column("reasoning", sa.String(), nullable=False),
        sa.Column("columns", JSONB(), nullable=False),
        sa.Column("rows", JSONB(), nullable=False),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ask_cache_question_normalized"),
        "ask_cache",
        ["question_normalized"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ask_cache_question_normalized"), table_name="ask_cache")
    op.drop_table("ask_cache")
