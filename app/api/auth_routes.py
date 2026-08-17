from __future__ import annotations

import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.auth_dependencies import DbSession, verify_csrf
from app.api.auth_schemas import AuthenticatedUserResponse, CredentialsRequest
from app.core.config import get_settings
from app.services.authentication_service import (
    AuthenticationService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/api/auth")


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.app_environment == "production",
        samesite="lax",
        max_age=int(timedelta(days=settings.session_lifetime_days).total_seconds()),
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=secrets.token_urlsafe(32),
        httponly=False,
        secure=settings.app_environment == "production",
        samesite="lax",
        max_age=int(timedelta(days=settings.session_lifetime_days).total_seconds()),
        path="/",
    )


@router.post(
    "/register", response_model=AuthenticatedUserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    payload: CredentialsRequest, response: Response, session: DbSession
) -> AuthenticatedUserResponse:
    service = AuthenticationService()
    try:
        user = service.register(session, str(payload.email), payload.password)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered."
        ) from error

    created_session = service.create_session(session, user)
    set_session_cookie(response, created_session.token)
    return AuthenticatedUserResponse(email=user.email)


@router.post("/login", response_model=AuthenticatedUserResponse)
def login(
    payload: CredentialsRequest, response: Response, session: DbSession
) -> AuthenticatedUserResponse:
    service = AuthenticationService()
    try:
        user = service.authenticate(session, str(payload.email), payload.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
        ) from error

    created_session = service.create_session(session, user)
    set_session_cookie(response, created_session.token)
    return AuthenticatedUserResponse(email=user.email)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_csrf)])
def logout(request: Request, response: Response, session: DbSession) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token is not None:
        AuthenticationService().revoke_session(session, token)
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
