from fastapi.testclient import TestClient


def test_public_page_has_a_mobile_viewport(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Relay<span>·</span>" in response.text
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in response.text
    assert 'href="/login"' in response.text
    assert 'href="/register"' in response.text
    assert 'class="account-actions site-nav"' in response.text
    assert "3–32 lowercase letters or numbers; hyphens allowed between them." in response.text
    assert 'aria-describedby="custom-alias-hint"' in response.text
    assert "Must be a future date and time." in response.text
    assert 'aria-describedby="expires-at-hint"' in response.text
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_styles_include_small_screen_layouts_and_touch_targets(client: TestClient) -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "@media (max-width: 600px)" in response.text
    assert "min-height: 44px" in response.text
    assert ".site-nav { gap: .45rem; }" in response.text
    assert ".nav-link, .nav-cta { display: inline-flex; min-height: 40px;" in response.text
    assert ".dashboard-intro { align-items: flex-start; flex-direction: column;" in response.text


def test_authentication_script_formats_validation_errors(client: TestClient) -> None:
    response = client.get("/static/auth.js")

    assert response.status_code == 200
    assert "function errorMessageFor(body, fallback)" in response.text
