from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.user import User, UserSession
from app.repositories.user_repository import UserRepository


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


@dataclass(frozen=True)
class CreatedSession:
    user: User
    token: str


class AuthenticationService:
    def __init__(
        self,
        repository: UserRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository or UserRepository()
        self.settings = settings or get_settings()
        self.password_hasher = PasswordHasher()

    def register(self, session: Session, email: str, password: str) -> User:
        user = User(
            email=self._normalize_email(email), password_hash=self.password_hasher.hash(password)
        )
        self.repository.add_user(session, user)

        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise EmailAlreadyRegisteredError from error

        return user

    def authenticate(self, session: Session, email: str, password: str) -> User:
        user = self.repository.get_by_email(session, self._normalize_email(email))
        if user is None:
            raise InvalidCredentialsError

        try:
            valid_password = self.password_hasher.verify(user.password_hash, password)
        except VerifyMismatchError as error:
            raise InvalidCredentialsError from error

        if not valid_password:
            raise InvalidCredentialsError

        return user

    def create_session(self, session: Session, user: User) -> CreatedSession:
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        user_session = UserSession(
            user_id=user.id,
            token_hash=self._token_hash(token),
            expires_at=now + timedelta(days=self.settings.session_lifetime_days),
        )
        self.repository.add_session(session, user_session)
        session.commit()
        return CreatedSession(user=user, token=token)

    def get_user_for_token(self, session: Session, token: str) -> User | None:
        active_session = self.repository.get_active_session(
            session, self._token_hash(token), datetime.now(UTC)
        )
        if active_session is None:
            return None
        return self.repository.get_user_by_id(session, active_session.user_id)

    def revoke_session(self, session: Session, token: str) -> None:
        active_session = self.repository.get_active_session(
            session, self._token_hash(token), datetime.now(UTC)
        )
        if active_session is not None:
            active_session.revoked_at = datetime.now(UTC)
            session.commit()

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    def _token_hash(self, token: str) -> str:
        return hmac.new(
            self.settings.session_token_pepper.encode(), token.encode(), hashlib.sha256
        ).hexdigest()
