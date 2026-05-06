"""Add revoked_refresh_tokens and one_time_tokens

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revoked_refresh_tokens",
        sa.Column("jti", sa.String(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("jti"),
    )
    op.create_index(
        op.f("ix_revoked_refresh_tokens_expires_at"),
        "revoked_refresh_tokens",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "one_time_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_one_time_tokens_id"), "one_time_tokens", ["id"], unique=False)
    op.create_index(
        op.f("ix_one_time_tokens_token_hash"),
        "one_time_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_one_time_tokens_user_id"), "one_time_tokens", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_one_time_tokens_purpose"), "one_time_tokens", ["purpose"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_one_time_tokens_purpose"), table_name="one_time_tokens")
    op.drop_index(op.f("ix_one_time_tokens_user_id"), table_name="one_time_tokens")
    op.drop_index(op.f("ix_one_time_tokens_token_hash"), table_name="one_time_tokens")
    op.drop_index(op.f("ix_one_time_tokens_id"), table_name="one_time_tokens")
    op.drop_table("one_time_tokens")
    op.drop_index(
        op.f("ix_revoked_refresh_tokens_expires_at"), table_name="revoked_refresh_tokens"
    )
    op.drop_table("revoked_refresh_tokens")
