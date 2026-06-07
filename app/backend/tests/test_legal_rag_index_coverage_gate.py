import re

import pytest

from services.legal_rag_index_coverage_gate import LegalRagIndexCoverageGateService


def test_index_coverage_gate_builds_metadata_only_plan_rows():
    gate = LegalRagIndexCoverageGateService().build_gate()

    assert gate["id"] == "legal-rag-index-coverage-gate"
    assert gate["status"] == "ready_with_blockers"
    assert gate["summary"]["index_plan_row_count"] == 6
    assert gate["summary"]["ready_plan_count"] == 1
    assert gate["summary"]["review_plan_count"] >= 3
    assert gate["summary"]["blocked_plan_count"] >= 2
    assert gate["summary"]["selected_source_total"] >= 8
    assert gate["summary"]["missing_requested_source_total"] >= 1
    assert gate["summary"]["stale_source_total"] >= 2
    assert gate["summary"]["missing_locator_total"] >= 1
    assert gate["summary"]["forbidden_filter_total"] == 1
    assert gate["summary"]["jurisdiction_gap_count"] >= 1
    assert gate["summary"]["freshness_gap_count"] >= 3
    assert gate["summary"]["cheap_first_continue_count"] >= 1
    assert gate["summary"]["cheap_first_verify_or_escalate_count"] >= 2

    row_ids = {row["id"] for row in gate["index_plan_rows"]}
    assert {
        "index-contract-primary-fresh",
        "index-local-rule-review-due",
        "index-cross-jurisdiction-drift",
        "index-stale-source-excluded",
        "index-missing-locator",
        "index-forbidden-filter",
    } <= row_ids


def test_index_coverage_gate_release_actions_and_linkage_are_explicit():
    gate = LegalRagIndexCoverageGateService().build_gate()
    rows = {row["id"]: row for row in gate["index_plan_rows"]}

    ready = rows["index-contract-primary-fresh"]
    review = rows["index-local-rule-review-due"]
    locator_gap = rows["index-missing-locator"]
    forbidden = rows["index-forbidden-filter"]

    assert ready["index_binding_status"] == "ready"
    assert ready["release_action"] == "allow_retrieval_plan"
    assert ready["source_coverage_status"] == "ready"
    assert ready["locator_status"] == "ready"
    assert review["release_action"] == "review_index_plan"
    assert "freshness:review_due" in review["reason_codes"]
    assert locator_gap["index_binding_status"] == "blocked"
    assert locator_gap["release_action"] == "block_retrieval_plan"
    assert "retrieval_locator_missing" in locator_gap["reason_codes"]
    assert forbidden["filter_validation_status"] == "blocked"
    assert "forbidden_query_filter_present" in forbidden["reason_codes"]
    assert forbidden["cheap_first_action"]["decision"] == "stop"
    assert forbidden["cheap_first_action"]["recommended_model_alias"] == "manual_review_only"

    for row in gate["index_plan_rows"]:
        assert "legal-rag-index-binding" in row["linked_gate_ids"]
        assert "legal-rag-retrieval-diagnostics-gate" in row["linked_gate_ids"]
        assert "legal-rag-retrieval-observation-gate" in row["linked_gate_ids"]
        assert "legal-rag-authority-citation-gate" in row["linked_gate_ids"]
        assert row["cheap_first_action"]["model_called"] is False
        assert row["cheap_first_action"]["gateway_called"] is False
        assert row["privacy_boundary"]["source_ids_returned"] is False
        assert row["privacy_boundary"]["raw_query_returned"] is False
        assert row["privacy_boundary"]["retrieved_context_returned"] is False
        assert row["privacy_boundary"]["raw_legal_text_returned"] is False
        assert row["privacy_boundary"]["credentials_returned"] is False


def test_index_coverage_gate_claim_privacy_and_contract_boundaries_are_safe():
    gate = LegalRagIndexCoverageGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["dataset_downloaded"] is False
    assert gate["summary"]["source_ids_returned"] is False
    assert gate["claim_boundary"]["legal_advice_claimed"] is False
    assert gate["claim_boundary"]["retrieval_quality_claimed"] is False
    assert gate["claim_boundary"]["index_quality_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_retrieved_context"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert "raw_legal_text" in gate["input_contract"]["raw_text_fields_ignored"]
    assert "gateway_response" in gate["input_contract"]["raw_text_fields_ignored"]
    assert gate["index_plan_policy"]["blocks_on_forbidden_query_filters"] is True
    assert gate["index_plan_policy"]["review_due_sources_require_reviewer_review"] is True
    assert gate["index_plan_policy"]["premium_exception_default_allowed"] is False
    assert gate["index_plan_policy"]["cheap_first_default"] is True

    text = str(gate)
    assert "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK" not in text
    assert "RAW_CONTEXT_SHOULD_NOT_LEAK" not in text
    assert "client@example.invalid" not in text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", text) is None


def test_index_coverage_gate_route_returns_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-index-coverage-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["index_plan_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_source_ids"] is False
    assert payload["data"]["privacy_boundary"]["returns_raw_legal_text"] is False


@pytest.mark.parametrize("filter_status", ["blocked", "fail", "failed", "invalid", "error", "rejected"])
def test_index_coverage_gate_blocks_failed_filter_validation_statuses(filter_status):
    gate = LegalRagIndexCoverageGateService().build_gate(
        [
            {
                "id": f"filter-{filter_status}",
                "query_intent": "contract_clause",
                "filter_validation_status": filter_status,
                "candidate_source_count": 3,
                "selected_source_count": 2,
                "requested_source_count": 1,
                "missing_requested_source_count": 0,
                "stale_source_count": 0,
                "missing_locator_count": 0,
                "jurisdiction_status": "matched",
                "freshness_status": "fresh",
                "signals": [],
            }
        ]
    )

    row = gate["index_plan_rows"][0]
    assert row["index_binding_status"] == "blocked"
    assert row["release_action"] == "block_retrieval_plan"
    assert f"filter_validation:{filter_status}" in row["reason_codes"]
    assert row["cheap_first_action"]["requires_operator_review"] is True


def test_index_coverage_gate_accepts_retrieval_plan_contract_rows():
    gate = LegalRagIndexCoverageGateService().build_gate(
        [
            {
                "id": "binding-contract-row",
                "query_intent": "contract_clause",
                "filter_validation_status": "pass",
                "candidate_source_count": 2,
                "selected_source_count": 1,
                "requested_source_count": 1,
                "missing_requested_source_count": 0,
                "stale_source_count": 0,
                "missing_locator_count": 0,
                "jurisdiction_status": "matched",
                "freshness_status": "review_due",
                "signals": ["weak_citations"],
            }
        ]
    )

    row = gate["index_plan_rows"][0]
    assert gate["summary"]["index_plan_row_count"] == 1
    assert row["index_binding_status"] == "review_required"
    assert row["source_coverage_status"] == "ready"
    assert row["locator_status"] == "ready"
    assert row["release_action"] == "review_index_plan"
    assert "freshness:review_due" in row["reason_codes"]
