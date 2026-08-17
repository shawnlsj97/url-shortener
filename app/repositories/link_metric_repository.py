from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.link_metric import LinkMetric


class LinkMetricRepository:
    def increment(self, session: Session, link_id: UUID, clicked_at: datetime) -> None:
        dialect_name = session.bind.dialect.name if session.bind is not None else ""
        insert = postgres_insert if dialect_name == "postgresql" else sqlite_insert
        statement = insert(LinkMetric).values(
            link_id=link_id,
            total_clicks=1,
            last_clicked_at=clicked_at,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[LinkMetric.link_id],
            set_={
                "total_clicks": LinkMetric.total_clicks + 1,
                "last_clicked_at": clicked_at,
            },
        )
        session.execute(statement)

    def get_totals(self, session: Session, link_ids: list[UUID]) -> dict[UUID, int]:
        if not link_ids:
            return {}
        statement = select(LinkMetric.link_id, LinkMetric.total_clicks).where(
            LinkMetric.link_id.in_(link_ids)
        )
        return {
            link_id: total_clicks
            for link_id, total_clicks in session.execute(statement).tuples().all()
        }
