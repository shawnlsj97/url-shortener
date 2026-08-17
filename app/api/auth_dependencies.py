from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.user import User
from app.services.authentication_service import AuthenticationService

DbSession = Annotated[Session, Depends(get_db_session)]


def get_optional_current_user(request: Request, session: DbSession) -> User | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if token is None:
        return None
    return AuthenticationService().get_user_for_token(session, token)


def get_current_user(user: Annotated[User | None, Depends(get_optional_current_user)]) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user


def verify_csrf(request: Request) -> None:
    settings = get_settings()
    if request.cookies.get(settings.session_cookie_name) is None:
        return

    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    header_token = request.headers.get("X-CSRF-Token")
    is_valid = (
        cookie_token is not None
        and header_token is not None
        and hmac.compare_digest(cookie_token, header_token)
    )
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token.")
