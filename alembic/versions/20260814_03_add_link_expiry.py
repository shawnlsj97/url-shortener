"""add link expiry

Revision ID: 20260814_03
Revises: 20260814_02
Create Date: 2026-08-14 00:20:00
"""

import sqlalchemy as sa

from alembic import op

revision = "20260814_03"
down_revision = "20260814_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("links", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("links", "expires_at")
