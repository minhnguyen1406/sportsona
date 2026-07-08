"""Add stats_of_day table for the daily AI-generated stat.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stats_of_day",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("sql", sa.String(), nullable=False),
        sa.Column("columns", JSONB(), nullable=False),
        sa.Column("rows", JSONB(), nullable=False),
        sa.Column("narration", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("date"),
    )


def downgrade() -> None:
    op.drop_table("stats_of_day")
