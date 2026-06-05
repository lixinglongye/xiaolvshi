import re

import pytest

from services.legal_rag_retrieval_diagnostics_gate import LegalRagRetrievalDiagnosticsGateService


def test_retrieval_diagnostics_gate_builds_metadata_only_rows():
    gate = LegalRagRetrievalDiagnosticsGateService().build_gate()

    assert gate["id"] == "legal-rag-retrieval-diagnostics-gate"
    assert gate["status"] == "ready_with_blockers"
    assert gate["summary"]["diagnostic_row_count"] == 6
    assert gate["summary"]["ready_row_count"] == 1
    assert gate["summary"]["review_row_count"] >= 3
    assert gate["summary"]["blocked_row_count"] >= 1
    assert gate["summary"]["authority_coverage_ready_count"] >= 2
    assert gate["summary"]["authority_coverage_partial_count"] >= 2
    assert gate["summary"]["authority_coverage_gap_count"] >= 1
    assert gate["summary"]["retrieval_depth_gap_count"] >= 2
    assert gate["summary"]["jurisdiction_gap_count"] >= 2
    assert gate["summary"]["freshness_gap_count"] >= 3
    assert gate["summary"]["cheap_first_retry_count"] >= 3
    assert gate["summary"]["retrieval_recall_weight"] == 30
    assert gate["summary"]["citation_precision_weight"] == 25

    row_ids = {row["id"] for row in gate["diagnostic_rows"]}
    assert {
        "retrieval-contract-primary-authority",
        "retrieval-review-due-local-rule",
        "retrieval-jurisdiction-drift",
        "retrieval-shallow-top-k",
        "retrieval-citation-source-mismatch",
        "retrieval-empty-index-coverage",
    } <= row_ids


def test_retrieval_diagnostics_gate_links_existing_gates_and_release_actions():
    gate = LegalRagRetrievalDiagnosticsGateService().build_gate()
    rows = {row["id"]: row for row in gate["diagnostic_rows"]}

    ready = rows["retrieval-contract-primary-authority"]
    empty = rows["retrieval-empty-index-coverage"]
    shallow = rows["retrieval-shallow-top-k"]
    mismatch = rows["retrieval-citation-source-mismatch"]

    assert ready["release_action"] == "allow_retrieval_use"
    assert ready["retrieval_status"] == "ready"
    assert ready["source_coverage_status"] == "ready"
    assert empty["release_action"] == "block_retrieval_use"
    assert empty["top_k_depth_status"] == "empty"
    assert "retrieval_gap" in empty["reason_codes"]
    assert "citation_gap" in mismatch["reason_codes"]
    assert shallow["release_action"] == "review_before_answer"
    assert "legal-rag-index-binding" in empty["linked_gate_ids"]
    assert "legal-rag-authority-citation-gate" in empty["linked_gate_ids"]
    assert "legal-rag-abstention-escalation-gate" in empty["linked_gate_ids"]
    assert empty["linked_abstention_modes"]
    assert mismatch["linked_authority_row_ids"]

    for row in gate["diagnostic_rows"]:
        assert row["cheap_first_action"]["model_called"] is False
        assert row["cheap_first_action"]["gateway_called"] is False
        assert row["privacy_boundary"]["raw_query_returned"] is False
        assert row["privacy_boundary"]["retrieved_context_returned"] is False
        assert row["privacy_boundary"]["raw_legal_text_returned"] is False


def test_retrieval_diagnostics_gate_claim_and_privacy_boundaries_are_explicit():
    gate = LegalRagRetrievalDiagnosticsGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["dataset_downloaded"] is False
    assert gate["summary"]["raw_query_included"] is False
    assert gate["summary"]["raw_retrieved_context_included"] is False
    assert gate["summary"]["raw_legal_text_included"] is False
    assert gate["claim_boundary"]["legal_advice_claimed"] is False
    assert gate["claim_boundary"]["retrieval_quality_claimed"] is False
    assert gate["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_retrieved_context"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert gate["diagnostic_policy"]["cheap_first_default"] is True
    assert gate["diagnostic_policy"]["premium_exception_default_allowed"] is False

    text = str(gate)
    assert "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK" not in text
    assert "Can the claimant still file" not in text
    assert "The claimant can still file" not in text
    assert "Article 99" not in text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", text) is None


def test_retrieval_diagnostics_gate_route_returns_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-retrieval-diagnostics-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["diagnostic_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_raw_query"] is False
