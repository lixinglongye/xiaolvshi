import re
from datetime import date

from services.legal_source_ingestion_metadata import LegalSourceIngestionMetadataService


def _valid_record(**overrides):
    record = {
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
        "official_url": "https://example.invalid/source",
        "retrieval_locator": "local-index://valid-source",
        "content_hash": "sha256:valid-source",
        "use_case": "contract_review",
        "ingestion_batch_id": "batch-2026-06-04",
    }
    record.update(overrides)
    return record


def test_ingestion_metadata_contract_exposes_schema_keys_and_sample_evaluation():
    payload = LegalSourceIngestionMetadataService().build_metadata_contract()

    assert payload["schema_version"] == "legal-source-ingestion-metadata-v1"
    assert payload["record_schema"]["required_fields"] == [
        "id",
        "title",
        "source_type",
        "jurisdiction",
        "effective_date",
        "citation",
        "last_verified_at",
    ]
    assert any(field["name"] == "jurisdiction" for field in payload["jurisdiction_fields"])
    assert any(field["name"] == "effective_date" for field in payload["effective_date_fields"])
    assert any(field["name"] == "citation" for field in payload["citation_fields"])
    assert any(field["name"] == "last_verified_at" for field in payload["freshness_fields"])
    assert {key["name"] for key in payload["dedupe_keys"]} >= {
        "citation_key",
        "effective_title_key",
        "issuer_title_key",
        "content_hash_key",
    }
    assert any(field["name"] == "raw_text" for field in payload["forbidden_fields"])
    assert payload["sample_evaluation"]["summary"]["record_count"] == len(payload["sample_source_records"])
    assert payload["sample_evaluation"]["status"] == "blocked"
    assert payload["integration_note"].startswith("This contract is intentionally adjacent")


def test_ingestion_metadata_accepts_complete_metadata_only_records():
    result = LegalSourceIngestionMetadataService().evaluate_records([_valid_record()])
    review = result["record_reviews"][0]

    assert result["status"] == "ready"
    assert result["summary"]["ready_count"] == 1
    assert review["status"] == "pass"
    assert review["freshness"]["status"] == "fresh"
    assert review["dedupe_keys"]["citation_key"] == "statute|cn-national|synthetic-citation-valid-source"
    assert review["recommended_actions"] == ["Source metadata is ready for local ingestion evaluation."]


def test_ingestion_metadata_blocks_missing_required_and_forbidden_fields():
    service = LegalSourceIngestionMetadataService()
    records = [
        _valid_record(
            id="missing-and-forbidden",
            citation="",
            raw_text="Do not store source body here.",
            metadata={"password": "secret"},
        )
    ]
    result = service.evaluate_records(records)
    contract = service.build_metadata_contract(records)
    review = result["record_reviews"][0]

    assert result["status"] == "blocked"
    assert contract["sample_evaluation"]["summary"]["forbidden_field_record_ids"] == ["missing-and-forbidden"]
    assert "missing_required_field" in review["flags"]
    assert "forbidden_field_present" in review["flags"]
    assert review["missing_required_fields"] == ["citation"]
    assert "raw_text" in review["forbidden_fields_present"]
    assert "metadata.password" in review["forbidden_fields_present"]
    assert "missing-and-forbidden" in result["summary"]["forbidden_field_record_ids"]


def test_ingestion_metadata_detects_duplicate_dedupe_keys():
    result = LegalSourceIngestionMetadataService().evaluate_records(
        [
            _valid_record(id="source-a", content_hash="sha256:duplicate", citation="Synthetic citation: same"),
            _valid_record(
                id="source-b",
                title="Synthetic duplicated title variant",
                retrieval_locator="local-index://source-b",
                content_hash="sha256:duplicate",
                citation="Synthetic citation: same",
            ),
        ]
    )

    assert result["status"] == "blocked"
    assert result["summary"]["duplicate_record_ids"] == []
    assert "sha256-duplicate" in result["summary"]["duplicate_dedupe_keys"]
    assert all("duplicate_dedupe_key" in review["flags"] for review in result["record_reviews"])
    assert all("content_hash_key" in review["duplicate_key_names"] for review in result["record_reviews"])


def test_ingestion_metadata_warns_when_freshness_review_is_due():
    result = LegalSourceIngestionMetadataService().evaluate_records(
        [
            _valid_record(
                id="review-due",
                last_verified_at="2025-07-10",
                content_hash="sha256:review-due",
            )
        ],
        reference_date=date(2026, 6, 4),
    )
    review = result["record_reviews"][0]

    assert result["status"] == "review_recommended"
    assert review["status"] == "warn"
    assert review["freshness"]["status"] == "review_due"
    assert "freshness_review_due" in review["flags"]


def test_ingestion_metadata_blocks_future_effective_or_invalid_dates():
    result = LegalSourceIngestionMetadataService().evaluate_records(
        [
            _valid_record(id="future-source", effective_date="2026-12-01", content_hash="sha256:future"),
            _valid_record(
                id="invalid-source",
                effective_date="2021/01/01",
                last_verified_at="2026/05/15",
                content_hash="sha256:invalid",
            ),
        ]
    )

    assert result["status"] == "blocked"
    assert "future_effective_date" in result["record_reviews"][0]["flags"]
    assert "invalid_effective_date" in result["record_reviews"][1]["flags"]
    assert "invalid_last_verified_at" in result["record_reviews"][1]["flags"]


def test_ingestion_metadata_redacts_sensitive_values_without_echoing_them():
    secret = "s" + "k-" + ("A" * 24)
    result = LegalSourceIngestionMetadataService().evaluate_records(
        [
            _valid_record(
                id="sensitive-source",
                title="Contact person@example.com password",
                citation=f"Synthetic citation {secret}",
                api_key=secret,
                content_hash="sha256:sensitive",
            )
        ]
    )
    text = str(result)

    assert "[redacted]" in text
    assert "person@example.com" not in text
    assert secret not in text
    assert not re.search(r"sk-[A-Za-z0-9]{20,}", text)
    assert "forbidden_field_present" in result["record_reviews"][0]["flags"]


def test_ingestion_metadata_route_returns_contract_and_record_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-review-benchmark/source-ingestion-metadata")

    assert response.status_code == 200
    assert response.json()["data"]["schema_version"] == "legal-source-ingestion-metadata-v1"

    reviewed = client.post(
        "/api/v1/maintenance/legal-review-benchmark/source-ingestion-metadata",
        json={"records": [_valid_record()]},
    )

    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["status"] == "ready"
