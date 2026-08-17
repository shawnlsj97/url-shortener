from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.link import Link


class LinkRepository:
    def get_by_code(self, session: Session, code: str) -> Link | None:
        return session.scalar(select(Link).where(Link.code == code))

    def add(self, session: Session, link: Link) -> None:
        session.add(link)

    def get_by_code_for_owner(self, session: Session, code: str, owner_id: UUID) -> Link | None:
        statement = select(Link).where(Link.code == code, Link.owner_id == owner_id)
        return session.scalar(statement)

    def list_for_owner(self, session: Session, owner_id: UUID) -> list[Link]:
        statement = select(Link).where(Link.owner_id == owner_id).order_by(Link.created_at.desc())
        return list(session.scalars(statement))
