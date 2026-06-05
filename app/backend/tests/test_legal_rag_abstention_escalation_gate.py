import re

import pytest

from services.legal_rag_abstention_escalation_gate import LegalRagAbstentionEscalationGateService


def test_abstention_escalation_gate_joins_rag_gates_into_answer_modes():
    gate = LegalRagAbstentionEscalationGateService().build_gate()

    assert gate["id"] == "legal-rag-abstention-escalation-gate"
    assert gate["status"] == "ready_with_blockers"
    assert gate["summary"]["decision_row_count"] == 7
    assert gate["summary"]["answer_count"] == 1
    assert gate["summary"]["answer_with_warning_count"] == 1
    assert gate["summary"]["abstain_count"] == 1
    assert gate["summary"]["ask_clarification_count"] == 2
    assert gate["summary"]["lawyer_review_count"] == 1
    assert gate["summary"]["premium_exception_count"] == 1
    assert gate["summary"]["blocker_count"] >= 5
    assert gate["summary"]["hallucination_blocker_count"] >= 5
    assert gate["summary"]["authority_blocker_count"] >= 3
    assert gate["summary"]["min_evidence_sufficiency_score"] < 55

    modes = {row["answer_mode"] for row in gate["decision_rows"]}
    assert {
        "answer",
        "answer_with_warning",
        "abstain",
        "ask_clarification",
        "lawyer_review",
        "premium_exception",
    } == modes


def test_abstention_escalation_gate_routes_blockers_without_model_calls():
    gate = LegalRagAbstentionEscalationGateService().build_gate()
    rows = {row["case_id"]: row for row in gate["decision_rows"]}

    assert rows["rag-hallucinated-article-small"]["answer_mode"] == "abstain"
    assert rows["rag-hallucinated-article-small"]["abstain_required"] is True
    assert rows["rag-hallucinated-article-small"]["citation_grounding_status"] == "ungrounded"
    assert rows["rag-unsupported-conclusion-small"]["answer_mode"] == "premium_exception"
    assert rows["rag-unsupported-conclusion-small"]["premium_exception_required"] is True
    assert rows["rag-stale-regulation-small"]["answer_mode"] == "lawyer_review"
    assert rows["rag-jurisdiction-mismatch-small"]["clarification_required"] is True
    assert rows["authority-ready-metadata"]["release_action"] == "allow_answer"
    assert rows["authority-ready-metadata"]["cheap_first_route"]["starts_cheap"] is True

    for row in gate["decision_rows"]:
        assert "legal-rag-abstention-escalation-gate" in row["linked_gate_ids"]
        assert row["cheap_first_route"]["model_called"] is False
        assert row["cheap_first_route"]["gateway_called"] is False
        assert row["privacy_boundary"]["retrieved_context_returned"] is False
        assert row["privacy_boundary"]["unsafe_answer_returned"] is False


def test_abstention_escalation_gate_claim_and_privacy_boundaries_are_explicit():
    gate = LegalRagAbstentionEscalationGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["raw_retrieved_context_included"] is False
    assert gate["summary"]["raw_legal_text_included"] is False
    assert gate["claim_boundary"]["legal_advice_claimed"] is False
    assert gate["claim_boundary"]["hallucination_free_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_user_question"] is False
    assert gate["privacy_boundary"]["returns_retrieved_context"] is False
    assert gate["privacy_boundary"]["returns_unsafe_answer"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert gate["escalation_policy"]["gateway_call_allowed"] is False
    assert gate["escalation_policy"]["config_write_allowed"] is False
    assert gate["escalation_policy"]["default_model_strategy"] == "cheap_first_metadata_only"

    text = str(gate)
    assert "Can the claimant still file" not in text
    assert "The claimant can still file" not in text
    assert "An appeal must be filed within 15 days after service of judgment." not in text
    assert "Article 99" not in text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", text) is None


def test_abstention_escalation_gate_route_returns_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-abstention-escalation-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["decision_row_count"] == 7
    assert payload["data"]["privacy_boundary"]["returns_retrieved_context"] is False
