import json
import re

from services.model_ops_cheap_first_canary_observation import ModelOpsCheapFirstCanaryObservationService
from services.model_ops_cheap_first_canary_promotion_decision import ModelOpsCheapFirstCanaryPromotionDecisionService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _plan(step_status: str = "ready") -> dict:
    return {
        "status": "ready",
        "canary_steps": [
            {
                "id": "canary_1_percent-fast",
                "task": "fast",
                "phase": "canary_1_percent",
                "step_status": step_status,
                "batch_percentage": 1,
                "holdout_percentage": 99,
            }
        ],
    }


def _observation(payload: dict, plan: dict | None = None) -> dict:
    return ModelOpsCheapFirstCanaryObservationService().build_review(
        payload,
        {"cheap_first_canary_plan": plan or _plan()},
    )


def test_canary_promotion_decision_advances_after_passing_observation():
    observation = _observation(
        {
            "observations": [
                {
                    "step_id": "canary_1_percent-fast",
                    "request_count": 100,
                    "failure_count": 0,
                    "over_budget_count": 0,
                    "premium_request_count": 0,
                    "operator_review_count": 1,
                }
            ]
        }
    )

    decision = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {"cheap_first_canary_plan": _plan(), "cheap_first_canary_observation": observation}
    )
    item = decision["promotion_items"][0]

    assert decision["status"] == "advance_next_batch"
    assert item["promotion_status"] == "advance_next_batch"
    assert item["traffic_shift_allowed"] is False
    assert decision["decision"]["configuration_change_allowed"] is False
    assert decision["summary"]["traffic_shifted"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(decision, ensure_ascii=False))


def test_canary_promotion_decision_rolls_back_on_failing_observation():
    observation = _observation(
        {
            "observations": [
                {
                    "step_id": "canary_1_percent-fast",
                    "request_count": 100,
                    "failure_count": 4,
                    "over_budget_count": 2,
                }
            ]
        }
    )

    decision = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {"cheap_first_canary_plan": _plan(), "cheap_first_canary_observation": observation}
    )

    assert decision["status"] == "rollback_required"
    assert decision["rollback_item_ids"] == ["promotion-canary_1_percent-fast"]
    assert "rollback-trigger-breached" in decision["promotion_items"][0]["reason_codes"]
    assert decision["claim_boundary"]["automatic_canary_rollout_claimed"] is False


def test_canary_promotion_decision_holds_when_observation_is_missing():
    decision = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {
            "cheap_first_canary_plan": _plan(),
            "cheap_first_canary_observation": {"status": "not_supplied", "summary": {}, "observation_rows": []},
        }
    )

    assert decision["status"] == "hold_for_review"
    assert decision["hold_item_ids"] == ["promotion-canary_1_percent-fast"]
    assert "observation-missing-for-step" in decision["promotion_items"][0]["reason_codes"]


def test_canary_promotion_decision_is_monitor_only_for_existing_default_steps():
    plan = _plan("monitor_only")
    plan["canary_steps"][0]["id"] = "monitor_existing_default-fast"
    plan["canary_steps"][0]["phase"] = "monitor_existing_default"

    decision = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {
            "cheap_first_canary_plan": plan,
            "cheap_first_canary_observation": {"status": "not_supplied", "summary": {}, "observation_rows": []},
        }
    )

    assert decision["status"] == "monitor_only"
    assert decision["promotion_items"][0]["promotion_status"] == "monitor_only"
    assert "current-default-monitor-only" in decision["promotion_items"][0]["reason_codes"]


def test_canary_promotion_decision_routes_return_decision():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-canary-promotion-decision")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["summary"]["configuration_written"] is False

    post_response = client.post(
        "/api/v1/aihub/models/cheap-first-canary-observation",
        json={
            "observations": [
                {
                    "step_id": "monitor_existing_default-fast",
                    "task": "fast",
                    "request_count": 25,
                    "failure_count": 0,
                }
            ]
        },
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["success"] is True
    assert post_payload["data"]["promotion_decision"]["summary"]["traffic_shifted"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert "cheap_first_canary_promotion_decision" in models_payload
