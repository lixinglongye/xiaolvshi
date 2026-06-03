from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date

import pytest
from models.legal_source_index_entries import LegalSourceIndexEntryRecord
from services.legal_rag_index_binding import LegalRagIndexBindingService
from services.legal_source_durable_index_plan import FORBIDDEN_FIELDS
from services.legal_source_index_repository import LegalSourceIndexRepository
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _valid_source(**overrides) -> dict:
    source = {
        "id": "cn-statute-2021",
        "title": "Synthetic national statute metadata",
        "source_title": "Synthetic statute source",
        "source_type": "statute",
        "jurisdiction": "CN-National",
        "effective_date": "2021-01-01",
        "citation": "Synthetic citation: national statute 2021",
        "last_verified_at": "2026-05-15",
        "authority_level": "national_statute",
        "issuer": "Synthetic national issuer",
        "publication_date": "2020-05-28",
        "amendment_date": "",
        "official_url": "https://example.invalid/statute",
        "retrieval_locator": "local-index://cn-statute-2021",
        "content_hash": "sha256:cn-statute-2021",
        "use_case": "contract_review",
        "ingestion_batch_id": "batch-2026-06-04",
    }
    source.update(overrides)
    return source


@asynccontextmanager
async def _sqlite_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(LegalSourceIndexEntryRecord.__table__.create)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            yield session
    finally:
        await engine.dispose()


def _service() -> LegalRagIndexBindingService:
    repository = LegalSourceIndexRepository(reference_date=date(2026, 6, 4))
    return LegalRagIndexBindingService(repository=repository)


@pytest.mark.asyncio
async def test_build_retrieval_plan_selects_sources_by_jurisdiction_type_effective_on_and_source_ids():
    async with _sqlite_session() as db:
        service = _service()
        await service.repository.upsert_source_records(
            db,
            [
                _valid_source(),
                _valid_source(
                    id="cn-statute-2025",
                    title="Synthetic newer statute metadata",
                    effective_date="2025-03-01",
                    citation="Synthetic citation: national statute 2025",
                    retrieval_locator="local-index://cn-statute-2025",
                    content_hash="sha256:cn-statute-2025",
                ),
                _valid_source(
                    id="beijing-template",
                    title="Synthetic Beijing template metadata",
                    source_title="Synthetic template source",
                    source_type="template",
                    jurisdiction="CN-Beijing",
                    effective_date="2023-07-01",
                    citation="Synthetic citation: Beijing template",
                    authority_level="template",
                    retrieval_locator="local-index://beijing-template",
                    content_hash="sha256:beijing-template",
                    use_case="lease_document_generation",
                ),
            ],
        )

        plan = await service.build_retrieval_plan(
            db,
            {
                "jurisdiction": "CN-National",
                "document_type": "statute",
                "effective_on": "2024-12-31",
                "source_ids": ["cn-statute-2021"],
                "use_case": "contract_review",
            },
        )

        assert plan["status"] == "ready"
        assert plan["blocked"] is False
        assert plan["selected_source_ids"] == ["cn-statute-2021"]
        assert plan["filters"]["document_type"] == "statute"
        assert plan["repository_filters"]["source_type"] == "statute"
        assert plan["repository_filters"]["effective_on_or_before"] == "2024-12-31"
        assert plan["coverage_counts"]["selected_source_count"] == 1
        assert plan["selected_sources"][0]["jurisdiction"] == "CN-National"
        assert plan["selected_sources"][0]["retrieval_locator"] == "local-index://cn-statute-2021"
        assert "cn-statute-2025" not in plan["selected_source_ids"]
        assert "beijing-template" not in plan["selected_source_ids"]
        assert set(plan["selected_sources"][0]).isdisjoint(FORBIDDEN_FIELDS)
        assert "content_hash" not in plan["selected_sources"][0]


@pytest.mark.asyncio
async def test_build_retrieval_plan_excludes_stale_sources_and_reports_reason_codes():
    async with _sqlite_session() as db:
        service = _service()
        saved = await service.repository.upsert_source_records(
            db,
            [
                _valid_source(id="active-statute", citation="Synthetic citation: active", content_hash="sha256:active"),
                _valid_source(id="stale-statute", citation="Synthetic citation: stale", content_hash="sha256:stale"),
            ],
        )
        saved[1].freshness_status = "stale"
        await db.commit()

        plan = await service.build_retrieval_plan(
            db,
            {
                "jurisdiction": "CN-National",
                "document_type": "statute",
                "effective_on": "2026-06-04",
            },
        )

        assert plan["status"] == "ready_with_warnings"
        assert plan["blocked"] is False
        assert plan["selected_source_ids"] == ["active-statute"]
        assert plan["blocked_source_ids"] == ["stale-statute"]
        assert plan["stale_source_ids"] == ["stale-statute"]
        assert "stale_or_unknown_sources_excluded" in plan["reason_codes"]
        assert plan["coverage_counts"]["blocked_source_count"] == 1
        assert plan["coverage_counts"]["stale_source_count"] == 1


@pytest.mark.asyncio
async def test_evaluate_retrieval_builds_payload_from_retrieval_plan_and_fixture_ids():
    async with _sqlite_session() as db:
        service = _service()
        await service.repository.upsert_source_records(db, [_valid_source()])
        plan = await service.build_retrieval_plan(
            db,
            {
                "jurisdiction": "CN-National",
                "document_type": "statute",
                "effective_on": "2026-06-04",
            },
        )

        payload = service.evaluate_retrieval(
            plan,
            retrieved_source_ids=["cn-statute-2021"],
            answer_citation_source_ids=["cn-statute-2021"],
            verified_claim_count=3,
            total_claim_count=3,
        )

        assert payload["evaluation_input"]["expected_source_ids"] == ["cn-statute-2021"]
        assert payload["evaluation_input"]["retrieved_source_ids"] == ["cn-statute-2021"]
        assert payload["evaluation_input"]["answer_citation_source_ids"] == ["cn-statute-2021"]
        assert payload["evaluation_input"]["stale_source_ids"] == []
        assert payload["evaluation"]["status"] == "pass"
        assert payload["retrieval_plan"]["selected_source_ids"] == ["cn-statute-2021"]


@pytest.mark.asyncio
async def test_build_retrieval_plan_blocks_empty_coverage_with_reason_code():
    async with _sqlite_session() as db:
        service = _service()

        plan = await service.build_retrieval_plan(
            db,
            {
                "jurisdiction": "CN-National",
                "document_type": "statute",
                "effective_on": "2026-06-04",
                "source_ids": ["missing-source"],
            },
        )

        assert plan["status"] == "blocked"
        assert plan["blocked"] is True
        assert plan["selected_source_ids"] == []
        assert "no_index_coverage" in plan["reason_codes"]
        assert plan["missing_requested_source_ids"] == ["missing-source"]
        assert plan["coverage_counts"]["selected_source_count"] == 0


@pytest.mark.asyncio
async def test_build_retrieval_plan_blocks_forbidden_validation_without_leaking_raw_text():
    async with _sqlite_session() as db:
        service = _service()
        await service.repository.upsert_source_records(db, [_valid_source()])
        raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK"

        plan = await service.build_retrieval_plan(
            db,
            {
                "jurisdiction": "CN-National",
                "document_type": "statute",
                "raw_text": raw_text,
                "source_ids": ["cn-statute-2021"],
            },
        )

        assert plan["status"] == "blocked"
        assert plan["selected_sources"] == []
        assert "forbidden_query_filter_present" in plan["reason_codes"]
        assert "raw_text" in plan["validation"]["forbidden_fields_present"]
        assert raw_text not in str(plan)
        assert "embedding" not in str(plan)
