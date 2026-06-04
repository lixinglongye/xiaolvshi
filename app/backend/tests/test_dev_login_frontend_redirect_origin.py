from starlette.requests import Request

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
