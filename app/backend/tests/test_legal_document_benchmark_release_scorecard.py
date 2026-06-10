import json
import re

from services.legal_document_benchmark_release_scorecard import (
    SCORECARD_ID,
    LegalDocumentBenchmarkReleaseScorecardService,
)


SENSITIVE_PATTERN = re.compile(
    r"(?<![A-Za-z])sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|access[_-]?token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def _passing_document_outputs(service: LegalDocumentBenchmarkReleaseScorecardService) -> dict[str, dict]:
    suite = service.suite_service.build_suite()
    outputs: dict[str, dict] = {}
    for case in suite["benchmark_cases"]:
        outputs[case["id"]] = {
            "sections": list(case["required_sections"]),
            "citations": list(case["expected_citations"]),
            "risk_labels": list(case["expected_risk_labels"]),
            "pii_findings": [],
        }
    return outputs


def _passing_fact_outputs(service: LegalDocumentBenchmarkReleaseScorecardService) -> dict[str, dict]:
    suite = service.fact_service.build_suite()
    outputs: dict[str, dict] = {}
    for case in suite["benchmark_cases"]:
        outputs[case["id"]] = {
            "amounts": {
                item["id"]: item["value"]
                for item in case["amount_expectations"]
            },
            "deadlines": {
                item["id"]: item["value"]
                for item in case["deadline_expectations"]
            },
            "facts": list(case["required_fact_ids"]),
        }
    return outputs


def _planned_observation(service: LegalDocumentBenchmarkReleaseScorecardService, case_id: str, *, phase: str = "primary") -> dict:
    route_plan = (
        service.execution_claim_gate_service.review_packet_service.readiness_service.route_plan_service.build_plan()
    )
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


def test_legal_document_benchmark_release_scorecard_defaults_to_review_required():
    scorecard = LegalDocumentBenchmarkReleaseScorecardService().build_scorecard()

    assert scorecard["id"] == SCORECARD_ID
    assert scorecard["status"] == "review_required"
    assert scorecard["summary"]["component_count"] == 8
    assert scorecard["summary"]["blocked_component_count"] == 0
    assert scorecard["summary"]["model_called"] is False
    assert scorecard["summary"]["gateway_called"] is False
    assert scorecard["summary"]["benchmark_executed"] is False
    assert scorecard["summary"]["release_claim_ready"] is False
    assert "document_output_evaluation" in scorecard["review_component_ids"]
    assert "fact_consistency_evaluation" in scorecard["review_component_ids"]
    assert "execution_claim_gate" in scorecard["review_component_ids"]
    assert scorecard["release_decision"]["requires_manual_review"] is True
    assert scorecard["release_decision"]["can_claim_public_benchmark_scores"] is False
    assert scorecard["privacy_boundary"]["returns_raw_document_text"] is False
    assert scorecard["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(scorecard, ensure_ascii=False))


def test_legal_document_benchmark_release_scorecard_ready_with_passing_local_evidence():
    service = LegalDocumentBenchmarkReleaseScorecardService()
    scorecard = service.build_scorecard(
        {
            "document_outputs": _passing_document_outputs(service),
            "fact_outputs": _passing_fact_outputs(service),
            "observations": [
                _planned_observation(service, "ldoc-contract-review-mini"),
                _planned_observation(service, "ldoc-civil-complaint-mini", phase="precheck"),
            ],
            "execution_claims": [
                "Repository-backed metadata-only route-plan execution review packet supports sanitized release evidence."
            ],
        }
    )

    assert scorecard["status"] == "ready"
    assert scorecard["summary"]["ready_component_count"] == scorecard["summary"]["component_count"]
    assert scorecard["summary"]["scorecard_score"] == 100
    assert scorecard["summary"]["release_claim_ready"] is True
    assert scorecard["blocking_component_ids"] == []
    assert scorecard["review_component_ids"] == []
    assert scorecard["release_decision"]["can_reference_local_synthetic_coverage"] is True
    assert scorecard["release_decision"]["can_reference_execution_review_packet"] is True
    assert all(row["release_action"] == "attach_to_release_scorecard" for row in scorecard["component_rows"])


def test_legal_document_benchmark_release_scorecard_blocks_overclaims_without_echoing_values():
    blocked_key_shape = "s" + "k-" + ("D" * 28)
    private_contact = "client" + "@" + "example.test"
    scorecard = LegalDocumentBenchmarkReleaseScorecardService().build_scorecard(
        {
            "coverage_claims": [
                f"All legal documents are validated on real client documents with LegalBench scores {blocked_key_shape}."
            ],
            "execution_claims": [
                f"Live Gemini provider run achieved public benchmark score and maintainer approved {private_contact}."
            ],
        }
    )
    serialized = json.dumps(scorecard, ensure_ascii=False)

    assert scorecard["status"] == "blocked"
    assert "coverage_claim_policy" in scorecard["blocking_component_ids"]
    assert "execution_claim_gate" in scorecard["blocking_component_ids"]
    assert scorecard["release_decision"]["can_claim_live_provider_execution"] is False
    assert scorecard["release_decision"]["can_claim_production_legal_quality"] is False
    assert blocked_key_shape not in serialized
    assert private_contact not in serialized
    assert "Live Gemini provider run" not in serialized
    assert "All legal documents" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_legal_document_benchmark_release_scorecard_route_returns_scorecard():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-review-benchmark/document-release-scorecard")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == SCORECARD_ID
    assert payload["data"]["status"] == "review_required"

    service = LegalDocumentBenchmarkReleaseScorecardService()
    ready_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-release-scorecard",
        json={
            "document_outputs": _passing_document_outputs(service),
            "fact_outputs": _passing_fact_outputs(service),
            "observations": [
                _planned_observation(service, "ldoc-contract-review-mini"),
                _planned_observation(service, "ldoc-civil-complaint-mini", phase="precheck"),
            ],
            "execution_claims": [
                "Repository-backed metadata-only route-plan execution review packet supports sanitized release evidence."
            ],
        },
    )

    assert ready_response.status_code == 200
    ready_payload = ready_response.json()
    assert ready_payload["success"] is True
    assert ready_payload["data"]["status"] == "ready"
    assert ready_payload["data"]["summary"]["model_called"] is False
