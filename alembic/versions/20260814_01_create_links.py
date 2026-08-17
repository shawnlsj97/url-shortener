"""create links table

Revision ID: 20260814_01
Revises:
Create Date: 2026-08-14 00:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "20260814_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_links_code"),
    )


def downgrade() -> None:
    op.drop_table("links")
