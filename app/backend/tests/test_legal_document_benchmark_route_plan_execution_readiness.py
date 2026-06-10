import json
import re

from services.legal_document_benchmark_route_plan_execution_readiness import (
    READINESS_ID,
    LegalDocumentBenchmarkRoutePlanExecutionReadinessService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_route_plan_execution_readiness_builds_manual_run_packet():
    packet = LegalDocumentBenchmarkRoutePlanExecutionReadinessService().build_packet()
    gates = {gate["id"]: gate for gate in packet["pre_execution_gates"]}

    assert packet["id"] == READINESS_ID
    assert packet["status"] == "ready"
    assert packet["summary"]["route_plan_status"] == "ready"
    assert packet["summary"]["replay_status"] == "pass"
    assert packet["summary"]["research_alignment_status"] == "ready"
    assert packet["summary"]["manual_execution_ready"] is True
    assert packet["summary"]["maintainer_approval_recorded"] is False
    assert packet["summary"]["benchmark_execution"] == "not_started"
    assert packet["summary"]["model_calls"] == "not_required"
    assert packet["summary"]["network_access"] == "disabled"
    assert packet["manual_run_packet"]["recommended_fixture_limit"] == 3
    assert packet["manual_run_packet"]["max_parallel_model_requests"] == 1
    assert packet["manual_run_packet"]["default_model_strategy"] == "cheap_first_gemini"
    assert packet["manual_run_packet"]["records_approval"] is False
    assert packet["manual_run_packet"]["executes_benchmark"] is False
    assert gates["route-plan-not-blocked"]["status"] == "pass"
    assert gates["replay-scenarios-pass"]["status"] == "pass"
    assert gates["premium-block-replayed"]["status"] == "pass"
    assert gates["research-alignment-ready"]["status"] == "pass"
    assert gates["metadata-only-boundary"]["status"] == "pass"
    assert packet["privacy_boundary"]["calls_model"] is False
    assert packet["privacy_boundary"]["downloads_datasets"] is False
    assert packet["privacy_boundary"]["returns_raw_fixture_snippets"] is False
    assert packet["privacy_boundary"]["returns_credentials"] is False
    assert packet["claim_boundary"]["benchmark_executed"] is False
    assert packet["claim_boundary"]["maintainer_approval_claimed"] is False


def test_route_plan_execution_readiness_blocks_premium_override_plan():
    packet = LegalDocumentBenchmarkRoutePlanExecutionReadinessService().build_packet(
        {
            "route_plan": {
                "case_route_overrides": {
                    "ldoc-contract-review-mini": {
                        "primary_task": "review",
                        "primary_model": "gemini-2.5-pro",
                        "allow_over_budget_model": True,
                    }
                }
            }
        }
    )
    gates = {gate["id"]: gate for gate in packet["pre_execution_gates"]}

    assert packet["status"] == "blocked"
    assert packet["summary"]["route_plan_status"] == "blocked"
    assert packet["summary"]["manual_execution_ready"] is False
    assert "route-plan-not-blocked" in packet["blocking_gate_ids"]
    assert gates["route-plan-not-blocked"]["status"] == "fail"
    assert packet["source_summaries"]["route_plan"]["premium_primary_case_count"] == 1
    assert packet["manual_run_packet"]["next_actions"][0].startswith("Resolve blocking readiness gates")


def test_route_plan_execution_readiness_blocks_replay_drift():
    packet = LegalDocumentBenchmarkRoutePlanExecutionReadinessService().build_packet(
        {
            "route_plan_replay": {
                "scenarios": [
                    {
                        "id": "contract-review-default-balanced",
                        "case_id": "ldoc-contract-review-mini",
                        "expected_plan_status": "ready",
                        "expected_primary_task": "review",
                        "expected_resolved_model": "gemini-2.5-pro",
                        "expected_cost_tier": "premium",
                        "expected_route_band": "blocked_premium_default",
                        "expected_routed_to_recommended": False,
                        "expected_blocking_check_ids": ["no-premium-primary-defaults"],
                    }
                ]
            }
        }
    )

    assert packet["status"] == "blocked"
    assert packet["summary"]["replay_status"] == "fail"
    assert packet["summary"]["research_alignment_status"] == "blocked"
    assert "replay-scenarios-pass" in packet["blocking_gate_ids"]
    assert "research-alignment-ready" in packet["blocking_gate_ids"]


def test_route_plan_execution_readiness_keeps_sensitive_payload_out_of_output():
    blocked_model_name = "s" + "k-" + ("z" * 28)
    packet = LegalDocumentBenchmarkRoutePlanExecutionReadinessService().build_packet(
        {
            "route_plan": {
                "case_route_overrides": {
                    "ldoc-contract-review-mini": {
                        "primary_task": "review",
                        "primary_model": blocked_model_name,
                        "allow_over_budget_model": True,
                    }
            }
        },
            "operator_ref": "operator-example",
            "note": "secret raw legal text should not appear",
        }
    )
    serialized = json.dumps(packet, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert "secret raw legal text" not in serialized
    assert packet["privacy_boundary"]["returns_raw_scenario_payload"] is False
    assert packet["privacy_boundary"]["returns_credentials"] is False
    assert packet["claim_boundary"]["public_benchmark_score_claimed"] is False


def test_route_plan_execution_readiness_route_returns_packet():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-readiness")
    assert template_response.status_code == 200
    template_payload = template_response.json()
    assert template_payload["success"] is True
    assert template_payload["data"]["id"] == READINESS_ID
    assert template_payload["data"]["status"] == "ready"
    assert template_payload["data"]["summary"]["manual_execution_ready"] is True

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-readiness",
        json={"route_plan_replay": {}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["source_summaries"]["route_plan_replay"]["status"] == "pass"
    assert payload["data"]["privacy_boundary"]["calls_model"] is False
