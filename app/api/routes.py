from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_current_user, get_optional_current_user, verify_csrf
from app.api.schemas import CreateLinkRequest, LinkResponse, ManagedLinkResponse
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.link import Link
from app.models.user import User
from app.services.link_service import (
    CustomAliasTakenError,
    LinkCreationError,
    LinkNotFoundError,
    LinkService,
)
from app.services.metric_service import MetricService

router = APIRouter(prefix="/api")
DbSession = Annotated[Session, Depends(get_db_session)]


def build_link_response(link: Link) -> LinkResponse:
    public_base_url = get_settings().public_base_url.rstrip("/")
    return LinkResponse(
        code=link.code,
        original_url=link.original_url,
        short_url=f"{public_base_url}/{link.code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


def build_managed_link_response(link: Link, total_clicks: int) -> ManagedLinkResponse:
    created_response = build_link_response(link)
    return ManagedLinkResponse(
        **created_response.model_dump(),
        disabled_at=link.disabled_at,
        total_clicks=total_clicks,
    )


@router.post(
    "/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)],
)
def create_link(
    payload: CreateLinkRequest,
    session: DbSession,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> LinkResponse:
    try:
        link = LinkService().create(
            session,
            str(payload.original_url),
            owner_id=current_user.id if current_user else None,
            custom_alias=payload.custom_alias,
            expires_at=payload.expires_at,
        )
    except CustomAliasTakenError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This custom alias is taken."
        ) from error
    except LinkCreationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to create a short link. Please retry.",
        ) from error

    return build_link_response(link)


@router.get("/links", response_model=list[ManagedLinkResponse])
def list_owned_links(
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ManagedLinkResponse]:
    links = LinkService().list_for_owner(session, current_user.id)
    totals = MetricService().get_totals(session, links)
    return [build_managed_link_response(link, totals.get(link.id, 0)) for link in links]


@router.delete(
    "/links/{code}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(verify_csrf)]
)
def disable_owned_link(
    code: str,
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    try:
        LinkService().disable(session, code, current_user.id)
    except LinkNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found."
        ) from error
