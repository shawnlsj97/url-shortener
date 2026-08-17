"""add disabled link state

Revision ID: 20260814_04
Revises: 20260814_03
Create Date: 2026-08-14 00:30:00
"""

import sqlalchemy as sa

from alembic import op

revision = "20260814_04"
down_revision = "20260814_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("links", sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("links", "disabled_at")
