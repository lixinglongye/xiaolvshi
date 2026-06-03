from datetime import datetime, timedelta
import json
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from dependencies.auth import get_current_user
from models.billing_quota_idempotency_keys import BillingQuotaIdempotencyKey
from models.billing_quota_usage_counters import BillingQuotaUsageCounter
from models.generated_documents import Generated_documents
from models.subscriptions import Subscriptions
from schemas.auth import UserResponse
from services.billing_entitlement_quota_binding import build_quota_subject_hash


CURRENT_USER_ID = "generated-doc-user-123"
CURRENT_USER_EMAIL = "generated-doc-user@example.test"
PRIVATE_CONTENT = "PRIVATE_CLIENT_FACT_PATTERN_9c70b2"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Generated_documents.__table__,
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
    from routers.generated_documents import router

    test_app = fastapi.FastAPI()
    test_app.include_router(router)

    async def override_get_current_user():
        return UserResponse(
            id=CURRENT_USER_ID,
            email=CURRENT_USER_EMAIL,
            name="Generated Doc User",
            role="user",
        )

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[get_db] = override_get_db

    yield test_app

    test_app.dependency_overrides.clear()


async def _request(app, method: str, path: str, *, params=None, json_body=None, extra_headers=None):
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
    for key, value in extra_headers or []:
        headers.append((key.lower().encode("ascii"), value.encode("utf-8")))
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
    status_code = next(message["status"] for message in sent if message["type"] == "http.response.start")
    response_body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    return SimpleNamespace(
        status_code=status_code,
        content=response_body,
        json=lambda: json.loads(response_body.decode("utf-8")),
    )


async def _subscription(db_session, *, limit: int = 1):
    now = datetime(2026, 6, 4)
    subscription = Subscriptions(
        user_id=CURRENT_USER_ID,
        plan_type="free",
        status="active",
        report_quota_monthly=limit,
        reports_used_month=0,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


def _document_body(*, content: str = PRIVATE_CONTENT):
    return {
        "case_id": 42,
        "doc_type": "civil_complaint",
        "title": "Draft complaint",
        "content": content,
        "input_data_json": json.dumps({"facts": content}),
        "status": "draft",
        "generated_by": "case_workspace",
    }


async def _quota_rows(db_session):
    rows = (
        await db_session.execute(
            select(BillingQuotaUsageCounter).order_by(BillingQuotaUsageCounter.id.asc())
        )
    ).scalars().all()
    ledgers = (
        await db_session.execute(
            select(BillingQuotaIdempotencyKey).order_by(BillingQuotaIdempotencyKey.id.asc())
        )
    ).scalars().all()
    return rows, ledgers


def _assert_quota_storage_is_private(rows, ledgers):
    rendered = " ".join(
        [
            *(row.idempotency_key + row.source_event_hash + row.quota_subject_hash + (row.reason_codes_json or "") for row in rows),
            *(ledger.idempotency_key + ledger.source_event_hash + ledger.quota_subject_hash for ledger in ledgers),
        ]
    )
    assert PRIVATE_CONTENT not in rendered
    assert CURRENT_USER_ID not in rendered
    assert CURRENT_USER_EMAIL not in rendered


@pytest.mark.asyncio
async def test_create_generated_document_consumes_quota_before_insert(app, db_session):
    await _subscription(db_session, limit=1)

    response = await _request(
        app,
        "POST",
        "/api/v1/entities/generated_documents",
        json_body=_document_body(),
        extra_headers=[("Idempotency-Key", "create-generated-doc-001")],
    )

    document_count = await db_session.scalar(select(func.count(Generated_documents.id)))
    rows, ledgers = await _quota_rows(db_session)
    payload = response.json()

    assert response.status_code == 201
    assert payload["content"] == PRIVATE_CONTENT
    assert payload["user_id"] == CURRENT_USER_ID
    assert document_count == 1
    assert len(rows) == 1
    assert len(ledgers) == 1
    assert rows[0].quota_subject_hash == build_quota_subject_hash(CURRENT_USER_ID)
    assert rows[0].decision_status == "ready"
    assert rows[0].used_value == 1
    _assert_quota_storage_is_private(rows, ledgers)


@pytest.mark.asyncio
async def test_create_generated_document_blocks_without_inserting_when_quota_exhausted(app, db_session):
    await _subscription(db_session, limit=1)
    first = await _request(
        app,
        "POST",
        "/api/v1/entities/generated_documents",
        json_body=_document_body(content=f"{PRIVATE_CONTENT}-first"),
    )

    blocked = await _request(
        app,
        "POST",
        "/api/v1/entities/generated_documents",
        json_body=_document_body(content=f"{PRIVATE_CONTENT}-second"),
    )

    document_count = await db_session.scalar(select(func.count(Generated_documents.id)))
    rows, ledgers = await _quota_rows(db_session)
    detail = blocked.json()["detail"]

    assert first.status_code == 201
    assert blocked.status_code == 402
    assert detail["code"] == "report_quota_blocked"
    assert detail["reason_codes"] == ["report_quota_exhausted"]
    assert document_count == 1
    assert len(rows) == 2
    assert len(ledgers) == 2
    assert rows[-1].decision_status == "blocked"
    assert rows[-1].used_value == 1
    _assert_quota_storage_is_private(rows, ledgers)


@pytest.mark.asyncio
async def test_replayed_create_returns_existing_document_without_double_count(app, db_session):
    await _subscription(db_session, limit=1)
    body = _document_body()

    first = await _request(app, "POST", "/api/v1/entities/generated_documents", json_body=body)
    replay = await _request(app, "POST", "/api/v1/entities/generated_documents", json_body=body)

    document_count = await db_session.scalar(select(func.count(Generated_documents.id)))
    rows, ledgers = await _quota_rows(db_session)
    ledger = ledgers[0]

    assert first.status_code == 201
    assert replay.status_code == 200
    assert first.json()["id"] == replay.json()["id"]
    assert document_count == 1
    assert len(rows) == 1
    assert len(ledgers) == 1
    assert ledger.seen_count == 2
    assert rows[0].used_value == 1
    _assert_quota_storage_is_private(rows, ledgers)


@pytest.mark.asyncio
async def test_batch_create_preflights_total_units_before_any_insert(app, db_session):
    await _subscription(db_session, limit=1)

    blocked = await _request(
        app,
        "POST",
        "/api/v1/entities/generated_documents/batch",
        json_body={
            "items": [
                _document_body(content=f"{PRIVATE_CONTENT}-batch-first"),
                _document_body(content=f"{PRIVATE_CONTENT}-batch-second"),
            ]
        },
    )

    document_count = await db_session.scalar(select(func.count(Generated_documents.id)))
    rows, ledgers = await _quota_rows(db_session)
    detail = blocked.json()["detail"]

    assert blocked.status_code == 402
    assert detail["code"] == "report_quota_blocked"
    assert detail["reason_codes"] == ["report_quota_exhausted"]
    assert document_count == 0
    assert rows == []
    assert ledgers == []
