"""Add race_recaps table for cached personalized recaps.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "race_recaps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["race_id"], ["f1.races.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("race_id", "user_id", "prompt_version", name="uq_race_recap"),
    )
    op.create_index(op.f("ix_race_recaps_race_id"), "race_recaps", ["race_id"])
    op.create_index(op.f("ix_race_recaps_user_id"), "race_recaps", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_race_recaps_user_id"), table_name="race_recaps")
    op.drop_index(op.f("ix_race_recaps_race_id"), table_name="race_recaps")
    op.drop_table("race_recaps")
