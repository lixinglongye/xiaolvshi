from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date

import pytest
from models.legal_source_index_entries import LegalSourceIndexEntryRecord
from services.legal_source_durable_index_plan import FORBIDDEN_FIELDS
from services.legal_source_index_repository import (
    LegalSourceIndexRepository,
    LegalSourceIndexValidationError,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _valid_source(**overrides) -> dict:
    source = {
        "id": "cn-valid-source",
        "title": "Synthetic valid legal source metadata",
        "source_title": "Synthetic source title",
        "source_type": "statute",
        "jurisdiction": "CN-National",
        "effective_date": "2021-01-01",
        "citation": "Synthetic citation: valid source",
        "last_verified_at": "2026-05-15",
        "authority_level": "national_statute",
        "issuer": "Synthetic national issuer",
        "publication_date": "2020-05-28",
        "amendment_date": "",
        "official_url": "https://example.invalid/source",
        "retrieval_locator": "local-index://valid-source",
        "content_hash": "sha256:valid-source",
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


def _repository() -> LegalSourceIndexRepository:
    return LegalSourceIndexRepository(reference_date=date(2026, 6, 4))


@pytest.mark.asyncio
async def test_upsert_source_records_writes_metadata_entries_and_filters_them():
    async with _sqlite_session() as db:
        repository = _repository()
        source = _valid_source()
        other_source = _valid_source(
            id="beijing-template",
            title="Synthetic Beijing template metadata",
            source_title="Synthetic template source",
            source_type="template",
            jurisdiction="CN-Beijing",
            effective_date="2025-11-15",
            citation="Synthetic citation: Beijing template",
            content_hash="sha256:beijing-template",
            use_case="lease_document_generation",
        )

        saved = await repository.upsert_source_records(db, [source, other_source])

        assert [entry.source_id for entry in saved] == ["cn-valid-source", "beijing-template"]
        assert saved[0].index_entry_id.startswith("idx-cn-valid-source-")
        assert saved[0].index_version == "legal-source-metadata-index-v1"
        assert saved[0].source_title == "Synthetic source title"
        assert saved[0].citation_key == "statute|cn-national|synthetic-citation-valid-source"
        assert saved[0].dedupe_key == "sha256-valid-source"
        assert saved[0].freshness_status == "fresh"
        assert saved[0].freshness_expires_at == "2027-05-15"
        assert saved[0].metadata_hash.startswith("sha256:")
        assert saved[0].use_case == "contract_review"

        filtered = await repository.list_entries(
            db,
            {
                "jurisdiction": "CN-National",
                "source_type": "statute",
                "effective_on_or_before": "2026-06-04",
                "freshness_status": ["fresh", "review_due"],
                "use_case": "contract_review",
            },
        )
        assert [entry.source_id for entry in filtered] == ["cn-valid-source"]

        missing = await repository.list_entries(db, {"use_case": "labor_dispute_review"})
        assert missing == []

        fetched = await repository.get_by_source_id(db, "cn-valid-source")
        assert fetched is not None
        assert fetched.title == "Synthetic valid legal source metadata"


@pytest.mark.asyncio
async def test_upsert_rejects_stale_or_raw_text_source_records_without_partial_writes():
    async with _sqlite_session() as db:
        repository = _repository()

        with pytest.raises(LegalSourceIndexValidationError) as stale_error:
            await repository.upsert_source_records(
                db,
                [
                    _valid_source(
                        id="stale-source",
                        last_verified_at="2024-01-01",
                        content_hash="sha256:stale-source",
                    )
                ],
            )
        stale_report = stale_error.value.validation_report
        assert stale_report["status"] == "blocked"
        assert "stale_freshness_metadata" in stale_report["entry_reviews"][0]["flags"]
        assert await repository.list_entries(db, {}) == []

        raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_PERSIST"
        with pytest.raises(LegalSourceIndexValidationError) as raw_text_error:
            await repository.upsert_source_records(
                db,
                [_valid_source(id="raw-source", content_hash="sha256:raw-source", raw_text=raw_text)],
            )
        raw_text_report = raw_text_error.value.validation_report
        assert raw_text_report["status"] == "blocked"
        assert "source_record.raw_text" in raw_text_report["entry_reviews"][0]["forbidden_fields_present"]
        assert raw_text not in str(raw_text_report)
        assert await repository.list_entries(db, {}) == []


@pytest.mark.asyncio
async def test_forbidden_fields_are_not_columns_or_queryable_repository_filters():
    table_columns = {column.name for column in LegalSourceIndexEntryRecord.__table__.columns}

    assert not table_columns & set(FORBIDDEN_FIELDS)
    assert {"raw_text", "embedding", "client_email", "client_name", "prompt"}.isdisjoint(table_columns)

    async with _sqlite_session() as db:
        repository = _repository()
        source = _valid_source(source_name="Synthetic source name")
        source.pop("source_title")
        saved = await repository.upsert_source_records(db, [source])

        assert not hasattr(saved[0], "raw_text")
        assert not hasattr(saved[0], "embedding")
        assert not hasattr(saved[0], "client_email")
        assert saved[0].source_title == "Synthetic source name"

        with pytest.raises(LegalSourceIndexValidationError) as filter_error:
            await repository.list_entries(db, {"raw_text": "do not query raw text", "embedding": [0.1, 0.2]})

        filter_report = filter_error.value.validation_report
        assert filter_report["status"] == "fail"
        assert "forbidden_query_filter_present" in filter_report["failures"]
        assert "raw_text" in filter_report["forbidden_fields_present"]
        assert "embedding" in filter_report["forbidden_fields_present"]
