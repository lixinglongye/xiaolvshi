import json
import re

from services.legal_document_benchmark_coverage import (
    MAX_LOCAL_FIXTURES_PER_RUN,
    TARGET_DOCUMENT_TYPES,
    LegalDocumentBenchmarkCoverageService,
)


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{12,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def test_legal_document_benchmark_coverage_matrix_is_metadata_only():
    matrix = LegalDocumentBenchmarkCoverageService().build_matrix()

    assert matrix["status"] == "ready_with_gaps"
    assert matrix["summary"]["case_count"] == 3
    assert matrix["summary"]["target_document_type_count"] == len(TARGET_DOCUMENT_TYPES)
    assert matrix["summary"]["covered_document_type_count"] == 3
    assert matrix["summary"]["missing_document_type_count"] == 3
    assert matrix["summary"]["model_calls"] == "not_required"
    assert matrix["summary"]["network_access"] == "disabled"
    assert matrix["privacy_boundary"]["returns_snippets"] is False
    assert matrix["privacy_boundary"]["returns_raw_model_output"] is False
    assert matrix["privacy_boundary"]["external_dataset_downloads"] is False
    assert matrix["privacy_boundary"]["model_calls"] is False
    assert all("snippet" not in row for row in matrix["case_rows"])


def test_legal_document_benchmark_coverage_tracks_missing_document_types():
    matrix = LegalDocumentBenchmarkCoverageService().build_matrix()
    document_type_rows = {row["label"]: row for row in matrix["dimensions"]["document_types"]}

    assert matrix["target_document_types"] == list(TARGET_DOCUMENT_TYPES)
    assert matrix["missing_document_types"] == [
        "evidence_catalog",
        "settlement_agreement",
        "legal_opinion",
    ]
    assert document_type_rows["civil_complaint"]["covered"] is True
    assert document_type_rows["evidence_catalog"]["covered"] is False
    assert document_type_rows["settlement_agreement"]["case_ids"] == []
    assert document_type_rows["legal_opinion"]["coverage_count"] == 0


def test_legal_document_benchmark_coverage_queue_is_laptop_safe():
    matrix = LegalDocumentBenchmarkCoverageService().build_matrix()
    queue = matrix["next_fixture_queue"]

    assert 1 <= len(queue) <= MAX_LOCAL_FIXTURES_PER_RUN
    assert [item["document_type"] for item in queue] == [
        "evidence_catalog",
        "settlement_agreement",
        "legal_opinion",
    ]
    assert all(item["priority"] in {"high", "medium"} for item in queue)
    assert all(item["validation_target"].startswith("/api/v1/maintenance/") for item in queue)
    assert any("missing document types" in action for action in matrix["recommended_actions"])
    assert any("laptop-safe" in action for action in matrix["recommended_actions"])


def test_legal_document_benchmark_coverage_dimensions_are_reviewable():
    matrix = LegalDocumentBenchmarkCoverageService().build_matrix()

    assert matrix["summary"]["section_label_count"] >= 12
    assert matrix["summary"]["citation_label_count"] == 6
    assert matrix["summary"]["risk_label_count"] == 9
    assert matrix["summary"]["pii_category_count"] == 4
    assert all(row["case_ids"] for row in matrix["dimensions"]["required_sections"])
    assert all(row["case_ids"] for row in matrix["dimensions"]["expected_citations"])
    assert all(row["case_ids"] for row in matrix["dimensions"]["expected_risk_labels"])
    assert {"identity_number", "mobile_phone", "email", "api_key"} == {
        row["label"] for row in matrix["dimensions"]["banned_pii_categories"]
    }


def test_legal_document_benchmark_coverage_has_no_secret_or_raw_text_material():
    matrix = LegalDocumentBenchmarkCoverageService().build_matrix()
    serialized = json.dumps(matrix, ensure_ascii=False)

    for pattern in SENSITIVE_PATTERNS:
        assert re.search(pattern, serialized) is None
    assert "raw client documents" in matrix["privacy_note"]
    assert "raw fixture snippets" in matrix["privacy_note"]
    assert "cd app/backend && python -m pytest tests/test_legal_document_benchmark_coverage.py -q" in matrix[
        "validation_commands"
    ]


def test_legal_document_benchmark_coverage_route_returns_matrix():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/document-coverage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready_with_gaps"
    assert payload["data"]["summary"]["max_local_fixtures_per_run"] == MAX_LOCAL_FIXTURES_PER_RUN
