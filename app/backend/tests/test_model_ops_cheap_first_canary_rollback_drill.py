import json
import re

from services.model_ops_cheap_first_canary_approval_packet import ModelOpsCheapFirstCanaryApprovalPacketService
from services.model_ops_cheap_first_canary_observation import ModelOpsCheapFirstCanaryObservationService
from services.model_ops_cheap_first_canary_promotion_decision import ModelOpsCheapFirstCanaryPromotionDecisionService
from services.model_ops_cheap_first_canary_rollback_drill import ModelOpsCheapFirstCanaryRollbackDrillService


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


def _approval_packet(payload: dict | None = None, plan: dict | None = None) -> tuple[dict, dict]:
    source_plan = plan or _plan()
    observation = ModelOpsCheapFirstCanaryObservationService().build_review(
        payload,
        {"cheap_first_canary_plan": source_plan},
    )
    promotion = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {"cheap_first_canary_plan": source_plan, "cheap_first_canary_observation": observation}
    )
    packet = ModelOpsCheapFirstCanaryApprovalPacketService().build_packet(
        {"cheap_first_canary_promotion_decision": promotion}
    )
    return promotion, packet


def test_canary_rollback_drill_is_ready_after_approval_ready_packet():
    promotion, packet = _approval_packet(
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

    drill = ModelOpsCheapFirstCanaryRollbackDrillService().build_drill(
        {
            "cheap_first_canary_promotion_decision": promotion,
            "cheap_first_canary_approval_packet": packet,
        }
    )
    item = drill["rollback_drill_items"][0]

    assert drill["status"] == "drill_ready"
    assert drill["summary"]["ready_drill_count"] == 1
    assert item["drill_status"] == "drill_ready"
    assert item["required_roles"] == ["maintainer_owner", "model_ops_reviewer", "release_operator"]
    assert "Confirm rollback trigger checklist" in " ".join(item["rehearsal_steps"])
    assert item["rollback_executed"] is False
    assert drill["summary"]["traffic_shifted"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(drill, ensure_ascii=False))


def test_canary_rollback_drill_requires_review_for_failed_observation():
    promotion, packet = _approval_packet(
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

    drill = ModelOpsCheapFirstCanaryRollbackDrillService().build_drill(
        {
            "cheap_first_canary_promotion_decision": promotion,
            "cheap_first_canary_approval_packet": packet,
        }
    )

    assert drill["status"] == "rollback_drill_required"
    assert drill["summary"]["rollback_required_count"] == 1
    assert drill["rollback_required_item_ids"] == ["rollback-drill-canary_1_percent-fast"]
    assert drill["rollback_drill_items"][0]["trigger_review_status"] == "failed_trigger_review_required"
    assert drill["claim_boundary"]["rollback_executed"] is False


def test_canary_rollback_drill_blocks_when_observation_is_missing():
    promotion, packet = _approval_packet(None)

    drill = ModelOpsCheapFirstCanaryRollbackDrillService().build_drill(
        {
            "cheap_first_canary_promotion_decision": promotion,
            "cheap_first_canary_approval_packet": packet,
        }
    )

    assert drill["status"] == "drill_blocked"
    assert drill["summary"]["blocked_drill_count"] == 1
    assert drill["blocked_drill_item_ids"] == ["rollback-drill-canary_1_percent-fast"]
    assert drill["rollback_drill_items"][0]["required_roles"] == ["model_ops_reviewer"]


def test_canary_rollback_drill_is_monitor_only_for_current_defaults():
    plan = _plan("monitor_only")
    plan["canary_steps"][0]["id"] = "monitor_existing_default-fast"
    plan["canary_steps"][0]["phase"] = "monitor_existing_default"
    promotion, packet = _approval_packet(None, plan)

    drill = ModelOpsCheapFirstCanaryRollbackDrillService().build_drill(
        {
            "cheap_first_canary_promotion_decision": promotion,
            "cheap_first_canary_approval_packet": packet,
        }
    )

    assert drill["status"] == "monitor_only"
    assert drill["summary"]["monitor_only_count"] == 1
    assert drill["rollback_drill_items"][0]["required_roles"] == []
    assert drill["rollback_drill_policy"]["rollback_execution_allowed"] is False


def test_canary_rollback_drill_routes_return_packet():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-canary-rollback-drill")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["summary"]["rollback_executed"] is False

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
    assert post_payload["data"]["rollback_drill"]["summary"]["configuration_written"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert "cheap_first_canary_rollback_drill" in models_payload
