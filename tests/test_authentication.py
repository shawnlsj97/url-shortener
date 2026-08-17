from fastapi.testclient import TestClient

VALID_PASSWORD = "a secure password 123"


def register(client: TestClient, email: str = "person@example.com") -> None:
    response = client.post("/api/auth/register", json={"email": email, "password": VALID_PASSWORD})
    assert response.status_code == 201


def csrf_headers(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies["ogp_csrf"]}


def test_register_sets_an_opaque_session_cookie(client: TestClient) -> None:
    register(client)

    assert client.cookies.get("ogp_session")


def test_cannot_register_same_email_twice(client: TestClient) -> None:
    register(client)
    response = client.post(
        "/api/auth/register", json={"email": "PERSON@example.com", "password": VALID_PASSWORD}
    )

    assert response.status_code == 409


def test_login_and_logout(client: TestClient) -> None:
    register(client)
    logout_response = client.post("/api/auth/logout", headers=csrf_headers(client))
    assert logout_response.status_code == 204

    login_response = client.post(
        "/api/auth/login", json={"email": "person@example.com", "password": VALID_PASSWORD}
    )
    assert login_response.status_code == 200
    assert login_response.json() == {"email": "person@example.com"}


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    register(client)

    response = client.post(
        "/api/auth/login", json={"email": "person@example.com", "password": "wrong password"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_authenticated_link_is_owned(client: TestClient) -> None:
    register(client)
    response = client.post(
        "/api/links", json={"original_url": "https://open.gov.sg/"}, headers=csrf_headers(client)
    )

    assert response.status_code == 201


def test_dashboard_requires_login(client: TestClient) -> None:
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_dashboard_lists_only_current_users_links(client: TestClient) -> None:
    register(client, "first@example.com")
    first_link = client.post(
        "/api/links",
        json={"original_url": "https://open.gov.sg/", "custom_alias": "first-link"},
        headers=csrf_headers(client),
    )
    assert first_link.status_code == 201

    client.cookies.clear()
    register(client, "second@example.com")
    second_link = client.post(
        "/api/links",
        json={"original_url": "https://example.com/", "custom_alias": "second-link"},
        headers=csrf_headers(client),
    )
    assert second_link.status_code == 201

    links_response = client.get("/api/links")
    assert links_response.status_code == 200
    assert [link["code"] for link in links_response.json()] == ["second-link"]


def test_owner_can_disable_link(client: TestClient) -> None:
    register(client)
    created = client.post(
        "/api/links",
        json={"original_url": "https://open.gov.sg/", "custom_alias": "to-disable"},
        headers=csrf_headers(client),
    )
    assert created.status_code == 201

    disabled = client.delete("/api/links/to-disable", headers=csrf_headers(client))
    assert disabled.status_code == 204

    resolve_response = client.get("/to-disable", follow_redirects=False)
    assert resolve_response.status_code == 404


def test_other_user_cannot_disable_an_owned_link(client: TestClient) -> None:
    register(client, "owner@example.com")
    created = client.post(
        "/api/links",
        json={"original_url": "https://open.gov.sg/", "custom_alias": "owners-link"},
        headers=csrf_headers(client),
    )
    assert created.status_code == 201

    client.cookies.clear()
    register(client, "other@example.com")

    response = client.delete("/api/links/owners-link", headers=csrf_headers(client))

    assert response.status_code == 404
    assert client.get("/owners-link", follow_redirects=False).status_code == 302


def test_owner_can_see_click_totals(client: TestClient) -> None:
    register(client)
    created = client.post(
        "/api/links",
        json={"original_url": "https://open.gov.sg/", "custom_alias": "metrics-link"},
        headers=csrf_headers(client),
    )
    assert created.status_code == 201

    assert client.get("/metrics-link", follow_redirects=False).status_code == 302
    assert client.get("/metrics-link", follow_redirects=False).status_code == 302

    links_response = client.get("/api/links")
    assert links_response.status_code == 200
    assert links_response.json()[0]["total_clicks"] == 2


def test_authenticated_state_change_requires_csrf_token(client: TestClient) -> None:
    register(client)

    response = client.post("/api/links", json={"original_url": "https://open.gov.sg/"})

    assert response.status_code == 403
