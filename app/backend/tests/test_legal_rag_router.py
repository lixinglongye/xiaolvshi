from __future__ import annotations

import json
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

from core.database import get_db
from models.legal_source_index_entries import LegalSourceIndexEntryRecord
from routers.legal_rag import router
from services.legal_source_durable_index_plan import FORBIDDEN_FIELDS
from services.legal_source_index_repository import LegalSourceIndexRepository


def _valid_source(**overrides) -> dict:
    source = {
        "id": "cn-router-statute",
        "title": "Synthetic router statute metadata",
        "source_title": "Router statute source",
        "source_type": "statute",
        "jurisdiction": "CN-National",
        "effective_date": "2021-01-01",
        "citation": "Synthetic citation: router statute",
        "last_verified_at": "2026-05-15",
        "authority_level": "national_statute",
        "issuer": "Synthetic national issuer",
        "publication_date": "2020-05-28",
        "amendment_date": "",
        "official_url": "https://example.invalid/router-statute",
        "retrieval_locator": "local-index://cn-router-statute",
        "content_hash": "sha256:cn-router-statute",
        "use_case": "contract_review",
        "ingestion_batch_id": "batch-router-2026-06-04",
    }
    source.update(overrides)
    return source


@pytest.fixture
def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    app = fastapi.FastAPI()
    app.include_router(router)

    @app.on_event("startup")
    async def _create_tables_and_seed_sources():
        async with engine.begin() as conn:
            await conn.run_sync(LegalSourceIndexEntryRecord.__table__.create)

        repository = LegalSourceIndexRepository(reference_date=date(2026, 6, 4))
        async with session_maker() as session:
            await repository.upsert_source_records(
                session,
                [
                    _valid_source(),
                    _valid_source(
                        id="cn-router-template",
                        title="Synthetic router template metadata",
                        source_title="Router template source",
                        source_type="template",
                        jurisdiction="CN-Beijing",
                        effective_date="2024-03-01",
                        citation="Synthetic citation: router template",
                        authority_level="template",
                        retrieval_locator="local-index://cn-router-template",
                        content_hash="sha256:cn-router-template",
                        use_case="lease_document_generation",
                    ),
                ],
            )

    @app.on_event("shutdown")
    async def _dispose_engine():
        await engine.dispose()

    async def _override_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _override_db

    with testclient.TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_retrieval_plan_route_returns_repository_metadata_only_sources(client):
    response = client.post(
        "/api/v1/legal-rag/retrieval-plan",
        json={
            "jurisdiction": "CN-National",
            "document_type": "statute",
            "effective_on": "2026-06-04",
            "source_ids": ["cn-router-statute"],
            "use_case": "contract_review",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]
    source = data["selected_sources"][0]

    assert payload["success"] is True
    assert data["status"] == "ready"
    assert data["selected_source_ids"] == ["cn-router-statute"]
    assert source["source_id"] == "cn-router-statute"
    assert source["source_title"] == "Router statute source"
    assert source["retrieval_locator"] == "local-index://cn-router-statute"
    assert source["metadata_hash"].startswith("sha256:")
    assert set(source).isdisjoint(FORBIDDEN_FIELDS)
    assert "content_hash" not in source
    assert "raw_text" not in json.dumps(payload)


def test_evaluate_route_builds_plan_then_scores_without_echoing_claim_or_pii_details(client):
    raw_claim = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK_FROM_EVALUATE"
    pii_value = "client-router@example.test"

    response = client.post(
        "/api/v1/legal-rag/evaluate",
        json={
            "filters": {
                "jurisdiction": "CN-National",
                "document_type": "statute",
                "effective_on": "2026-06-04",
                "source_ids": ["cn-router-statute"],
            },
            "retrieved_source_ids": ["cn-router-statute"],
            "answer_citation_source_ids": ["cn-router-statute"],
            "verified_claim_count": 2,
            "total_claim_count": 2,
            "unsupported_claims": [{"claim": raw_claim, "severity": "low"}],
            "pii_findings": [{"value": pii_value, "severity": "low"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    assert payload["success"] is True
    assert data["retrieval_plan"]["selected_source_ids"] == ["cn-router-statute"]
    assert data["evaluation_input"]["expected_source_ids"] == ["cn-router-statute"]
    assert data["evaluation_input"]["retrieved_source_ids"] == ["cn-router-statute"]
    assert data["evaluation_input"]["answer_citation_source_ids"] == ["cn-router-statute"]
    assert data["evaluation_input"]["unsupported_claim_count"] == 1
    assert data["evaluation_input"]["pii_finding_count"] == 1
    assert "unsupported_claims" not in data["evaluation_input"]
    assert "pii_findings" not in data["evaluation_input"]
    assert data["evaluation"]["status"] == "pass"
    assert raw_claim not in response.text
    assert pii_value not in response.text


def test_forbidden_raw_text_query_returns_blocked_plan_without_leaking_value(client):
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK_FROM_RETRIEVAL_PLAN"

    response = client.post(
        "/api/v1/legal-rag/retrieval-plan",
        json={
            "jurisdiction": "CN-National",
            "document_type": "statute",
            "source_ids": ["cn-router-statute"],
            "raw_text": raw_text,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    assert payload["success"] is True
    assert data["status"] == "blocked"
    assert data["selected_source_ids"] == []
    assert data["selected_sources"] == []
    assert "forbidden_query_filter_present" in data["reason_codes"]
    assert "raw_text" in data["validation"]["forbidden_fields_present"]
    assert raw_text not in response.text


def test_empty_index_coverage_returns_blocked_plan(client):
    response = client.post(
        "/api/v1/legal-rag/retrieval-plan",
        json={
            "jurisdiction": "CN-National",
            "document_type": "statute",
            "effective_on": "2026-06-04",
            "source_ids": ["missing-router-source"],
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["status"] == "blocked"
    assert data["blocked"] is True
    assert data["selected_source_ids"] == []
    assert data["missing_requested_source_ids"] == ["missing-router-source"]
    assert "no_index_coverage" in data["reason_codes"]
    assert data["coverage_counts"]["selected_source_count"] == 0


def test_invalid_evaluate_filters_return_400_without_echoing_payload_values(client):
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK_FROM_400"

    response = client.post(
        "/api/v1/legal-rag/evaluate",
        json={"filters": ["not-an-object", {"raw_text": raw_text}]},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "invalid_legal_rag_request"
    assert raw_text not in response.text
