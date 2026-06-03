from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.billing_quota_idempotency_keys import BillingQuotaIdempotencyKey
from models.billing_quota_usage_counters import BillingQuotaUsageCounter
from models.subscriptions import Subscriptions
import services.billing_entitlement_quota_binding as binding_module
from services.billing_entitlement_quota_binding import BillingEntitlementQuotaBindingService, build_quota_subject_hash


QUOTA_WINDOW = "2026-06"
SUBJECT_HASH = "qsh_abcdefghijklmnop"


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


async def _subscription(db_session, *, user_id: str, plan_type: str, limit: int | None = None, status: str = "active"):
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


@pytest.mark.asyncio
async def test_free_plan_summary_uses_persisted_usage_and_hides_real_email(db_session):
    user_id = "alice@example.test"
    quota_subject_hash = build_quota_subject_hash(user_id, namespace="test")
    await _subscription(db_session, user_id=user_id, plan_type="free")

    summary = await BillingEntitlementQuotaBindingService(db_session).build_entitlement_summary(
        user_id=user_id,
        quota_subject_hash=quota_subject_hash,
        quota_window=QUOTA_WINDOW,
    )

    assert summary["plan_type"] == "free"
    assert summary["limit"] == 2
    assert summary["persisted_usage"] == 0
    assert summary["remaining"] == 2
    assert summary["can_create_report"] is True
    assert summary["reason_codes"] == []
    assert "alice@example.test" not in str(summary)
    assert "user_id" not in summary


@pytest.mark.asyncio
async def test_paid_pro_alias_uses_personal_plan_limit(db_session):
    user_id = "paid-user"
    await _subscription(db_session, user_id=user_id, plan_type="pro")

    summary = await BillingEntitlementQuotaBindingService(db_session).build_entitlement_summary(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        quota_window=QUOTA_WINDOW,
    )

    assert summary["plan_type"] == "pro"
    assert summary["effective_plan_type"] == "personal"
    assert summary["limit"] == 20
    assert summary["remaining"] == 20
    assert summary["can_create_report"] is True


@pytest.mark.asyncio
async def test_consumption_blocks_after_free_quota_is_exhausted(db_session):
    user_id = "free-user"
    service = BillingEntitlementQuotaBindingService(db_session)
    await _subscription(db_session, user_id=user_id, plan_type="free")

    await service.consume_report_usage(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        source="report_generation",
        event_id="report-1",
        quota_window=QUOTA_WINDOW,
    )
    second = await service.consume_report_usage(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        source="report_generation",
        event_id="report-2",
        quota_window=QUOTA_WINDOW,
    )
    blocked = await service.consume_report_usage(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        source="report_generation",
        event_id="report-3",
        quota_window=QUOTA_WINDOW,
    )

    assert second["persisted_usage"] == 2
    assert second["remaining"] == 0
    assert second["can_create_report"] is False
    assert blocked["persisted_usage"] == 2
    assert blocked["remaining"] == 0
    assert blocked["can_create_report"] is False
    assert blocked["reason_codes"] == ["report_quota_exhausted"]
    assert blocked["last_usage_event"]["recorded"] is True
    assert blocked["last_usage_event"]["decision_status"] == "blocked"


@pytest.mark.asyncio
async def test_idempotent_replay_does_not_double_count_usage(db_session):
    user_id = "replay-user"
    service = BillingEntitlementQuotaBindingService(db_session)
    await _subscription(db_session, user_id=user_id, plan_type="personal")

    first = await service.consume_report_usage(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        source="report_generation",
        event_id="stable-event",
        quota_window=QUOTA_WINDOW,
    )
    replay = await service.consume_report_usage(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        source="report_generation",
        event_id="stable-event",
        quota_window=QUOTA_WINDOW,
    )

    usage_count = await db_session.scalar(select(func.count(BillingQuotaUsageCounter.id)))
    ledger = await db_session.scalar(select(BillingQuotaIdempotencyKey))

    assert first["persisted_usage"] == 1
    assert replay["persisted_usage"] == 1
    assert replay["remaining"] == 19
    assert replay["last_usage_event"]["recorded"] is False
    assert replay["last_usage_event"]["idempotent_replay"] is True
    assert usage_count == 1
    assert ledger.seen_count == 2


@pytest.mark.asyncio
async def test_same_source_event_with_different_units_raises_conflict(db_session):
    user_id = "conflict-user"
    service = BillingEntitlementQuotaBindingService(db_session)
    await _subscription(db_session, user_id=user_id, plan_type="personal")

    await service.consume_report_usage(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        source="report_generation",
        event_id="same-source-event",
        units=1,
        quota_window=QUOTA_WINDOW,
    )

    with pytest.raises(ValueError) as exc_info:
        await service.consume_report_usage(
            user_id=user_id,
            quota_subject_hash=SUBJECT_HASH,
            source="report_generation",
            event_id="same-source-event",
            units=2,
            quota_window=QUOTA_WINDOW,
        )

    assert str(exc_info.value) == "billing_quota_idempotency_conflict"
    assert await db_session.scalar(select(func.count(BillingQuotaUsageCounter.id))) == 1


@pytest.mark.asyncio
async def test_unknown_plan_returns_reason_code_and_no_limit(db_session):
    user_id = "legacy-user"
    service = BillingEntitlementQuotaBindingService(db_session)
    await _subscription(db_session, user_id=user_id, plan_type="legacy")

    summary = await service.build_entitlement_summary(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        quota_window=QUOTA_WINDOW,
    )
    blocked = await service.consume_report_usage(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        source="report_generation",
        event_id="legacy-report",
        quota_window=QUOTA_WINDOW,
    )

    assert summary["limit"] is None
    assert summary["remaining"] is None
    assert summary["can_create_report"] is False
    assert summary["reason_codes"] == ["unknown_plan"]
    assert blocked["persisted_usage"] == 0
    assert blocked["reason_codes"] == ["unknown_plan"]
    assert blocked["last_usage_event"]["decision_status"] == "blocked"


@pytest.mark.asyncio
async def test_known_plan_with_empty_limit_returns_plan_limit_reason(db_session, monkeypatch):
    user_id = "empty-limit-user"
    patched_limits = dict(binding_module.PLAN_LIMITS)
    patched_limits["empty_limit"] = {"report_quota_monthly": None, "team_seats": 1, "features": []}
    monkeypatch.setattr(binding_module, "PLAN_LIMITS", patched_limits)
    await _subscription(db_session, user_id=user_id, plan_type="empty_limit")

    summary = await BillingEntitlementQuotaBindingService(db_session).build_entitlement_summary(
        user_id=user_id,
        quota_subject_hash=SUBJECT_HASH,
        quota_window=QUOTA_WINDOW,
    )

    assert summary["plan_type"] == "empty_limit"
    assert summary["limit"] is None
    assert summary["remaining"] is None
    assert summary["can_create_report"] is False
    assert summary["reason_codes"] == ["plan_limit_unavailable"]
