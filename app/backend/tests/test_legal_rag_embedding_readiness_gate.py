import re

import pytest

from services.legal_rag_embedding_readiness_gate import LegalRagEmbeddingReadinessGateService


def test_embedding_readiness_gate_links_gemini_embedding_to_legal_rag_gates():
    gate = LegalRagEmbeddingReadinessGateService().build_gate()

    assert gate["id"] == "legal-rag-embedding-readiness-gate"
    assert gate["status"] == "ready_with_blockers"
    assert gate["summary"]["readiness_row_count"] == 4
    assert gate["summary"]["ready_row_count"] == 2
    assert gate["summary"]["review_row_count"] == 1
    assert gate["summary"]["blocked_row_count"] == 1
    assert gate["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert gate["summary"]["embedding_default_canonical_model"] == "gemini-embedding-001"
    assert gate["summary"]["text_embedding_ready_count"] == 1
    assert gate["summary"]["multimodal_review_required_count"] == 1
    assert gate["summary"]["index_plan_row_count"] == 6
    assert gate["summary"]["diagnostic_row_count"] == 6

    assert gate["linked_gate_summary"]["modelops_gemini_embedding_cheap_first_preflight"] == "review_required"
    assert gate["linked_gate_summary"]["legal_rag_index_coverage_gate"] == "ready_with_blockers"
    assert gate["linked_gate_summary"]["legal_rag_retrieval_diagnostics_gate"] == "ready_with_blockers"


def test_embedding_readiness_gate_rows_explain_release_actions():
    gate = LegalRagEmbeddingReadinessGateService().build_gate()
    rows = {row["id"]: row for row in gate["readiness_rows"]}

    text_index = rows["legal-rag-text-index"]
    batch_index = rows["source-deduping-batch-index"]
    multimodal = rows["multimodal-evidence-index"]
    empty_coverage = rows["empty-index-coverage-block"]

    assert text_index["default_model"] == "gemini-embedding-001"
    assert text_index["readiness_status"] == "ready"
    assert text_index["release_action"] == "allow_text_embedding_preflight"
    assert "text_embedding_default_ready" in text_index["reason_codes"]
    assert batch_index["release_action"] == "allow_batch_embedding_preflight"
    assert multimodal["default_model"] == "gemini-embedding-2"
    assert multimodal["readiness_status"] == "review_required"
    assert multimodal["release_action"] == "review_multimodal_embedding_route"
    assert "explicit_multimodal_embedding_review_required" in multimodal["reason_codes"]
    assert empty_coverage["readiness_status"] == "blocked"
    assert empty_coverage["release_action"] == "block_embedding_index_write"

    for row in gate["readiness_rows"]:
        assert "modelops-gemini-embedding-cheap-first-preflight" in row["linked_gate_ids"]
        assert "legal-rag-index-coverage-gate" in row["linked_gate_ids"]
        assert "legal-rag-retrieval-diagnostics-gate" in row["linked_gate_ids"]
        assert row["privacy_boundary"]["source_ids_returned"] is False
        assert row["privacy_boundary"]["raw_query_returned"] is False
        assert row["privacy_boundary"]["raw_legal_text_returned"] is False
        assert row["privacy_boundary"]["embedding_vectors_returned"] is False
        assert row["privacy_boundary"]["credentials_returned"] is False


def test_embedding_readiness_gate_claim_privacy_and_contract_boundaries_are_safe():
    gate = LegalRagEmbeddingReadinessGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["index_written"] is False
    assert gate["summary"]["raw_embedding_vectors_included"] is False
    assert gate["summary"]["source_ids_returned"] is False
    assert gate["readiness_policy"]["index_write_allowed"] is False
    assert gate["claim_boundary"]["legal_advice_claimed"] is False
    assert gate["claim_boundary"]["embedding_quality_claimed"] is False
    assert gate["claim_boundary"]["index_quality_claimed"] is False
    assert gate["claim_boundary"]["automatic_index_write_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["calls_gemini"] is False
    assert gate["privacy_boundary"]["writes_index"] is False
    assert "embedding_vector" in gate["input_contract"]["forbidden_fields_ignored"]
    assert "raw_legal_text" in gate["input_contract"]["forbidden_fields_ignored"]

    text = str(gate)
    assert "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK" not in text
    assert "RAW_EMBEDDING_VECTOR_SHOULD_NOT_LEAK" not in text
    assert "client@example.invalid" not in text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", text) is None


def test_embedding_readiness_gate_checks_surface_review_and_blockers():
    gate = LegalRagEmbeddingReadinessGateService().build_gate()
    checks = {check["id"]: check for check in gate["checks"]}

    assert checks["cheap-first-text-embedding-default"]["status"] == "pass"
    assert checks["cheap-first-text-embedding-default"]["evidence"] == ["gemini-embedding-001"]
    assert checks["index-coverage-linked"]["status"] == "warn"
    assert checks["retrieval-diagnostics-linked"]["status"] == "warn"
    assert checks["multimodal-review-boundary"]["status"] == "warn"
    assert checks["metadata-only-boundary"]["status"] == "pass"
    assert "multimodal-evidence-index" in checks["multimodal-review-boundary"]["evidence"]


def test_embedding_readiness_gate_route_returns_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-readiness-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False
    assert payload["data"]["privacy_boundary"]["writes_index"] is False
