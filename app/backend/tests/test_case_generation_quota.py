from datetime import datetime, timedelta
import json

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import Base
from models.billing_quota_idempotency_keys import BillingQuotaIdempotencyKey
from models.billing_quota_usage_counters import BillingQuotaUsageCounter
from models.case_facts import Case_facts
from models.case_materials import Case_materials
from models.case_parties import Case_parties
from models.cases import Cases
from models.claims import Claims
from models.evidence_items import Evidence_items
from models.generated_documents import Generated_documents
from models.legal_sources import Legal_sources
from models.subscriptions import Subscriptions
from services.case_intelligence import CaseDraftingService, CaseGenerationQuotaError


CURRENT_USER_ID = "case-generation-quota-user"
CURRENT_USER_EMAIL = "case-generation-quota@example.test"
PRIVATE_FACT = "PRIVATE_CASE_FACT_PATTERN_2d5a93"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Cases.__table__,
        Case_materials.__table__,
        Case_facts.__table__,
        Case_parties.__table__,
        Claims.__table__,
        Evidence_items.__table__,
        Legal_sources.__table__,
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


async def _case(db_session):
    case = Cases(
        user_id=CURRENT_USER_ID,
        title="Synthetic service dispute",
        case_type="civil",
        client_name="Synthetic Plaintiff",
        opposing_party="Synthetic Defendant",
        court_or_arbitration="Synthetic Court",
        claims="Refund service fee",
        summary="Synthetic summary",
    )
    db_session.add(case)
    await db_session.flush()
    db_session.add(
        Case_facts(
            user_id=CURRENT_USER_ID,
            case_id=case.id,
            fact_no="F-001",
            event_date="2026-01-01",
            fact_text=PRIVATE_FACT,
            source_refs="E-001",
        )
    )
    db_session.add(
        Evidence_items(
            user_id=CURRENT_USER_ID,
            case_id=case.id,
            evidence_id="E-001",
            sequence_no=1,
            evidence_name="Synthetic receipt",
            evidence_source="Synthetic source",
            page_range="1",
            proof_purpose="Prove service payment",
        )
    )
    db_session.add(
        Case_materials(
            user_id=CURRENT_USER_ID,
            case_id=case.id,
            material_no="E-001",
            title="Synthetic receipt",
            is_evidence=True,
            source="Synthetic source",
            proof_purpose="Prove service payment",
            page_refs="1",
        )
    )
    await db_session.commit()
    await db_session.refresh(case)
    return case


async def _quota_rows(db_session):
    rows = (
        await db_session.execute(select(BillingQuotaUsageCounter).order_by(BillingQuotaUsageCounter.id.asc()))
    ).scalars().all()
    ledgers = (
        await db_session.execute(select(BillingQuotaIdempotencyKey).order_by(BillingQuotaIdempotencyKey.id.asc()))
    ).scalars().all()
    return rows, ledgers


def _assert_quota_storage_is_private(rows, ledgers):
    rendered = " ".join(
        [
            *(row.idempotency_key + row.source_event_hash + row.quota_subject_hash + (row.reason_codes_json or "") for row in rows),
            *(ledger.idempotency_key + ledger.source_event_hash + ledger.quota_subject_hash for ledger in ledgers),
        ]
    )
    assert PRIVATE_FACT not in rendered
    assert CURRENT_USER_ID not in rendered
    assert CURRENT_USER_EMAIL not in rendered


@pytest.mark.asyncio
async def test_case_evidence_catalog_generation_consumes_report_quota(db_session):
    await _subscription(db_session, limit=1)
    case = await _case(db_session)

    payload = await CaseDraftingService(db_session).generate_evidence_catalog(
        case_id=case.id,
        user_id=CURRENT_USER_ID,
        user_role="user",
    )

    rows, ledgers = await _quota_rows(db_session)
    document_count = await db_session.scalar(select(func.count(Generated_documents.id)))

    assert payload["success"] is True
    assert payload["quota"]["decision_status"] == "ready"
    assert payload["quota"]["privacy_boundary"] == {
        "raw_document_text_included": False,
        "case_claims_included": False,
        "pii_included": False,
    }
    assert document_count == 1
    assert len(rows) == 1
    assert len(ledgers) == 1
    assert rows[0].source_event_hash
    _assert_quota_storage_is_private(rows, ledgers)


@pytest.mark.asyncio
async def test_case_civil_complaint_generation_blocks_without_insert_when_quota_exhausted(db_session):
    await _subscription(db_session, limit=1)
    case = await _case(db_session)
    first = await CaseDraftingService(db_session).generate_evidence_catalog(
        case_id=case.id,
        user_id=CURRENT_USER_ID,
        user_role="user",
    )

    with pytest.raises(CaseGenerationQuotaError) as exc_info:
        await CaseDraftingService(db_session).generate_civil_complaint(
            case_id=case.id,
            user_id=CURRENT_USER_ID,
            user_role="user",
            force_draft=True,
        )

    rows, ledgers = await _quota_rows(db_session)
    document_count = await db_session.scalar(select(func.count(Generated_documents.id)))
    detail = exc_info.value.detail

    assert first["success"] is True
    assert detail["code"] == "report_quota_blocked"
    assert detail["reason_codes"] == ["report_quota_exhausted"]
    assert document_count == 1
    assert len(rows) == 2
    assert len(ledgers) == 2
    assert rows[-1].decision_status == "blocked"
    _assert_quota_storage_is_private(rows, ledgers)
