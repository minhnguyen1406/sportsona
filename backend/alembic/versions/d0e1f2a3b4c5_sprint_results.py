"""Sprint results table + races.format

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-09-13
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("races", sa.Column("format", sa.String(), nullable=True), schema="f1")
    op.create_table(
        "sprint_results",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("race_id", sa.Integer(), sa.ForeignKey("f1.races.id"), nullable=False),
        sa.Column("driver_id", sa.String(), sa.ForeignKey("f1.drivers.driver_id"), nullable=False),
        sa.Column("constructor_id", sa.String(), sa.ForeignKey("f1.constructors.constructor_id"), nullable=False),
        sa.Column("grid_position", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("position_text", sa.String(), nullable=True),
        sa.Column("points", sa.Float(), nullable=True),
        sa.Column("laps", sa.Integer(), nullable=True),
        sa.Column("time", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.UniqueConstraint("race_id", "driver_id", name="uq_sprint_result"),
        schema="f1",
    )
    op.create_index("ix_sprint_results_race_id", "sprint_results", ["race_id"], schema="f1")


def downgrade() -> None:
    op.drop_index("ix_sprint_results_race_id", table_name="sprint_results", schema="f1")
    op.drop_table("sprint_results", schema="f1")
    op.drop_column("races", "format", schema="f1")
