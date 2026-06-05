import json
import re

from services.model_ops_default_change_queue import ModelOpsDefaultChangeQueueService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _signals() -> dict:
    return {
        "cheap_first_release_decision": {
            "status": "pass",
            "summary": {
                "default_promotion_blocked": False,
                "maintainer_review_required": False,
            },
        },
        "default_optimization": {
            "status": "warn",
            "recommendations": [
                {
                    "task": "fast",
                    "status": "warn",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "requires_change": True,
                    "requires_operator_review": False,
                    "current_cost_tier": "low",
                    "recommended_cost_tier": "lowest",
                    "estimated_monthly_savings_usd": 1.25,
                },
                {
                    "task": "ocr",
                    "status": "pass",
                    "env_var": "APP_OCR_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "requires_change": False,
                    "requires_operator_review": False,
                    "current_cost_tier": "lowest",
                    "recommended_cost_tier": "lowest",
                },
            ],
        },
        "gateway_probe_evaluation": {"status": "pass"},
        "price_refresh_monitor": {"status": "pass"},
        "catalog_source_audit": {"status": "pass"},
    }


def test_default_change_queue_marks_ready_change_after_passing_evidence():
    signals = _signals()
    signals["default_optimization"]["recommendations"][0]["status"] = "pass"

    queue = ModelOpsDefaultChangeQueueService().build_queue(signals)
    items = {item["task"]: item for item in queue["queue_items"]}

    assert queue["status"] == "ready"
    assert items["fast"]["queue_status"] == "ready"
    assert items["fast"]["requires_change"] is True
    assert items["ocr"]["queue_status"] == "no_action"
    assert queue["summary"]["configuration_written"] is False
    assert queue["privacy_boundary"]["network_called"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(queue, ensure_ascii=False))


def test_default_change_queue_requires_review_when_release_decision_requires_review():
    signals = _signals()
    signals["cheap_first_release_decision"] = {
        "status": "review_required",
        "summary": {
            "default_promotion_blocked": False,
            "maintainer_review_required": True,
        },
    }

    queue = ModelOpsDefaultChangeQueueService().build_queue(signals)
    fast = next(item for item in queue["queue_items"] if item["task"] == "fast")

    assert queue["status"] == "review_required"
    assert fast["queue_status"] == "review_required"
    assert "maintainer-review-required" in fast["reason_codes"]
    assert queue["review_item_ids"] == ["default-change-fast"]


def test_default_change_queue_blocks_when_release_decision_blocks_default_promotion():
    signals = _signals()
    signals["cheap_first_release_decision"] = {
        "status": "fail",
        "summary": {
            "default_promotion_blocked": True,
            "maintainer_review_required": False,
        },
    }

    queue = ModelOpsDefaultChangeQueueService().build_queue(signals)
    fast = next(item for item in queue["queue_items"] if item["task"] == "fast")

    assert queue["status"] == "blocked"
    assert fast["queue_status"] == "blocked"
    assert "release-decision-blocked" in fast["reason_codes"]
    assert queue["blocking_item_ids"] == ["default-change-fast"]


def test_default_change_queue_route_and_models_payload_include_queue():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/default-change-queue")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["queue_item_count"] >= 6

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["default_change_queue"]["summary"]["queue_item_count"] >= 6
    assert payload["default_change_queue"]["summary"]["configuration_written"] is False
