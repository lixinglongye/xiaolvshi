import re

from services.legal_rag_authority_citation_gate import LegalRagAuthorityCitationGateService


def test_legal_rag_authority_citation_gate_builds_metadata_only_evidence():
    gate = LegalRagAuthorityCitationGateService().build_gate()

    assert gate["status"] == "ready"
    assert gate["id"] == "legal-rag-authority-citation-gate"
    assert gate["summary"]["metadata_only"] is True
    assert gate["summary"]["network_access"] == "disabled"
    assert gate["summary"]["model_calls"] == "disabled"
    assert gate["summary"]["raw_content_storage"] == "forbidden"
    assert gate["summary"]["authority_rule_count"] == 3
    assert gate["summary"]["citation_rule_count"] == 3
    assert gate["summary"]["source_tier_count"] >= 2
    assert gate["summary"]["authority_review_count"] == len(gate["source_rows"])
    assert gate["summary"]["citation_mismatch_count"] == len(gate["citation_mismatch_rows"])
    assert gate["summary"]["retrieval_gap_count"] == len(gate["retrieval_gap_rows"])
    assert "source_id" in gate["required_metadata_fields"]
    assert "authority_tier" in gate["required_metadata_fields"]
    assert "citation_map_source_ids" in gate["required_metadata_fields"]
    assert any(row["status"] == "blocked" for row in gate["source_rows"])
    assert "CN-National" in gate["jurisdiction_counts"]


def test_legal_rag_authority_citation_gate_links_existing_release_evidence():
    gate = LegalRagAuthorityCitationGateService().build_gate()

    assert "legal-rag-selected-source-citation-validation" in gate["release_gate_links"]
    assert "legal-rag-selected-source-request-metadata" in gate["release_gate_links"]
    assert "legal-rag-index-binding" in gate["release_gate_links"]
    assert "frontend-ui-regression-gate" in gate["release_gate_links"]
    assert "app/backend/services/legal_rag_authority_citation_gate.py" in gate["evidence_paths"]
    assert "app/backend/tests/test_legal_rag_authority_citation_gate.py" in gate["evidence_paths"]
    assert "docs/LEGAL_RAG_AUTHORITY_CITATION_GATE.md" in gate["evidence_paths"]
    assert "python -m pytest tests/test_legal_rag_authority_citation_gate.py -q" in gate["validation_commands"]


def test_legal_rag_authority_citation_gate_blocks_unmatched_or_weak_citations():
    gate = LegalRagAuthorityCitationGateService().build_gate()
    authority_rules = {rule["id"]: rule for rule in gate["authority_rules"]}
    citation_rules = {rule["id"]: rule for rule in gate["citation_rules"]}

    assert authority_rules["primary-official-source-preferred"]["severity"] == "blocker"
    assert authority_rules["jurisdiction-and-date-required"]["severity"] == "blocker"
    assert authority_rules["unknown-authority-needs-review"]["severity"] == "review"
    assert citation_rules["citation-source-id-match"]["blocks_release"] is True
    assert citation_rules["no-unsupported-citation-claims"]["blocks_release"] is True
    assert citation_rules["metadata-only-citation-review"]["blocks_release"] is True
    assert "selected_source_ids" in citation_rules["citation-source-id-match"]["evidence_fields"]
    assert "citation_map_source_ids" in citation_rules["citation-source-id-match"]["evidence_fields"]


def test_legal_rag_authority_citation_gate_privacy_boundary_excludes_raw_content():
    gate = LegalRagAuthorityCitationGateService().build_gate()
    payload_text = str(gate)

    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["calls_newapi"] is False
    assert gate["privacy_boundary"]["calls_gemini"] is False
    assert gate["privacy_boundary"]["calls_gateway"] is False
    assert gate["privacy_boundary"]["downloads_datasets"] is False
    assert gate["privacy_boundary"]["stores_raw_legal_text"] is False
    assert gate["privacy_boundary"]["stores_prompt"] is False
    assert gate["privacy_boundary"]["stores_model_output"] is False
    assert gate["privacy_boundary"]["stores_credentials"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_prompts"] is False
    assert gate["privacy_boundary"]["returns_raw_model_output"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert gate["privacy_boundary"]["returns_gateway_payloads"] is False
    assert gate["claim_boundary"]["legal_advice_claimed"] is False
    assert gate["claim_boundary"]["citation_without_source_allowed"] is False
    assert gate["claim_boundary"]["freshness_gap_allowed"] is False
    assert "raw_legal_text" in gate["privacy_boundary"]["forbidden_content_labels"]
    assert "prompt" in gate["privacy_boundary"]["forbidden_content_labels"]
    assert "model_output" in gate["privacy_boundary"]["forbidden_content_labels"]
    assert "credentials" in gate["privacy_boundary"]["forbidden_content_labels"]
    assert re.search(r"\bsk-[A-Za-z0-9]{20,}\b", payload_text) is None


def test_legal_rag_authority_citation_gate_route_returns_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-rag-authority-citation-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "legal-rag-authority-citation-gate"
    assert payload["data"]["privacy_boundary"]["stores_raw_legal_text"] is False
