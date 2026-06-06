import json
import re

from services.model_ops_cheap_first_maintainer_execution_checklist import (
    ModelOpsCheapFirstMaintainerExecutionChecklistService,
)


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", re.IGNORECASE)


def _signals() -> dict:
    return {
        "cheap_first_release_decision": {
            "status": "pass",
            "summary": {"default_promotion_blocked": False, "maintainer_review_required": False},
        },
        "cheap_first_priority_queue": {
            "status": "ready",
            "priority_items": [
                {
                    "id": "cheap-first-priority-fast",
                    "task": "fast",
                    "priority_rank": 1,
                    "priority_score": 68,
                    "priority_label": "P1",
                    "work_status": "ready",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "requires_change": True,
                    "reason_codes": ["default-change-requested"],
                }
            ],
        },
        "cheap_first_canary_plan": {
            "status": "ready",
            "canary_steps": [
                {
                    "id": "canary_1_percent-fast",
                    "task": "fast",
                    "step_status": "ready",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash",
                    "recommended_model": "gemini-2.5-flash-lite",
                }
            ],
        },
        "cheap_first_canary_promotion_decision": {
            "status": "advance_next_batch",
            "promotion_items": [
                {
                    "id": "promotion-canary_1_percent-fast",
                    "task": "fast",
                    "promotion_status": "advance_next_batch",
                }
            ],
        },
        "cheap_first_canary_approval_packet": {
            "status": "approval_ready",
            "approval_items": [
                {
                    "id": "approval-canary_1_percent-fast",
                    "task": "fast",
                    "approval_status": "ready_for_maintainer_approval",
                }
            ],
        },
        "cheap_first_canary_rollback_drill": {
            "status": "drill_ready",
            "rollback_drill_items": [
                {
                    "id": "rollback-drill-canary_1_percent-fast",
                    "task": "fast",
                    "drill_status": "drill_ready",
                }
            ],
        },
        "cheap_first_canary_change_manifest": {
            "status": "manifest_ready",
            "change_manifest_items": [
                {
                    "id": "change-manifest-canary_1_percent-fast",
                    "task": "fast",
                    "manifest_status": "manifest_ready",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash",
                    "recommended_model": "gemini-2.5-flash-lite",
                }
            ],
        },
    }


def test_execution_checklist_allows_external_change_only_when_evidence_is_ready():
    checklist = ModelOpsCheapFirstMaintainerExecutionChecklistService().build_checklist(_signals())
    item = checklist["execution_items"][0]

    assert checklist["status"] == "ready_for_external_change"
    assert checklist["summary"]["ready_for_external_change_count"] == 1
    assert checklist["summary"]["configuration_written"] is False
    assert checklist["summary"]["gateway_called"] is False
    assert item["execution_status"] == "ready_for_external_change"
    assert item["external_change_allowed"] is True
    assert item["env_var"] == "APP_AI_FAST_MODEL"
    assert item["missing_evidence"] == []
    assert "default-change-requested" in item["reason_codes"]


def test_execution_checklist_blocks_when_release_or_manifest_blocks():
    signals = _signals()
    signals["cheap_first_release_decision"]["status"] = "fail"
    signals["cheap_first_canary_change_manifest"]["status"] = "manifest_blocked"
    signals["cheap_first_canary_change_manifest"]["change_manifest_items"][0]["manifest_status"] = "manifest_blocked"

    checklist = ModelOpsCheapFirstMaintainerExecutionChecklistService().build_checklist(signals)
    item = checklist["execution_items"][0]

    assert checklist["status"] == "blocked"
    assert checklist["summary"]["blocked_count"] == 1
    assert item["execution_status"] == "blocked"
    assert "release-decision-blocked" in item["reason_codes"]
    assert "change-manifest-not-ready" in item["reason_codes"]
    assert "release-decision-pass" in item["missing_evidence"]
    assert item["configuration_written"] is False


def test_execution_checklist_requires_rollback_review_when_canary_failed():
    signals = _signals()
    signals["cheap_first_canary_rollback_drill"]["status"] = "rollback_required"
    signals["cheap_first_canary_rollback_drill"]["rollback_drill_items"][0]["drill_status"] = "rollback_drill_required"
    signals["cheap_first_canary_change_manifest"]["status"] = "rollback_review_required"
    signals["cheap_first_canary_change_manifest"]["change_manifest_items"][0]["manifest_status"] = "rollback_review_required"

    checklist = ModelOpsCheapFirstMaintainerExecutionChecklistService().build_checklist(signals)

    assert checklist["status"] == "rollback_review_required"
    assert checklist["summary"]["rollback_review_count"] == 1
    assert checklist["execution_items"][0]["execution_status"] == "rollback_review_required"
    assert checklist["execution_items"][0]["external_change_allowed"] is False


def test_execution_checklist_monitor_only_rows_do_not_require_evidence():
    signals = _signals()
    signals["cheap_first_priority_queue"]["priority_items"][0]["work_status"] = "monitor_only"
    signals["cheap_first_priority_queue"]["priority_items"][0]["requires_change"] = False
    signals["cheap_first_canary_plan"]["canary_steps"][0]["step_status"] = "monitor_only"
    signals["cheap_first_canary_promotion_decision"]["promotion_items"][0]["promotion_status"] = "monitor_only"
    signals["cheap_first_canary_approval_packet"]["approval_items"][0]["approval_status"] = "monitor_only"
    signals["cheap_first_canary_rollback_drill"]["rollback_drill_items"][0]["drill_status"] = "monitor_only"
    signals["cheap_first_canary_change_manifest"]["change_manifest_items"][0]["manifest_status"] = "monitor_only"

    checklist = ModelOpsCheapFirstMaintainerExecutionChecklistService().build_checklist(signals)

    assert checklist["status"] == "monitor_only"
    assert checklist["summary"]["monitor_only_count"] == 1
    assert checklist["execution_items"][0]["missing_evidence"] == []
    assert checklist["execution_items"][0]["external_change_allowed"] is False


def test_execution_checklist_is_metadata_only_and_redacts_secret_like_values():
    signals = _signals()
    signals["cheap_first_priority_queue"]["priority_items"][0]["recommended_model"] = "sk-" + "a" * 24
    signals["cheap_first_canary_change_manifest"]["change_manifest_items"][0]["recommended_model"] = "sk-" + "a" * 24

    checklist = ModelOpsCheapFirstMaintainerExecutionChecklistService().build_checklist(signals)
    payload_text = json.dumps(checklist, ensure_ascii=False)

    assert checklist["privacy_boundary"]["metadata_only"] is True
    assert checklist["privacy_boundary"]["credentials_included"] is False
    assert checklist["privacy_boundary"]["raw_payloads_included"] is False
    assert checklist["summary"]["secret_value_included"] is False
    assert checklist["claim_boundary"]["automatic_default_change_claimed"] is False
    assert "redacted-secret-like-value" in payload_text
    assert not SENSITIVE_PATTERN.search(payload_text)


def test_execution_checklist_route_and_models_payload_include_checklist():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/cheap-first-maintainer-execution-checklist")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["execution_item_count"] >= 6
    assert route_payload["data"]["summary"]["configuration_written"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["cheap_first_maintainer_execution_checklist"]["summary"]["execution_item_count"] >= 6
    assert payload["cheap_first_maintainer_execution_checklist"]["summary"]["gateway_called"] is False
    assert "cheap_first_maintainer_execution_checklist" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
