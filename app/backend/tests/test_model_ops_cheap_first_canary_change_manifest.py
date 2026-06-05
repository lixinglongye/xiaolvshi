import json
import re

from services.model_ops_cheap_first_canary_approval_packet import ModelOpsCheapFirstCanaryApprovalPacketService
from services.model_ops_cheap_first_canary_change_manifest import ModelOpsCheapFirstCanaryChangeManifestService
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
                "env_var": "APP_AI_FAST_MODEL",
                "current_model": "current-fast-model",
                "recommended_model": "recommended-fast-model",
                "phase": "canary_1_percent",
                "step_status": step_status,
                "batch_percentage": 1,
                "holdout_percentage": 99,
            }
        ],
    }


def _manifest(payload: dict | None = None, plan: dict | None = None) -> dict:
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
    drill = ModelOpsCheapFirstCanaryRollbackDrillService().build_drill(
        {
            "cheap_first_canary_promotion_decision": promotion,
            "cheap_first_canary_approval_packet": packet,
        }
    )
    return ModelOpsCheapFirstCanaryChangeManifestService().build_manifest(
        {
            "cheap_first_canary_plan": source_plan,
            "cheap_first_canary_promotion_decision": promotion,
            "cheap_first_canary_approval_packet": packet,
            "cheap_first_canary_rollback_drill": drill,
        }
    )


def test_canary_change_manifest_is_ready_after_ready_rollback_drill():
    manifest = _manifest(
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
    item = manifest["change_manifest_items"][0]

    assert manifest["status"] == "manifest_ready"
    assert manifest["summary"]["ready_change_count"] == 1
    assert manifest["summary"]["change_applied"] is False
    assert manifest["summary"]["env_file_written"] is False
    assert item["manifest_status"] == "manifest_ready"
    assert item["env_var"] == "APP_AI_FAST_MODEL"
    assert item["external_change_set"]["apply_mode"] == "manual_only"
    assert item["external_change_set"]["secret_value_included"] is False
    assert item["change_applied"] is False
    assert "rollback-drill-ready" in item["prerequisites"]
    assert not SENSITIVE_PATTERN.search(json.dumps(manifest, ensure_ascii=False))


def test_canary_change_manifest_requires_rollback_review_for_failed_observation():
    manifest = _manifest(
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

    assert manifest["status"] == "rollback_review_required"
    assert manifest["summary"]["rollback_review_count"] == 1
    assert manifest["rollback_review_item_ids"] == ["change-manifest-canary_1_percent-fast"]
    assert manifest["change_manifest_items"][0]["change_applied"] is False
    assert manifest["claim_boundary"]["change_applied"] is False


def test_canary_change_manifest_blocks_when_observation_is_missing():
    manifest = _manifest(None)

    assert manifest["status"] == "manifest_blocked"
    assert manifest["summary"]["blocked_change_count"] == 1
    assert manifest["blocked_change_item_ids"] == ["change-manifest-canary_1_percent-fast"]
    assert manifest["change_manifest_policy"]["configuration_write_allowed"] is False


def test_canary_change_manifest_is_monitor_only_for_current_defaults():
    plan = _plan("monitor_only")
    plan["canary_steps"][0]["id"] = "monitor_existing_default-fast"
    plan["canary_steps"][0]["phase"] = "monitor_existing_default"

    manifest = _manifest(None, plan)

    assert manifest["status"] == "monitor_only"
    assert manifest["summary"]["monitor_only_count"] == 1
    assert manifest["change_manifest_items"][0]["operator_steps"] == [
        "Continue monitoring the current fast default.",
        "No external change set is queued by this manifest.",
    ]
    assert manifest["change_manifest_policy"]["traffic_shift_allowed"] is False


def test_canary_change_manifest_redacts_secret_like_source_values():
    plan = _plan()
    plan["canary_steps"][0]["recommended_model"] = "sk-" + "a" * 24

    manifest = _manifest(
        {
            "observations": [
                {
                    "step_id": "canary_1_percent-fast",
                    "request_count": 100,
                    "failure_count": 0,
                }
            ]
        },
        plan,
    )

    serialized = json.dumps(manifest, ensure_ascii=False)
    assert "redacted-secret-like-value" in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_canary_change_manifest_routes_return_manifest():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-canary-change-manifest")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["summary"]["change_applied"] is False

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
    assert post_payload["data"]["change_manifest"]["summary"]["configuration_written"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert "cheap_first_canary_change_manifest" in models_payload
