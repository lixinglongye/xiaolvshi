import json
import re

from services.legal_document_benchmark_route_plan_execution_claim_gate import (
    CLAIM_GATE_ID,
    LegalDocumentBenchmarkRoutePlanExecutionClaimGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|access[_-]?token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def _planned_observation(case_id: str, *, phase: str = "primary") -> dict:
    service = LegalDocumentBenchmarkRoutePlanExecutionClaimGateService()
    route_plan = service.review_packet_service.readiness_service.route_plan_service.build_plan()
    row = {item["case_id"]: item for item in route_plan["case_route_rows"]}[case_id]
    expected_model = row["precheck_route"]["model"] if phase == "precheck" else row["primary_route"]["resolved_model"]
    return {
        "case_id": case_id,
        "phase": phase,
        "observed_model": expected_model,
        "observed_status": "success",
        "observed_input_tokens": 1200,
        "observed_output_tokens": 256,
        "observed_cost_usd": 0.0002,
        "latency_ms": 1200,
    }


def test_route_plan_execution_claim_gate_blocks_default_overclaims():
    gate = LegalDocumentBenchmarkRoutePlanExecutionClaimGateService().evaluate()
    claim_statuses = {tuple(check["detected_claim_types"]): check for check in gate["claim_checks"]}

    assert gate["id"] == CLAIM_GATE_ID
    assert gate["status"] == "blocked"
    assert gate["summary"]["claim_count"] == 3
    assert gate["summary"]["review_packet_status"] == "review_required"
    assert gate["summary"]["raw_claim_text_echoed"] is False
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["benchmark_executed"] is False
    assert gate["privacy_boundary"]["raw_claim_text_included"] is False
    assert gate["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert claim_statuses[("public_benchmark_score",)]["status"] == "blocked"
    assert claim_statuses[("approval_recorded",)]["status"] == "blocked"
    assert not SENSITIVE_PATTERN.search(json.dumps(gate, ensure_ascii=False))


def test_route_plan_execution_claim_gate_allows_metadata_claim_when_packet_ready():
    gate = LegalDocumentBenchmarkRoutePlanExecutionClaimGateService().evaluate(
        {
            "observations": [
                _planned_observation("ldoc-contract-review-mini"),
                _planned_observation("ldoc-civil-complaint-mini", phase="precheck"),
            ],
            "claims": [
                "Repository-backed metadata-only route-plan execution review packet supports sanitized release evidence."
            ],
        }
    )
    check = gate["claim_checks"][0]

    assert gate["status"] == "ready"
    assert gate["summary"]["review_packet_status"] == "ready"
    assert gate["summary"]["ready_claim_count"] == 1
    assert check["allowed"] is True
    assert check["release_action"] == "allow_metadata_only_claim"
    assert check["detected_claim_types"] == ["metadata_only_execution_evidence"]


def test_route_plan_execution_claim_gate_holds_metadata_claim_until_packet_ready():
    gate = LegalDocumentBenchmarkRoutePlanExecutionClaimGateService().evaluate(
        {
            "claims": [
                "Repository-backed metadata-only route-plan execution review packet supports sanitized release evidence."
            ]
        }
    )
    check = gate["claim_checks"][0]

    assert gate["status"] == "review_required"
    assert gate["summary"]["review_packet_status"] == "review_required"
    assert check["status"] == "review_required"
    assert check["allowed"] is False
    assert "review_packet_not_ready" in check["reason_codes"]
    assert check["release_action"] == "hold_until_review_packet_ready"


def test_route_plan_execution_claim_gate_blocks_forbidden_claims_without_echoing_values():
    blocked_key_shape = "s" + "k-" + ("C" * 28)
    private_contact = "client" + "@" + "example.test"
    gate = LegalDocumentBenchmarkRoutePlanExecutionClaimGateService().evaluate(
        {
            "observations": [_planned_observation("ldoc-contract-review-mini")],
            "claims": [
                f"Live Gemini provider run achieved a LegalBench score; maintainer approved {blocked_key_shape} {private_contact}."
            ],
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)
    check = gate["claim_checks"][0]

    assert gate["status"] == "blocked"
    assert check["status"] == "blocked"
    assert "forbidden_public_benchmark_score" in check["reason_codes"]
    assert "forbidden_live_provider_execution" in check["reason_codes"]
    assert "forbidden_approval_recorded" in check["reason_codes"]
    assert "sensitive_material_dropped" in check["reason_codes"]
    assert blocked_key_shape not in serialized
    assert private_contact not in serialized
    assert "Live Gemini provider run" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_route_plan_execution_claim_gate_route_returns_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-claim-gate"
    )
    assert template_response.status_code == 200
    assert template_response.json()["data"]["id"] == CLAIM_GATE_ID
    assert template_response.json()["data"]["status"] == "blocked"

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-claim-gate",
        json={
            "observations": [_planned_observation("ldoc-contract-review-mini")],
            "claims": [
                "Repository-backed metadata-only route-plan execution review packet supports sanitized release evidence."
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["summary"]["model_called"] is False
    assert payload["data"]["summary"]["raw_claim_text_echoed"] is False
