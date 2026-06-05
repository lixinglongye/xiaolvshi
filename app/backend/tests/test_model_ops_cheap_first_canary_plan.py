import json
import re

from services.model_ops_cheap_first_canary_plan import ModelOpsCheapFirstCanaryPlanService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _signals() -> dict:
    return {
        "cheap_first_release_decision": {"status": "pass"},
        "route_guardrails": {"status": "pass"},
        "cost_guardrails": {"status": "pass"},
        "route_telemetry_ops_summary": {"status": "pass"},
        "default_change_queue": {
            "status": "ready",
            "queue_items": [
                {
                    "id": "default-change-fast",
                    "task": "fast",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "requires_change": True,
                    "requires_operator_review": False,
                    "queue_status": "ready",
                    "reason_codes": ["ready-after-standard-validation"],
                },
                {
                    "id": "default-change-ocr",
                    "task": "ocr",
                    "env_var": "APP_OCR_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "requires_change": False,
                    "requires_operator_review": False,
                    "queue_status": "no_action",
                    "reason_codes": ["runtime-default-aligned"],
                },
            ],
        },
    }


def test_canary_plan_builds_batch_steps_for_ready_default_changes():
    plan = ModelOpsCheapFirstCanaryPlanService().build_plan(_signals())
    ready_steps = [step for step in plan["canary_steps"] if step["source_queue_item_id"] == "default-change-fast"]

    assert plan["status"] == "ready"
    assert [step["batch_percentage"] for step in ready_steps] == [1, 10, 25]
    assert ready_steps[0]["step_status"] == "ready"
    assert ready_steps[1]["step_status"] == "pending_after_prior_pass"
    assert ready_steps[0]["holdout_percentage"] == 99
    assert ready_steps[0]["requires_operator_review"] is True
    assert "route-failure-rate" in ready_steps[0]["rollback_trigger_ids"]
    assert plan["summary"]["canary_required_count"] == 1
    assert plan["summary"]["configuration_written"] is False
    assert plan["privacy_boundary"]["network_called"] is False
    assert plan["claim_boundary"]["automatic_canary_rollout_claimed"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(plan, ensure_ascii=False))


def test_canary_plan_keeps_review_queue_items_out_of_traffic_steps():
    signals = _signals()
    signals["default_change_queue"]["queue_items"][0]["queue_status"] = "review_required"
    signals["default_change_queue"]["queue_items"][0]["reason_codes"] = ["maintainer-review-required"]

    plan = ModelOpsCheapFirstCanaryPlanService().build_plan(signals)
    fast = next(step for step in plan["canary_steps"] if step["source_queue_item_id"] == "default-change-fast")

    assert plan["status"] == "review_required"
    assert fast["step_status"] == "review_required"
    assert fast["batch_percentage"] == 0
    assert "maintainer-review-required" in fast["reason_codes"]
    assert plan["review_step_ids"] == ["maintainer_review-fast"]


def test_canary_plan_blocks_when_route_or_cost_guardrails_fail():
    signals = _signals()
    signals["route_guardrails"] = {"status": "fail"}

    plan = ModelOpsCheapFirstCanaryPlanService().build_plan(signals)
    fast = next(step for step in plan["canary_steps"] if step["source_queue_item_id"] == "default-change-fast")

    assert plan["status"] == "blocked"
    assert fast["step_status"] == "blocked"
    assert fast["batch_percentage"] == 0
    assert "route-guardrails-blocked" in fast["reason_codes"]
    assert plan["blocking_step_ids"] == ["blocked_before_canary-fast"]


def test_canary_plan_is_monitor_only_when_no_default_changes_are_queued():
    signals = _signals()
    signals["default_change_queue"]["queue_items"] = [signals["default_change_queue"]["queue_items"][1]]

    plan = ModelOpsCheapFirstCanaryPlanService().build_plan(signals)
    step = plan["canary_steps"][0]

    assert plan["status"] == "monitor_only"
    assert step["step_status"] == "monitor_only"
    assert step["batch_percentage"] == 0
    assert step["observation_window_hours"] == 24
    assert plan["summary"]["monitor_only_step_count"] == 1


def test_canary_plan_route_and_models_payload_include_plan():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/cheap-first-canary-plan")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["queue_item_count"] >= 6
    assert route_payload["data"]["summary"]["configuration_written"] is False
    assert route_payload["data"]["summary"]["gateway_called"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["cheap_first_canary_plan"]["summary"]["queue_item_count"] >= 6
    assert payload["cheap_first_canary_plan"]["claim_boundary"]["production_traffic_shifted"] is False
