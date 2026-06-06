import json
import re

from services.legal_benchmark_fixture_crosswalk import LegalBenchmarkFixtureCrosswalkService


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{12,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def test_fixture_crosswalk_builds_metadata_only_source_rows():
    crosswalk = LegalBenchmarkFixtureCrosswalkService().build_crosswalk()

    assert crosswalk["status"] == "ready"
    assert crosswalk["method"]["type"] == "legal-benchmark-fixture-crosswalk"
    assert crosswalk["summary"]["source_count"] >= 7
    assert crosswalk["summary"]["source_with_benchmark_case_count"] >= 7
    assert crosswalk["summary"]["source_with_local_fixture_count"] >= 7
    assert crosswalk["summary"]["source_with_document_fixture_count"] >= 3
    assert crosswalk["summary"]["source_with_small_corpus_count"] >= 6
    assert crosswalk["summary"]["public_benchmark_score_claimed"] is False
    assert crosswalk["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert crosswalk["privacy_boundary"]["returns_local_fixture_snippets"] is False
    assert crosswalk["privacy_boundary"]["returns_small_corpus_excerpts"] is False
    assert crosswalk["privacy_boundary"]["downloads_datasets"] is False
    assert crosswalk["privacy_boundary"]["model_calls"] is False


def test_fixture_crosswalk_maps_new_public_sources_to_document_and_corpus_fixtures():
    crosswalk = LegalBenchmarkFixtureCrosswalkService().build_crosswalk()
    rows = {row["source_id"]: row for row in crosswalk["source_rows"]}

    assert "legal-rag-grounding" in rows["legalbench-rag"]["benchmark_case_ids"]
    assert "fixture-low-text-pdf-page-small" in rows["legalbench-rag"]["local_fixture_ids"]
    assert "ldoc-legal-opinion-mini" in rows["legalbench-rag"]["document_fixture_ids"]
    assert "small-corpus-labor-001" in rows["legalbench-rag"]["small_corpus_item_ids"]
    assert rows["legalbench-rag"]["coverage_status"] == "ready"

    assert "ldoc-contract-review-mini" in rows["lexeval"]["document_fixture_ids"]
    assert "small-corpus-service-004" in rows["lexeval"]["small_corpus_item_ids"]
    assert rows["lexeval"]["coverage_status"] == "ready"

    assert "ldoc-settlement-agreement-mini" in rows["casegen"]["document_fixture_ids"]
    assert "service-contract-risk" in rows["casegen"]["benchmark_case_ids"]
    assert rows["casegen"]["coverage_status"] == "ready"


def test_fixture_crosswalk_marks_catalog_and_gap_work_without_claiming_scores():
    crosswalk = LegalBenchmarkFixtureCrosswalkService().build_crosswalk()
    rows = {row["source_id"]: row for row in crosswalk["source_rows"]}
    gaps = {row["source_id"]: row for row in crosswalk["gap_queue"]}

    assert rows["pile-of-law"]["coverage_status"] == "catalog_reference_mapped"
    assert "small_corpus_mapping_missing" in gaps["pile-of-law"]["gap_reasons"]
    assert "document_fixture_mapping_missing" in gaps["cuad"]["gap_reasons"]
    assert any("fixture path" in action for action in crosswalk["recommended_actions"])
    assert any("python -m pytest tests/test_legal_benchmark_fixture_crosswalk.py -q" == command for command in crosswalk["validation_commands"])


def test_fixture_crosswalk_does_not_return_raw_snippets_or_secrets():
    crosswalk = LegalBenchmarkFixtureCrosswalkService().build_crosswalk()
    serialized = json.dumps(crosswalk, ensure_ascii=False)

    assert "Service Agreement. Alpha Service Provider" not in serialized
    assert "OCR page 7 text fragment" not in serialized
    assert "synthetic_excerpt" not in serialized
    assert "sample_text" not in serialized
    assert "input_excerpt" not in serialized
    for pattern in SENSITIVE_PATTERNS:
        assert re.search(pattern, serialized) is None


def test_fixture_crosswalk_route_returns_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/fixture-crosswalk")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["source_count"] >= 7
