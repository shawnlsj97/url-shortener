"""add link metrics

Revision ID: 20260814_05
Revises: 20260814_04
Create Date: 2026-08-14 00:40:00
"""

import sqlalchemy as sa

from alembic import op

revision = "20260814_05"
down_revision = "20260814_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "link_metrics",
        sa.Column("link_id", sa.Uuid(), nullable=False),
        sa.Column("total_clicks", sa.BigInteger(), nullable=False),
        sa.Column("last_clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["link_id"], ["links.id"]),
        sa.PrimaryKeyConstraint("link_id"),
    )


def downgrade() -> None:
    op.drop_table("link_metrics")
