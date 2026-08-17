from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth_dependencies import get_optional_current_user
from app.api.auth_routes import router as auth_router
from app.api.routes import router as api_router
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models.user import User
from app.services.link_service import (
    LinkDisabledError,
    LinkExpiredError,
    LinkNotFoundError,
    LinkService,
)
from app.services.metric_service import MetricService

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Relay URL Shortener", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(api_router)
app.include_router(auth_router)
DbSession = Annotated[Session, Depends(get_db_session)]


@app.middleware("http")
async def add_security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    if request.url.path not in {"/docs", "/redoc"}:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path in {"/dashboard", "/login", "/register"}:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": current_user},
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={"mode": "login", "page_title": "Welcome back", "submit_label": "Log in"},
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={
            "mode": "register",
            "page_title": "Create your account",
            "submit_label": "Create account",
        },
    )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    session: DbSession,
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)
    links = LinkService().list_for_owner(session, current_user.id)
    click_totals = MetricService().get_totals(session, links)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": current_user,
            "links": links,
            "click_totals": click_totals,
            "public_base_url": get_settings().public_base_url.rstrip("/"),
        },
    )


@app.get("/healthz")
def healthcheck(session: DbSession) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/not-found", response_class=HTMLResponse, include_in_schema=False)
def not_found(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="not_found.html", status_code=404)


@app.get("/expired", response_class=HTMLResponse, include_in_schema=False)
def expired(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="expired.html", status_code=410)


@app.get("/{code}", name="resolve_link", include_in_schema=False)
def resolve_link(code: str, request: Request, session: DbSession) -> Response:
    try:
        link = LinkService().resolve(session, code)
    except LinkNotFoundError:
        return templates.TemplateResponse(request=request, name="not_found.html", status_code=404)
    except LinkDisabledError:
        return templates.TemplateResponse(request=request, name="not_found.html", status_code=404)
    except LinkExpiredError:
        return templates.TemplateResponse(request=request, name="expired.html", status_code=410)

    MetricService().record_redirect(session, link.id)
    return RedirectResponse(url=link.original_url, status_code=302)
