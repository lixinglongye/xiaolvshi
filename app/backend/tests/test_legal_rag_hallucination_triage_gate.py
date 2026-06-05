import re

import pytest

from services.legal_rag_hallucination_triage_gate import LegalRagHallucinationTriageGateService


def test_hallucination_triage_gate_maps_failure_fixtures_to_release_blockers():
    gate = LegalRagHallucinationTriageGateService().build_gate()

    assert gate["id"] == "legal-rag-hallucination-triage-gate"
    assert gate["status"] == "ready_with_blockers"
    assert gate["summary"]["triage_row_count"] == 6
    assert gate["summary"]["fixture_case_count"] == 6
    assert gate["summary"]["taxonomy_count"] == 6
    assert gate["summary"]["blocker_row_count"] >= 5
    assert gate["summary"]["critical_row_count"] >= 2
    assert gate["summary"]["high_row_count"] >= 3
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["dataset_downloaded"] is False

    labels = set(gate["failure_label_counts"])
    assert {
        "missing_citation",
        "stale_regulation",
        "jurisdiction_mismatch",
        "unsupported_conclusion",
        "hallucinated_article",
        "conflicting_facts",
    }.issubset(labels)
    assert all("release_action" in row for row in gate["triage_rows"])


def test_hallucination_triage_gate_links_authority_rows_without_raw_context():
    gate = LegalRagHallucinationTriageGateService().build_gate()
    hallucinated = next(row for row in gate["triage_rows"] if row["case_id"] == "rag-hallucinated-article-small")
    unsupported = next(row for row in gate["triage_rows"] if row["case_id"] == "rag-unsupported-conclusion-small")

    assert hallucinated["severity"] == "critical"
    assert hallucinated["block_release"] is True
    assert "remove_hallucinated_citation" in hallucinated["reviewer_actions"]
    assert hallucinated["linked_authority_row_ids"]
    assert unsupported["linked_authority_row_ids"]
    assert unsupported["release_action"] == "block_client_delivery"


def test_hallucination_triage_gate_claim_and_privacy_boundaries_are_explicit():
    gate = LegalRagHallucinationTriageGateService().build_gate()

    assert gate["claim_boundary"]["hallucination_free_claimed"] is False
    assert gate["claim_boundary"]["legal_answer_accuracy_claimed"] is False
    assert gate["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_user_question"] is False
    assert gate["privacy_boundary"]["returns_retrieved_context"] is False
    assert gate["privacy_boundary"]["returns_unsafe_answer"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert any("hallucination-free" in claim for claim in gate["claim_boundary"]["forbidden_claims"])
    assert any("test_legal_rag_hallucination_triage_gate.py" in command for command in gate["validation_commands"])

    text = str(gate)
    assert "Can the claimant still file" not in text
    assert "The claimant can still file" not in text
    assert "An appeal must be filed within 15 days after service of judgment." not in text
    assert "Article 99" not in text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", text) is None


def test_hallucination_triage_gate_route_returns_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-hallucination-triage-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["triage_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_retrieved_context"] is False
