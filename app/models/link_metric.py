from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LinkMetric(Base):
    __tablename__ = "link_metrics"

    link_id: Mapped[UUID] = mapped_column(ForeignKey("links.id"), primary_key=True)
    total_clicks: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
