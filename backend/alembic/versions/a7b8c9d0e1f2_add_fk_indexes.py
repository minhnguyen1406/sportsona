"""Add B-tree indexes on FK columns used by entity-centric lookups.

Postgres does NOT auto-index FK columns. The composite unique
(race_id, driver_id) only accelerates race_id-prefixed lookups; queries
that filter by driver alone ("all of Hamilton's results", dashboard
recent-results, /ask career aggregations) were sequential scans.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_INDEXES = [
    ("ix_f1_race_results_driver_id", "race_results", "driver_id"),
    ("ix_f1_race_results_constructor_id", "race_results", "constructor_id"),
    ("ix_f1_qualifying_results_driver_id", "qualifying_results", "driver_id"),
    ("ix_f1_qualifying_results_constructor_id", "qualifying_results", "constructor_id"),
    ("ix_f1_driver_standings_driver_id", "driver_standings", "driver_id"),
    ("ix_f1_constructor_standings_constructor_id", "constructor_standings", "constructor_id"),
]


def upgrade() -> None:
    for name, table, column in _INDEXES:
        op.create_index(name, table, [column], schema="f1")


def downgrade() -> None:
    for name, table, _ in _INDEXES:
        op.drop_index(name, table_name=table, schema="f1")
