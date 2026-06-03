from datetime import datetime, timedelta
import json
from types import ModuleType, SimpleNamespace
import sys
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

try:
    import httpx  # noqa: F401
except ModuleNotFoundError:
    httpx_stub = ModuleType("httpx")

    class _HTTPXStubError(Exception):
        pass

    class _AsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    httpx_stub.AsyncClient = _AsyncClient
    httpx_stub.HTTPError = _HTTPXStubError
    httpx_stub.HTTPStatusError = _HTTPXStubError
    httpx_stub.TimeoutException = _HTTPXStubError
    sys.modules["httpx"] = httpx_stub

from core.database import Base, get_db
from dependencies.auth import get_current_user
from models.billing_quota_idempotency_keys import BillingQuotaIdempotencyKey
from models.billing_quota_usage_counters import BillingQuotaUsageCounter
from models.subscriptions import Subscriptions
from schemas.auth import UserResponse
from services.billing_entitlement_quota_binding import build_quota_subject_hash


CURRENT_USER_ID = "raw-user-id-123"
CURRENT_USER_EMAIL = "billing-user@example.test"
QUOTA_WINDOW = "2026-06"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Subscriptions.__table__,
        BillingQuotaUsageCounter.__table__,
        BillingQuotaIdempotencyKey.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def app(db_session):
    fastapi = pytest.importorskip("fastapi")
    from routers.billing_usage import router

    test_app = fastapi.FastAPI()
    test_app.include_router(router)

    async def override_get_current_user():
        return UserResponse(
            id=CURRENT_USER_ID,
            email=CURRENT_USER_EMAIL,
            name="Billing User",
            role="user",
        )

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[get_db] = override_get_db

    yield test_app

    test_app.dependency_overrides.clear()


async def _request(app, method: str, path: str, *, params=None, json_body=None):
    body = b""
    headers = [(b"host", b"testserver")]
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        headers.extend(
            [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ]
        )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": urlencode(params or {}).encode("ascii"),
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "root_path": "",
    }
    received = False
    sent = []

    async def receive():
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    status = next(message["status"] for message in sent if message["type"] == "http.response.start")
    response_body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    return SimpleNamespace(
        status_code=status,
        content=response_body,
        json=lambda: json.loads(response_body.decode("utf-8")),
    )


async def _subscription(
    db_session,
    *,
    user_id: str = CURRENT_USER_ID,
    plan_type: str = "personal",
    limit: int | None = None,
    status: str = "active",
):
    now = datetime(2026, 6, 4)
    subscription = Subscriptions(
        user_id=user_id,
        plan_type=plan_type,
        status=status,
        report_quota_monthly=limit,
        reports_used_month=99,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


def _assert_raw_identity_not_exposed(payload):
    rendered = str(payload)
    assert CURRENT_USER_ID not in rendered
    assert CURRENT_USER_EMAIL not in rendered
    assert "user_id" not in rendered
    assert "email" not in rendered


@pytest.mark.asyncio
async def test_get_me_returns_quota_summary_with_default_opaque_subject_hash(app, db_session):
    await _subscription(db_session)

    response = await _request(app, "GET", "/api/v1/billing-usage/me")

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    assert payload["success"] is True
    assert data["quota_subject_hash"] == build_quota_subject_hash(CURRENT_USER_ID)
    assert data["plan_type"] == "personal"
    assert data["limit"] == 20
    assert data["persisted_usage"] == 0
    assert data["remaining"] == 20
    assert data["can_create_report"] is True
    _assert_raw_identity_not_exposed(payload)


@pytest.mark.asyncio
async def test_get_me_accepts_explicit_quota_subject_hash(app, db_session):
    quota_subject_hash = "qsh_abcdefghijklmnop"
    await _subscription(db_session, plan_type="free")

    response = await _request(
        app,
        "GET",
        "/api/v1/billing-usage/me",
        params={"quota_subject_hash": quota_subject_hash},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["quota_subject_hash"] == quota_subject_hash
    assert payload["data"]["limit"] == 2
    _assert_raw_identity_not_exposed(payload)


@pytest.mark.asyncio
async def test_consume_report_idempotent_replay_does_not_double_count(app, db_session):
    await _subscription(db_session)
    request_body = {
        "source": "report_generation",
        "event_id": "stable-router-event",
        "units": 1,
        "quota_window": QUOTA_WINDOW,
    }

    first = await _request(app, "POST", "/api/v1/billing-usage/consume-report", json_body=request_body)
    replay = await _request(app, "POST", "/api/v1/billing-usage/consume-report", json_body=request_body)

    usage_count = await db_session.scalar(select(func.count(BillingQuotaUsageCounter.id)))
    ledger = await db_session.scalar(select(BillingQuotaIdempotencyKey))
    first_payload = first.json()
    replay_payload = replay.json()

    assert first.status_code == 200
    assert replay.status_code == 200
    assert first_payload["data"]["persisted_usage"] == 1
    assert first_payload["data"]["last_usage_event"]["recorded"] is True
    assert replay_payload["data"]["persisted_usage"] == 1
    assert replay_payload["data"]["remaining"] == 19
    assert replay_payload["data"]["last_usage_event"]["recorded"] is False
    assert replay_payload["data"]["last_usage_event"]["idempotent_replay"] is True
    assert usage_count == 1
    assert ledger.seen_count == 2
    _assert_raw_identity_not_exposed(replay_payload)


@pytest.mark.asyncio
async def test_invalid_quota_subject_hash_returns_400(app, db_session):
    await _subscription(db_session)

    get_response = await _request(
        app,
        "GET",
        "/api/v1/billing-usage/me",
        params={"quota_subject_hash": "raw-user-id-123"},
    )
    post_response = await _request(
        app,
        "POST",
        "/api/v1/billing-usage/consume-report",
        json_body={
            "source": "report_generation",
            "event_id": "invalid-subject-event",
            "units": 1,
            "quota_window": QUOTA_WINDOW,
            "quota_subject_hash": "raw-user-id-123",
        },
    )

    assert get_response.status_code == 400
    assert post_response.status_code == 400
    assert get_response.json()["detail"] == "billing_entitlement_quota_subject_hash_required"
    assert post_response.json()["detail"] == "billing_entitlement_quota_subject_hash_required"
