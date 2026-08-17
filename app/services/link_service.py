from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.link import Link
from app.repositories.link_repository import LinkRepository

BASE62_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 8
MAX_CODE_ATTEMPTS = 5


class LinkNotFoundError(Exception):
    pass


class LinkCreationError(Exception):
    pass


class CustomAliasTakenError(Exception):
    pass


class LinkExpiredError(Exception):
    pass


class LinkDisabledError(Exception):
    pass


class LinkService:
    def __init__(self, repository: LinkRepository | None = None) -> None:
        self.repository = repository or LinkRepository()

    def create(
        self,
        session: Session,
        original_url: str,
        owner_id: UUID | None = None,
        custom_alias: str | None = None,
        expires_at: datetime | None = None,
    ) -> Link:
        for _ in range(MAX_CODE_ATTEMPTS):
            link = Link(
                code=custom_alias or self._generate_code(),
                original_url=original_url,
                owner_id=owner_id,
                expires_at=expires_at,
            )
            self.repository.add(session, link)

            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                if custom_alias is not None:
                    raise CustomAliasTakenError(custom_alias) from None
                continue

            return link

        raise LinkCreationError("Could not allocate a unique short code.")

    def resolve(self, session: Session, code: str) -> Link:
        link = self.repository.get_by_code(session, code)
        if link is None:
            raise LinkNotFoundError(code)
        if link.disabled_at is not None:
            raise LinkDisabledError(code)
        if self._is_expired(link):
            raise LinkExpiredError(code)
        return link

    def list_for_owner(self, session: Session, owner_id: UUID) -> list[Link]:
        return self.repository.list_for_owner(session, owner_id)

    def disable(self, session: Session, code: str, owner_id: UUID) -> None:
        link = self.repository.get_by_code_for_owner(session, code, owner_id)
        if link is None:
            raise LinkNotFoundError(code)
        if link.disabled_at is None:
            link.disabled_at = datetime.now(UTC)
            session.commit()

    @staticmethod
    def _generate_code() -> str:
        return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(CODE_LENGTH))

    @staticmethod
    def _is_expired(link: Link) -> bool:
        if link.expires_at is None:
            return False
        expires_at = link.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at <= datetime.now(UTC)
