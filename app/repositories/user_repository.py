from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserSession


class UserRepository:
    def get_by_email(self, session: Session, email: str) -> User | None:
        return session.scalar(select(User).where(User.email == email))

    def add_user(self, session: Session, user: User) -> None:
        session.add(user)

    def add_session(self, session: Session, user_session: UserSession) -> None:
        session.add(user_session)

    def get_active_session(
        self, session: Session, token_hash: str, now: datetime
    ) -> UserSession | None:
        statement = select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        return session.scalar(statement)

    def get_user_by_id(self, session: Session, user_id: UUID) -> User | None:
        return session.get(User, user_id)
