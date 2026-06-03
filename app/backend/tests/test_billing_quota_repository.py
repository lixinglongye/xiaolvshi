import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.billing_quota_idempotency_keys import BillingQuotaIdempotencyKey
from models.billing_quota_usage_counters import BillingQuotaUsageCounter
from services.billing_quota_repository import BillingQuotaRepository


def _event(**overrides):
    data = {
        "event_id": "billing-quota-event-001",
        "event_type": "billing_quota_usage_counter",
        "timestamp": "2026-06-04T08:00:00Z",
        "idempotency_key": "bqp:v1:qsh_abcdefghijklmnop:2026-06:review:review_credits:src_000001",
        "quota_subject_hash": "qsh_abcdefghijklmnop",
        "plan_type": "personal",
        "action": "review",
        "usage_metric": "review_credits",
        "units": 1,
        "request_units": 1,
        "quota_window": "2026-06",
        "counter_bucket": "subject_metric_monthly",
        "allowed": True,
        "decision_status": "ready",
        "limit": 20,
        "used_before": 2,
        "remaining_before": 18,
        "remaining_after": 17,
        "over_limit_reason_codes": [],
        "policy_version": "billing-usage-quota-v1",
        "entitlement_snapshot_id": "ent_snap_opaque_001",
        "source_component": "quota_policy",
    }
    data.update(overrides)
    return data


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        BillingQuotaUsageCounter.__table__,
        BillingQuotaIdempotencyKey.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_billing_quota_repository_records_and_aggregates_usage(db_session):
    repo = BillingQuotaRepository()
    first = _event()
    second = _event(
        event_id="billing-quota-event-002",
        timestamp="2026-06-04T08:01:00Z",
        idempotency_key="bqp:v1:qsh_abcdefghijklmnop:2026-06:review:review_credits:src_000002",
        units=2,
        request_units=2,
        used_before=3,
        remaining_before=17,
        remaining_after=15,
    )

    created = await repo.record_usage_event(db_session, first)
    await repo.record_usage_event(db_session, second)

    assert created["recorded"] is True
    assert created["idempotent_replay"] is False
    assert created["quota_subject_hash"] == "qsh_abcdefghijklmnop"
    assert "event_id" not in created
    assert "source_component" not in created

    snapshot = await repo.get_usage_snapshot(
        db_session,
        "qsh_abcdefghijklmnop",
        "review_credits",
        "2026-06",
    )
    assert snapshot == {
        "quota_subject_hash": "qsh_abcdefghijklmnop",
        "usage_metric": "review_credits",
        "quota_window": "2026-06",
        "units": 3,
        "event_count": 2,
        "limit": 20.0,
        "used": 5.0,
        "remaining": 15.0,
        "decision_status": "ready",
        "reason_codes": [],
    }

    events = await repo.list_events(db_session, "qsh_abcdefghijklmnop")
    assert [event["units"] for event in events] == [1, 2]
    assert all("raw_payload" not in event and "payment_intent" not in event for event in events)


@pytest.mark.asyncio
async def test_billing_quota_repository_idempotency_same_key_same_hash_noops(db_session):
    repo = BillingQuotaRepository()
    event = _event()

    first = await repo.record_usage_event(db_session, event)
    replay = await repo.record_usage_event(db_session, dict(event))

    assert first["recorded"] is True
    assert replay["recorded"] is False
    assert replay["idempotent_replay"] is True

    usage_count = await db_session.scalar(select(func.count(BillingQuotaUsageCounter.id)))
    ledger_count = await db_session.scalar(select(func.count(BillingQuotaIdempotencyKey.id)))
    ledger = await db_session.scalar(select(BillingQuotaIdempotencyKey))
    snapshot = await repo.get_usage_snapshot(db_session, "qsh_abcdefghijklmnop", "review_credits", "2026-06")

    assert usage_count == 1
    assert ledger_count == 1
    assert ledger.seen_count == 2
    assert snapshot["units"] == 1
    assert snapshot["event_count"] == 1


@pytest.mark.asyncio
async def test_billing_quota_repository_idempotency_same_key_different_hash_rejects(db_session):
    repo = BillingQuotaRepository()
    event = _event()
    await repo.record_usage_event(db_session, event)

    conflicting = _event(units=2, request_units=2, remaining_after=16)
    with pytest.raises(ValueError) as exc_info:
        await repo.record_usage_event(db_session, conflicting)

    assert str(exc_info.value) == "billing_quota_idempotency_conflict"
    usage_count = await db_session.scalar(select(func.count(BillingQuotaUsageCounter.id)))
    snapshot = await repo.get_usage_snapshot(db_session, "qsh_abcdefghijklmnop", "review_credits", "2026-06")
    assert usage_count == 1
    assert snapshot["units"] == 1


@pytest.mark.asyncio
async def test_billing_quota_repository_rejects_duplicate_source_event_with_new_idempotency_key(db_session):
    repo = BillingQuotaRepository()
    event = _event()
    await repo.record_usage_event(db_session, event)

    duplicate_source = _event(idempotency_key="bqp:v1:qsh_abcdefghijklmnop:2026-06:review:review_credits:src_000099")
    with pytest.raises(ValueError) as exc_info:
        await repo.record_usage_event(db_session, duplicate_source)

    usage_count = await db_session.scalar(select(func.count(BillingQuotaUsageCounter.id)))
    ledger_count = await db_session.scalar(select(func.count(BillingQuotaIdempotencyKey.id)))
    snapshot = await repo.get_usage_snapshot(db_session, "qsh_abcdefghijklmnop", "review_credits", "2026-06")
    assert str(exc_info.value) == "billing_quota_source_event_duplicate"
    assert usage_count == 1
    assert ledger_count == 1
    assert snapshot["units"] == 1


@pytest.mark.asyncio
async def test_billing_quota_repository_rejects_forbidden_raw_and_payment_without_echo(db_session):
    repo = BillingQuotaRepository()
    raw_payload = "UNSAFE_RAW_PAYLOAD_SHOULD_NOT_ECHO"
    payment_intent = "pi_" + ("A" * 18)
    event = _event(raw_payload=raw_payload, payment_intent=payment_intent)

    with pytest.raises(ValueError) as exc_info:
        await repo.record_usage_event(db_session, event)

    rendered_error = str(exc_info.value)
    assert "billing_quota_event_validation_failed" in rendered_error
    assert raw_payload not in rendered_error
    assert payment_intent not in rendered_error
    assert "raw_payload" not in rendered_error
    assert "payment_intent" not in rendered_error

    usage_count = await db_session.scalar(select(func.count(BillingQuotaUsageCounter.id)))
    ledger_count = await db_session.scalar(select(func.count(BillingQuotaIdempotencyKey.id)))
    assert usage_count == 0
    assert ledger_count == 0
