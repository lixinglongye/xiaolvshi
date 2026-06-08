from starlette.requests import Request

from routers import auth as auth_router
from routers.auth import get_dev_login_frontend_url


def _request(headers: dict[str, str] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/auth/dev-login",
            "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
        }
    )


def test_dev_login_prefers_explicit_local_frontend_origin():
    request = _request({"host": "localhost:8000"})

    assert (
        get_dev_login_frontend_url(request, frontend_origin="http://127.0.0.1:3000")
        == "http://127.0.0.1:3000"
    )


def test_dev_login_uses_origin_header_when_frontend_origin_missing():
    request = _request({"host": "localhost:8000", "origin": "http://127.0.0.1:3000"})

    assert get_dev_login_frontend_url(request) == "http://127.0.0.1:3000"


def test_dev_login_rejects_non_local_redirect_origin():
    request = _request({"host": "localhost:8000", "origin": "https://attacker.example"})

    assert get_dev_login_frontend_url(request, frontend_origin="https://attacker.example") == "http://localhost:3000"


def test_local_login_falls_back_to_dev_login_when_oidc_missing(monkeypatch):
    monkeypatch.setattr(auth_router.settings, "oidc_client_id", None)
    monkeypatch.setattr(auth_router.settings, "oidc_client_secret", None)
    monkeypatch.setattr(auth_router.settings, "oidc_issuer_url", None)
    request = _request({"host": "127.0.0.1:8000", "origin": "http://127.0.0.1:3000"})

    redirect_url = auth_router.get_local_dev_login_redirect_url(request)

    assert auth_router.should_use_local_dev_login(request) is True
    assert redirect_url.startswith("/api/v1/auth/dev-login?")
    assert "frontend_origin=http%3A%2F%2F127.0.0.1%3A3000" in redirect_url
    assert "None/authorize" not in redirect_url


def test_local_login_keeps_oidc_when_configured(monkeypatch):
    monkeypatch.setattr(auth_router.settings, "oidc_client_id", "client-id")
    monkeypatch.setattr(auth_router.settings, "oidc_client_secret", "client-secret")
    monkeypatch.setattr(auth_router.settings, "oidc_issuer_url", "https://issuer.example")
    request = _request({"host": "127.0.0.1:8000", "origin": "http://127.0.0.1:3000"})

    assert auth_router.should_use_local_dev_login(request) is False
