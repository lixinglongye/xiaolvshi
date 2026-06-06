import json
import re

from services.model_ops_cheap_first_priority_queue import ModelOpsCheapFirstPriorityQueueService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|token|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def _signals() -> dict:
    return {
        "cheap_first_release_decision": {
            "status": "review_required",
            "summary": {
                "default_promotion_blocked": False,
                "maintainer_review_required": True,
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
                    "current_cost_tier": "low",
                    "recommended_cost_tier": "lowest",
                    "requires_change": True,
                    "requires_operator_review": False,
                    "estimated_monthly_savings_usd": 1.25,
                },
                {
                    "task": "ocr",
                    "status": "pass",
                    "env_var": "APP_OCR_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "current_cost_tier": "lowest",
                    "recommended_cost_tier": "lowest",
                    "requires_change": False,
                    "requires_operator_review": False,
                    "estimated_monthly_savings_usd": 0,
                },
            ],
        },
        "gemini_cheap_first_coverage_gate": {
            "status": "review_required",
            "coverage_rows": [
                {
                    "task": "fast",
                    "coverage_status": "review_required",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "reason_codes": ["runtime_default_not_cheapest_capable"],
                },
                {
                    "task": "ocr",
                    "coverage_status": "ready",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "reason_codes": ["coverage_ready"],
                },
            ],
        },
        "route_quality_budget": {
            "status": "warn",
            "task_quality_budgets": [
                {
                    "task": "fast",
                    "runtime_default_model": "gemini-2.5-flash",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "cheap_start_model": "gemini-2.5-flash-lite",
                    "runtime_default_cost_tier": "low",
                    "recommended_model_cost_tier": "lowest",
                    "runtime_default_has_required_capabilities": True,
                    "runtime_default_over_budget": False,
                    "quality_score": 82,
                    "quality_floor": 75,
                    "review_action": "cheap_first_with_quality_gate",
                },
                {
                    "task": "ocr",
                    "runtime_default_model": "gemini-2.5-flash-lite",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "cheap_start_model": "gemini-2.5-flash-lite",
                    "runtime_default_cost_tier": "lowest",
                    "recommended_model_cost_tier": "lowest",
                    "runtime_default_has_required_capabilities": True,
                    "runtime_default_over_budget": False,
                    "quality_score": 88,
                    "quality_floor": 75,
                    "review_action": "cheap_first_with_quality_gate",
                },
            ],
        },
        "default_change_queue": {
            "status": "review_required",
            "queue_items": [
                {
                    "task": "fast",
                    "queue_status": "review_required",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "requires_change": True,
                    "requires_operator_review": False,
                    "reason_codes": ["maintainer-review-required"],
                },
                {
                    "task": "ocr",
                    "queue_status": "no_action",
                    "env_var": "APP_OCR_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "requires_change": False,
                    "requires_operator_review": False,
                    "reason_codes": ["runtime-default-aligned"],
                },
            ],
        },
        "price_refresh_monitor": {"status": "pass"},
        "catalog_source_audit": {"status": "pass"},
    }


def test_priority_queue_ranks_change_requests_before_monitor_only_rows():
    queue = ModelOpsCheapFirstPriorityQueueService().build_queue(_signals())

    assert queue["status"] == "review_required"
    assert queue["summary"]["priority_item_count"] == 2
    assert queue["summary"]["review_required_count"] == 1
    assert queue["summary"]["monitor_only_count"] == 1
    assert queue["summary"]["estimated_monthly_savings_usd"] == 1.25
    assert queue["priority_items"][0]["task"] == "fast"
    assert queue["priority_items"][0]["priority_rank"] == 1
    assert queue["priority_items"][0]["priority_label"] in {"P0", "P1"}
    assert queue["priority_items"][0]["work_status"] == "review_required"
    assert "default-change-requested" in queue["priority_items"][0]["reason_codes"]
    assert "estimated-savings-available" in queue["priority_items"][0]["reason_codes"]
    assert queue["priority_items"][1]["task"] == "ocr"
    assert queue["priority_items"][1]["work_status"] == "monitor_only"


def test_priority_queue_blocks_when_release_gate_or_capability_gap_blocks():
    signals = _signals()
    signals["cheap_first_release_decision"] = {
        "status": "fail",
        "summary": {
            "default_promotion_blocked": True,
            "maintainer_review_required": False,
        },
    }
    signals["route_quality_budget"]["task_quality_budgets"][0]["runtime_default_has_required_capabilities"] = False
    signals["default_change_queue"]["queue_items"][0]["queue_status"] = "blocked"

    queue = ModelOpsCheapFirstPriorityQueueService().build_queue(signals)
    fast = next(item for item in queue["priority_items"] if item["task"] == "fast")

    assert queue["status"] == "blocked"
    assert queue["summary"]["blocked_count"] == 1
    assert fast["work_status"] == "blocked"
    assert fast["priority_label"] == "P0"
    assert "release-gate-blocked" in fast["reason_codes"]
    assert "runtime-default-capability-gap" in fast["reason_codes"]
    assert queue["blocking_item_ids"] == ["cheap-first-priority-fast"]


def test_priority_queue_is_metadata_only():
    queue = ModelOpsCheapFirstPriorityQueueService().build_queue(_signals())
    payload_text = json.dumps(queue, ensure_ascii=False)

    assert queue["summary"]["configuration_written"] is False
    assert queue["summary"]["model_called"] is False
    assert queue["summary"]["gateway_called"] is False
    assert queue["summary"]["network_called"] is False
    assert queue["privacy_boundary"]["metadata_only"] is True
    assert queue["privacy_boundary"]["credentials_included"] is False
    assert queue["privacy_boundary"]["raw_payloads_included"] is False
    assert queue["claim_boundary"]["automatic_default_change_claimed"] is False
    assert queue["claim_boundary"]["live_gateway_execution_claimed"] is False
    assert queue["claim_boundary"]["twenty_four_hour_completion_claimed"] is False
    assert queue["claim_boundary"]["hundred_update_completion_claimed"] is False
    assert not SENSITIVE_PATTERN.search(payload_text)


def test_priority_queue_route_and_models_payload_include_queue():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/cheap-first-priority-queue")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["priority_item_count"] >= 6
    assert route_payload["data"]["summary"]["configuration_written"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["cheap_first_priority_queue"]["summary"]["priority_item_count"] >= 6
    assert payload["cheap_first_priority_queue"]["summary"]["model_called"] is False
    assert "cheap_first_priority_queue" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
