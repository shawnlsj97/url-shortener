from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.link import Link
from app.repositories.link_metric_repository import LinkMetricRepository


class MetricService:
    def __init__(self, repository: LinkMetricRepository | None = None) -> None:
        self.repository = repository or LinkMetricRepository()

    def record_redirect(self, session: Session, link_id: UUID) -> None:
        self.repository.increment(session, link_id, datetime.now(UTC))
        session.commit()

    def get_totals(self, session: Session, links: list[Link]) -> dict[UUID, int]:
        return self.repository.get_totals(session, [link.id for link in links])
