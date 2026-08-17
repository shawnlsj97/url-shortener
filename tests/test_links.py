from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.link import Link


def test_create_then_resolve_link(client: TestClient) -> None:
    create_response = client.post(
        "/api/links",
        json={"original_url": "https://open.gov.sg/"},
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert len(payload["code"]) == 8
    assert payload["short_url"] == f"http://localhost:8000/{payload['code']}"

    resolve_response = client.get(f"/{payload['code']}", follow_redirects=False)
    assert resolve_response.status_code == 302
    assert resolve_response.headers["location"] == "https://open.gov.sg/"


def test_rejects_non_http_url(client: TestClient) -> None:
    response = client.post("/api/links", json={"original_url": "file:///etc/passwd"})

    assert response.status_code == 422


def test_creates_and_resolves_custom_alias(client: TestClient) -> None:
    response = client.post(
        "/api/links",
        json={"original_url": "https://open.gov.sg/", "custom_alias": "open-gov"},
    )

    assert response.status_code == 201
    assert response.json()["code"] == "open-gov"

    resolve_response = client.get("/open-gov", follow_redirects=False)
    assert resolve_response.headers["location"] == "https://open.gov.sg/"


def test_rejects_custom_alias_conflicts(client: TestClient) -> None:
    payload = {"original_url": "https://open.gov.sg/", "custom_alias": "open-gov"}
    assert client.post("/api/links", json=payload).status_code == 201

    response = client.post("/api/links", json=payload)
    assert response.status_code == 409


def test_rejects_reserved_custom_alias(client: TestClient) -> None:
    response = client.post(
        "/api/links",
        json={"original_url": "https://open.gov.sg/", "custom_alias": "dashboard"},
    )

    assert response.status_code == 422


def test_rejects_past_expiry(client: TestClient) -> None:
    response = client.post(
        "/api/links",
        json={
            "original_url": "https://open.gov.sg/",
            "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
    )

    assert response.status_code == 422


def test_expired_link_returns_gone_page(client: TestClient, test_engine: Engine) -> None:
    with Session(test_engine) as session:
        session.add(
            Link(
                code="expired-link",
                original_url="https://open.gov.sg/",
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
            )
        )
        session.commit()

    response = client.get("/expired-link", follow_redirects=False)

    assert response.status_code == 410
    assert "This short link has expired." in response.text


def test_unknown_code_returns_not_found_page(client: TestClient) -> None:
    response = client.get("/does-not-exist", follow_redirects=False)

    assert response.status_code == 404
    assert "This short link does not exist." in response.text


def test_healthcheck(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_created_link_uses_configured_public_base_url(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://short.example/")
    get_settings.cache_clear()

    response = client.post("/api/links", json={"original_url": "https://open.gov.sg/"})

    assert response.status_code == 201
    assert response.json()["short_url"].startswith("https://short.example/")
