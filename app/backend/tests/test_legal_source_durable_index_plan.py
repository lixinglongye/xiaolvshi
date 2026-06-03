import re
from datetime import date
from pathlib import Path

from services.legal_source_durable_index_plan import (
    FORBIDDEN_FIELDS,
    REQUIRED_INDEX_ENTRY_FIELDS,
    LegalSourceDurableIndexPlanService,
)


SECRET_PATTERN = re.compile(r"s[k]-[A-Za-z0-9_-]{12,}|[^@\s]+@[^@\s]+\.[^@\s]+", re.IGNORECASE)


def _service() -> LegalSourceDurableIndexPlanService:
    return LegalSourceDurableIndexPlanService()


def _valid_source(**overrides) -> dict:
    source = {
        "id": "cn-valid-source",
        "title": "Synthetic valid legal source metadata",
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


def test_durable_index_plan_exposes_metadata_only_schema_policy_and_sample_validation():
    plan = _service().build_plan()

    assert plan["schema_version"] == "legal-source-durable-index-plan-v1"
    assert plan["status"] == "ready"
    assert plan["local_only_guards"] == {
        "database_required": False,
        "vector_store_required": False,
        "network_required": False,
        "raw_text_storage_allowed": False,
        "router_integration_required": False,
        "release_or_ledger_integration_required": False,
    }
    assert set(plan["index_entry_schema"]["required_fields"]) == set(REQUIRED_INDEX_ENTRY_FIELDS)
    assert not set(plan["index_entry_schema"]["allowed_fields"]) & set(FORBIDDEN_FIELDS)
    assert any(field["name"] == "jurisdiction" for field in plan["jurisdiction_fields"])
    assert any(field["name"] == "effective_date" for field in plan["effective_date_fields"])
    assert any(field["name"] == "citation" for field in plan["citation_fields"])
    assert any(field["name"] == "freshness_status" for field in plan["freshness_fields"])
    assert {field["name"] for field in plan["dedupe_fields"]} >= {
        "dedupe_key",
        "citation_key",
        "effective_title_key",
        "content_hash_key",
        "metadata_hash",
    }
    assert {item["name"] for item in plan["query_filters"]} >= {
        "jurisdiction",
        "source_type",
        "effective_on_or_before",
        "freshness_status",
    }
    assert plan["retention_policy"]["raw_text_retention"] == "never_store"
    assert plan["rebuild_policy"]["external_services_required"] == []
    assert plan["sample_validation"]["status"] == "ready"
    assert len(plan["sample_index_entries"]) == len(plan["sample_source_records"])


def test_durable_index_entries_are_built_from_source_metadata_only():
    entries = _service().build_index_entries([_valid_source()])
    entry = entries[0].to_api()

    assert entry["source_id"] == "cn-valid-source"
    assert entry["index_entry_id"].startswith("idx-cn-valid-source-")
    assert entry["index_version"] == "legal-source-metadata-index-v1"
    assert entry["freshness_status"] == "fresh"
    assert entry["freshness_expires_at"] == "2027-05-15"
    assert entry["dedupe_key"] == "sha256-valid-source"
    assert entry["citation_key"] == "statute|cn-national|synthetic-citation-valid-source"
    assert entry["effective_title_key"].endswith("|2021-01-01")
    assert entry["metadata_hash"].startswith("sha256:")
    assert "raw_text" not in entry
    assert "embedding" not in entry
    assert _service().validate_index_entries(entries)["status"] == "ready"


def test_durable_index_validation_blocks_forbidden_source_and_entry_fields_without_echoing_values():
    secret = "s" + "k-" + ("A" * 24)
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_ECHO"
    client_email = "client" + "@example.com"
    source = _valid_source(
        id="source-with-forbidden",
        citation=f"Synthetic citation {secret}",
        raw_text=raw_text,
        client_email=client_email,
    )

    plan = _service().build_plan([source])
    review = plan["sample_validation"]["entry_reviews"][0]
    rendered = str(plan)

    assert plan["status"] == "blocked"
    assert "forbidden_field_present" in review["flags"]
    assert "sensitive_value_present" in review["flags"]
    assert "source_record.raw_text" in review["forbidden_fields_present"]
    assert "source_record.client_email" in review["forbidden_fields_present"]
    assert raw_text not in rendered
    assert client_email not in rendered
    assert secret not in rendered
    assert not SECRET_PATTERN.search(rendered)

    entry = _service().build_index_entries([_valid_source()])[0].to_api()
    entry.update({"raw_text": raw_text, "api_key": secret})
    result = _service().validate_index_entries([entry])
    entry_review = result["entry_reviews"][0]

    assert result["status"] == "blocked"
    assert "entry.raw_text" in entry_review["forbidden_fields_present"]
    assert "entry.api_key" in entry_review["forbidden_fields_present"]
    assert raw_text not in str(result)
    assert secret not in str(result)


def test_durable_index_validation_blocks_duplicates_and_stale_entries():
    stale_result = _service().build_plan(
        [
            _valid_source(
                id="stale-source",
                last_verified_at="2024-01-01",
                content_hash="sha256:stale-source",
            )
        ],
        reference_date=date(2026, 6, 4),
    )

    assert stale_result["status"] == "blocked"
    stale_review = stale_result["sample_validation"]["entry_reviews"][0]
    assert stale_review["freshness_status"] == "stale"
    assert "stale_freshness_metadata" in stale_review["flags"]
    assert stale_review["allowed_for_active_index"] is False

    duplicate_result = _service().build_plan(
        [
            _valid_source(id="source-a", content_hash="sha256:duplicate"),
            _valid_source(
                id="source-b",
                title="Synthetic other title",
                citation="Synthetic citation: other source",
                content_hash="sha256:duplicate",
            ),
        ]
    )

    assert duplicate_result["status"] == "blocked"
    assert duplicate_result["sample_validation"]["summary"]["duplicate_dedupe_keys"] == ["sha256-duplicate"]
    assert all(
        "duplicate_dedupe_key" in review["flags"]
        for review in duplicate_result["sample_validation"]["entry_reviews"]
    )


def test_durable_index_validation_warns_for_review_due_freshness():
    plan = _service().build_plan(
        [
            _valid_source(
                id="review-due",
                last_verified_at="2025-07-10",
                content_hash="sha256:review-due",
            )
        ],
        reference_date=date(2026, 6, 4),
    )
    review = plan["sample_validation"]["entry_reviews"][0]

    assert plan["status"] == "review_recommended"
    assert review["status"] == "warn"
    assert review["freshness_status"] == "review_due"
    assert review["allowed_for_active_index"] is True
    assert "freshness_review_due" in review["flags"]


def test_durable_index_validation_blocks_mismatched_dedupe_or_freshness_fields():
    entry = _service().build_index_entries([_valid_source()])[0].to_api()
    entry["freshness_status"] = "fresh"
    entry["freshness_expires_at"] = "2026-01-01"
    entry["citation_key"] = "wrong-key"
    entry["dedupe_key"] = "wrong-dedupe"

    result = _service().validate_index_entries([entry])
    review = result["entry_reviews"][0]

    assert result["status"] == "blocked"
    assert "freshness_expires_at_mismatch" in review["flags"]
    assert "citation_key_mismatch" in review["flags"]
    assert "dedupe_key_mismatch" in review["flags"]


def test_durable_index_query_filters_are_metadata_only():
    valid = _service().validate_query_filters(
        {
            "jurisdiction": "CN-National",
            "source_type": ["statute", "template"],
            "effective_on_or_before": "2026-06-04",
            "freshness_status": ["fresh", "review_due"],
            "use_case": "contract_review",
        }
    )
    assert valid["status"] == "pass"
    assert valid["active_index_query_safe"] is True

    warning = _service().validate_query_filters({"freshness_status": "stale"})
    assert warning["status"] == "warn"
    assert "stale_or_unknown_freshness_filter" in warning["warnings"]

    secret = "s" + "k-" + ("B" * 24)
    invalid = _service().validate_query_filters(
        {
            "jurisdiction": "US-CA",
            "raw_text": "Do not search raw text here",
            "embedding": [0.1, 0.2],
            "api_key": secret,
            "effective_on_or_before": "2026/06/04",
        }
    )
    rendered = str(invalid)

    assert invalid["status"] == "fail"
    assert "unsupported_jurisdiction_filter" in invalid["failures"]
    assert "forbidden_query_filter_present" in invalid["failures"]
    assert "invalid_effective_filter_date" in invalid["failures"]
    assert "raw_text" in invalid["forbidden_fields_present"]
    assert "embedding" in invalid["forbidden_fields_present"]
    assert "api_key" in invalid["forbidden_fields_present"]
    assert secret not in rendered
    assert not SECRET_PATTERN.search(rendered)


def test_durable_index_plan_service_has_no_db_vector_network_or_router_dependency():
    service_path = Path(__file__).resolve().parents[1] / "services" / "legal_source_durable_index_plan.py"
    service_source = service_path.read_text(encoding="utf-8")

    assert not re.search(r"^(from|import)\s+(requests|httpx|urllib|sqlalchemy|chromadb|faiss|qdrant)", service_source, re.M)
    assert not re.search(r"^(from|import)\s+routers\b", service_source, re.M)
    assert "legal_source_ingestion_metadata" not in service_source
    assert "legal_source_freshness_policy" not in service_source


def test_durable_index_plan_route_returns_template_and_record_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/legal-review-benchmark/source-durable-index-plan")
    alias_response = client.get("/api/v1/maintenance/legal-source-durable-index-plan")
    record_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/source-durable-index-plan",
        json={"source_records": [_valid_source()]},
    )

    assert template_response.status_code == 200
    assert template_response.json()["success"] is True
    assert template_response.json()["data"]["status"] == "ready"
    assert alias_response.status_code == 200
    assert alias_response.json()["data"]["schema_version"] == template_response.json()["data"]["schema_version"]
    assert record_response.status_code == 200
    assert record_response.json()["data"]["status"] == "ready"
    assert record_response.json()["data"]["sample_validation"]["summary"]["ready_entry_count"] == 1
