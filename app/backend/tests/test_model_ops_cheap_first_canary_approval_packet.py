import json
import re

from services.model_ops_cheap_first_canary_approval_packet import ModelOpsCheapFirstCanaryApprovalPacketService
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


def _promotion(payload: dict | None = None, plan: dict | None = None) -> dict:
    source_plan = plan or _plan()
    observation = ModelOpsCheapFirstCanaryObservationService().build_review(
        payload,
        {"cheap_first_canary_plan": source_plan},
    )
    return ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {"cheap_first_canary_plan": source_plan, "cheap_first_canary_observation": observation}
    )


def test_canary_approval_packet_is_ready_after_advance_decision():
    promotion = _promotion(
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

    packet = ModelOpsCheapFirstCanaryApprovalPacketService().build_packet(
        {"cheap_first_canary_promotion_decision": promotion}
    )
    item = packet["approval_items"][0]

    assert packet["status"] == "approval_ready"
    assert packet["summary"]["ready_for_approval_count"] == 1
    assert item["approval_status"] == "ready_for_maintainer_approval"
    assert item["required_signoffs"] == ["maintainer_owner", "model_ops_reviewer"]
    assert "confirm-no-rollback-trigger-breach" in item["pre_approval_checks"]
    assert item["configuration_change_allowed"] is False
    assert packet["approval_policy"]["approval_record_written"] is False
    assert packet["summary"]["traffic_shifted"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(packet, ensure_ascii=False))


def test_canary_approval_packet_requires_rollback_review_for_failed_observation():
    promotion = _promotion(
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

    packet = ModelOpsCheapFirstCanaryApprovalPacketService().build_packet(
        {"cheap_first_canary_promotion_decision": promotion}
    )

    assert packet["status"] == "rollback_review_required"
    assert packet["rollback_review_item_ids"] == ["approval-canary_1_percent-fast"]
    assert packet["claim_boundary"]["maintainer_approval_claimed"] is False
    assert "rollback-trigger-breached" in packet["approval_items"][0]["blocking_reason_codes"]


def test_canary_approval_packet_blocks_when_observation_is_missing():
    promotion = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {
            "cheap_first_canary_plan": _plan(),
            "cheap_first_canary_observation": {"status": "not_supplied", "summary": {}, "observation_rows": []},
        }
    )

    packet = ModelOpsCheapFirstCanaryApprovalPacketService().build_packet(
        {"cheap_first_canary_promotion_decision": promotion}
    )

    assert packet["status"] == "approval_blocked"
    assert packet["blocked_item_ids"] == ["approval-canary_1_percent-fast"]
    assert packet["approval_items"][0]["required_signoffs"] == ["model_ops_reviewer"]
    assert packet["privacy_boundary"]["approval_record_written"] is False


def test_canary_approval_packet_is_monitor_only_for_current_defaults():
    plan = _plan("monitor_only")
    plan["canary_steps"][0]["id"] = "monitor_existing_default-fast"
    plan["canary_steps"][0]["phase"] = "monitor_existing_default"
    promotion = ModelOpsCheapFirstCanaryPromotionDecisionService().build_decision(
        {
            "cheap_first_canary_plan": plan,
            "cheap_first_canary_observation": {"status": "not_supplied", "summary": {}, "observation_rows": []},
        }
    )

    packet = ModelOpsCheapFirstCanaryApprovalPacketService().build_packet(
        {"cheap_first_canary_promotion_decision": promotion}
    )

    assert packet["status"] == "monitor_only"
    assert packet["summary"]["monitor_only_count"] == 1
    assert packet["approval_items"][0]["required_signoffs"] == []


def test_canary_approval_packet_routes_return_packet():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-canary-approval-packet")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["summary"]["approval_record_written"] is False

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
    assert post_payload["data"]["approval_packet"]["summary"]["configuration_written"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert "cheap_first_canary_approval_packet" in models_payload
