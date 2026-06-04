from datetime import datetime, timedelta
import json
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from dependencies.auth import get_current_user
from models.billing_quota_idempotency_keys import BillingQuotaIdempotencyKey
from models.billing_quota_usage_counters import BillingQuotaUsageCounter
from models.subscriptions import Subscriptions
from schemas.auth import UserResponse
from services.deep_review_document_quota import deep_review_document_quota_event_id


CURRENT_USER_ID = "deep-review-document-quota-user"
CURRENT_USER_EMAIL = "deep-review-document-quota@example.test"
PRIVATE_INPUT = "PRIVATE_DEEP_REVIEW_INPUT_PATTERN_41e0f4"


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
async def app(db_session, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from routers.deep_review import router
    import routers.deep_review as deep_review_router

    class FakeDeepReviewService:
        calls: list[dict] = []

        async def generate_legal_document(self, **kwargs):
            self.calls.append(kwargs)
            return {
                "document_meta": {
                    "doc_type": kwargs["doc_type"],
                    "language": kwargs["language"],
                },
                "content": "Synthetic generated document for quota tests.",
                "key_clauses": [],
                "review_notes": [],
                "legal_references": [],
            }

    FakeDeepReviewService.calls = []
    monkeypatch.setattr(deep_review_router, "DeepReviewService", FakeDeepReviewService)

    test_app = fastapi.FastAPI()
    test_app.include_router(router)

    async def override_get_current_user():
        return UserResponse(
            id=CURRENT_USER_ID,
            email=CURRENT_USER_EMAIL,
            name="Deep Review Quota User",
            role="user",
        )

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_current_user] = override_get_current_user
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.state.fake_service = FakeDeepReviewService

    yield test_app

    test_app.dependency_overrides.clear()


async def _request(app, method: str, path: str, *, json_body=None):
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
        "query_string": b"",
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


async def _subscription(db_session, *, limit: int):
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


def _body(*, title: str = "Draft title", marker: str = PRIVATE_INPUT):
    return {
        "doc_type": "civil_complaint",
        "user_role": "plaintiff",
        "title": title,
        "input_data": {
            "facts": marker,
            "client_email": CURRENT_USER_EMAIL,
            f"field-{marker}": "key should be hashed",
        },
        "language": "zh",
    }


async def _quota_rows(db_session):
    rows = (
        await db_session.execute(select(BillingQuotaUsageCounter).order_by(BillingQuotaUsageCounter.id.asc()))
    ).scalars().all()
    ledgers = (
        await db_session.execute(select(BillingQuotaIdempotencyKey).order_by(BillingQuotaIdempotencyKey.id.asc()))
    ).scalars().all()
    return rows, ledgers


def _render_quota_storage(rows, ledgers):
    return " ".join(
        [
            *(row.idempotency_key + row.source_event_hash + row.quota_subject_hash + (row.reason_codes_json or "") for row in rows),
            *(ledger.idempotency_key + ledger.source_event_hash + ledger.quota_subject_hash for ledger in ledgers),
        ]
    )


@pytest.mark.asyncio
async def test_deep_review_generate_document_consumes_quota_before_ai_call(app, db_session):
    await _subscription(db_session, limit=1)

    response = await _request(
        app,
        "POST",
        "/api/v1/deep-review/generate-document",
        json_body=_body(title=f"Private {PRIVATE_INPUT} title"),
    )

    rows, ledgers = await _quota_rows(db_session)
    payload = response.json()
    rendered_storage = _render_quota_storage(rows, ledgers)
    rendered_response = json.dumps(payload, ensure_ascii=False)

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["quota"]["decision_status"] == "ready"
    assert payload["quota"]["privacy_boundary"] == {
        "raw_document_text_included": False,
        "input_data_included": False,
        "title_included": False,
        "pii_included": False,
    }
    assert len(app.state.fake_service.calls) == 1
    assert len(rows) == 1
    assert len(ledgers) == 1
    assert rows[0].decision_status == "ready"
    assert PRIVATE_INPUT not in rendered_storage
    assert CURRENT_USER_ID not in rendered_storage
    assert CURRENT_USER_EMAIL not in rendered_storage
    assert PRIVATE_INPUT not in rendered_response
    assert CURRENT_USER_EMAIL not in rendered_response


@pytest.mark.asyncio
async def test_deep_review_generate_document_blocks_without_ai_call_when_quota_exhausted(app, db_session):
    await _subscription(db_session, limit=1)

    first = await _request(
        app,
        "POST",
        "/api/v1/deep-review/generate-document",
        json_body=_body(title="First quota event", marker=f"{PRIVATE_INPUT}-first"),
    )
    blocked = await _request(
        app,
        "POST",
        "/api/v1/deep-review/generate-document",
        json_body=_body(title="Second quota event", marker=f"{PRIVATE_INPUT}-second"),
    )

    rows, ledgers = await _quota_rows(db_session)
    detail = blocked.json()["detail"]
    rendered_storage = _render_quota_storage(rows, ledgers)
    rendered_blocked = json.dumps(blocked.json(), ensure_ascii=False)

    assert first.status_code == 200
    assert blocked.status_code == 402
    assert detail["code"] == "report_quota_blocked"
    assert detail["reason_codes"] == ["report_quota_exhausted"]
    assert len(app.state.fake_service.calls) == 1
    assert len(rows) == 2
    assert len(ledgers) == 2
    assert rows[-1].decision_status == "blocked"
    assert PRIVATE_INPUT not in rendered_storage
    assert CURRENT_USER_ID not in rendered_storage
    assert CURRENT_USER_EMAIL not in rendered_storage
    assert PRIVATE_INPUT not in rendered_blocked
    assert CURRENT_USER_EMAIL not in rendered_blocked


def test_deep_review_document_quota_event_id_hashes_user_payload():
    event_id = deep_review_document_quota_event_id(
        user_id=CURRENT_USER_ID,
        doc_type=f"doc {PRIVATE_INPUT}",
        title=f"title {PRIVATE_INPUT}",
        input_data={f"field-{PRIVATE_INPUT}": PRIVATE_INPUT},
        language="zh",
    )

    assert event_id.startswith("deep_review_document_")
    assert PRIVATE_INPUT not in event_id
    assert CURRENT_USER_ID not in event_id
    assert CURRENT_USER_EMAIL not in event_id
