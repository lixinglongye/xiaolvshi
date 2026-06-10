import json
import re

from services.legal_document_benchmark_route_plan_replay import (
    REPLAY_ID,
    LegalDocumentBenchmarkRoutePlanReplayService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_legal_document_benchmark_route_plan_replay_runs_default_scenarios_metadata_only():
    replay = LegalDocumentBenchmarkRoutePlanReplayService().run_replay()
    scenarios = {item["id"]: item for item in replay["replay_results"]}

    assert replay["id"] == REPLAY_ID
    assert replay["status"] == "pass"
    assert replay["summary"]["scenario_count"] == 5
    assert replay["summary"]["pass_count"] == 5
    assert replay["summary"]["fail_count"] == 0
    assert replay["summary"]["blocked_plan_count"] == 1
    assert replay["summary"]["routed_to_recommended_count"] == 1
    assert replay["summary"]["premium_block_count"] == 1
    assert replay["summary"]["model_calls"] == "not_required"
    assert replay["summary"]["network_access"] == "disabled"
    assert replay["privacy_boundary"]["model_calls"] is False
    assert replay["privacy_boundary"]["network_access"] is False
    assert replay["privacy_boundary"]["returns_credentials"] is False
    assert replay["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert scenarios["unapproved-premium-routes-to-recommended"]["actual"]["resolved_model"] == "gemini-2.5-flash"
    assert scenarios["unapproved-premium-routes-to-recommended"]["actual"]["routed_to_recommended_model"] is True
    assert scenarios["approved-premium-remains-blocked"]["actual"]["plan_status"] == "blocked"
    assert "no-premium-primary-defaults" in scenarios["approved-premium-remains-blocked"]["actual"]["blocking_check_ids"]
    assert scenarios["legal-opinion-grounded-flash-lite"]["actual"]["resolved_model"] == "gemini-3.1-flash-lite"


def test_legal_document_benchmark_route_plan_replay_catches_unexpected_policy():
    replay = LegalDocumentBenchmarkRoutePlanReplayService().run_replay(
        {
            "scenarios": [
                {
                    "id": "wrong-expected-route",
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
    )
    result = replay["replay_results"][0]

    assert replay["status"] == "fail"
    assert replay["summary"]["fail_count"] == 1
    assert result["status"] == "fail"
    assert {"resolved-model", "cost-tier", "route-band", "blocking-checks"} <= set(result["failures"])
    assert "route-plan-replay-scenarios-pass" in replay["blocking_check_ids"]


def test_legal_document_benchmark_route_plan_replay_rejects_sensitive_scenario_values():
    secret = "s" + "k-" + ("z" * 28)
    replay = LegalDocumentBenchmarkRoutePlanReplayService().run_replay(
        {
            "scenarios": [
                {
                    "id": "reviewer@example.com",
                    "case_id": "ldoc-civil-complaint-mini",
                    "override_primary_task": "document-generation",
                    "override_primary_model": secret,
                    "expected_plan_status": "ready",
                    "expected_primary_task": "document-generation",
                    "expected_resolved_model": "gemini-2.5-flash",
                    "expected_cost_tier": "low",
                    "expected_route_band": "balanced_after_cheap_precheck",
                    "note": "secret raw legal text should not appear",
                }
            ],
            "operator_email": "operator@example.com",
        }
    )
    serialized = json.dumps(replay, ensure_ascii=False)
    result = replay["replay_results"][0]

    assert not SENSITIVE_PATTERN.search(serialized)
    assert replay["summary"]["rejected_sensitive_scenario_count"] == 1
    assert replay["privacy_boundary"]["raw_scenario_payload_echoed"] is False
    assert result["id"].startswith("submitted-route-plan-replay")
    assert result["scenario"]["override_primary_model"] is None
    assert result["scenario"]["rationale"] == (
        "Submitted metadata-only route-plan replay scenario; raw rationale is not echoed."
    )
    assert "secret raw legal text" not in serialized


def test_legal_document_benchmark_route_plan_replay_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/legal-review-benchmark/document-route-plan/replay")
    assert template_response.status_code == 200
    template_payload = template_response.json()
    assert template_payload["success"] is True
    assert template_payload["data"]["id"] == REPLAY_ID
    assert template_payload["data"]["status"] == "pass"
    assert template_payload["data"]["summary"]["premium_block_count"] == 1

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/replay",
        json={
            "scenarios": [
                {
                    "id": "submitted-premium-block",
                    "case_id": "ldoc-contract-review-mini",
                    "override_primary_task": "review",
                    "override_primary_model": "gemini-2.5-pro",
                    "override_approval": True,
                    "expected_plan_status": "blocked",
                    "expected_primary_task": "review",
                    "expected_resolved_model": "gemini-2.5-pro",
                    "expected_cost_tier": "premium",
                    "expected_route_band": "blocked_premium_default",
                    "expected_routed_to_recommended": False,
                    "expected_blocking_check_ids": ["no-premium-primary-defaults"],
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "pass"
    assert payload["data"]["summary"]["scenario_count"] == 1
    assert payload["data"]["summary"]["blocked_plan_count"] == 1
    assert payload["data"]["privacy_boundary"]["model_calls"] is False
