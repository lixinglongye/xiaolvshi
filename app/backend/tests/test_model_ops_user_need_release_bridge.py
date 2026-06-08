import re

from services.model_ops_user_need_release_bridge import ModelOpsUserNeedReleaseBridgeService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+"
)


def _base_signals(*, priority_band: str = "high", implementation_status: str = "ready", route_status: str = "ready"):
    need_id = "synthetic-need"
    implementation_blockers = ["high-priority-local-fixture-missing"] if implementation_status == "blocked" else []
    route_blockers = ["high_priority_route_unmapped"] if route_status in {"blocked", "unmapped"} else []
    return {
        "user_need_benchmark_coverage": {
            "status": "ready",
            "summary": {
                "need_count": 1,
                "high_priority_need_count": 1 if priority_band == "high" else 0,
            },
        },
        "user_need_implementation_priority_queue": {
            "status": implementation_status,
            "summary": {
                "queue_item_count": 1,
                "blocked_action_count": 1 if implementation_status == "blocked" else 0,
            },
            "queue_items": [
                {
                    "id": f"user-need-implementation-{need_id}",
                    "need_id": need_id,
                    "title": "Synthetic release need",
                    "category": "release",
                    "priority_band": priority_band,
                    "user_need_priority_score": 90,
                    "action_status": implementation_status,
                    "blocker_codes": implementation_blockers,
                    "review_reason_codes": [],
                    "release_gate_links": ["model-ops-cheap-first-release-decision"],
                    "next_actions": ["Attach local fixture metadata before promotion."],
                }
            ],
        },
        "user_need_gemini_route_coverage": {
            "status": route_status,
            "summary": {
                "need_count": 1,
                "high_priority_need_count": 1 if priority_band == "high" else 0,
                "high_priority_route_protected_count": 1 if route_status == "ready" else 0,
            },
            "coverage_rows": [
                {
                    "id": f"user-need-gemini-route-{need_id}",
                    "need_id": need_id,
                    "title": "Synthetic release need",
                    "category": "release",
                    "priority_band": priority_band,
                    "priority_score": 90,
                    "benchmark_coverage_status": "covered",
                    "route_coverage_status": route_status,
                    "high_frequency_route_ready": route_status == "ready",
                    "default_allowed_without_review": route_status == "ready",
                    "linked_route_tasks": ["fast"],
                    "linked_default_models": ["gemini-2.5-flash-lite"],
                    "blocked_reason_codes": route_blockers,
                    "review_reason_codes": [],
                    "release_gate_links": ["user-need-gemini-route-coverage"],
                    "next_actions": ["Keep route coverage attached."],
                }
            ],
        },
    }


def test_model_ops_user_need_release_bridge_current_metadata_requires_review_without_overblocking():
    bridge = ModelOpsUserNeedReleaseBridgeService().build_bridge()
    rows = {row["need_id"]: row for row in bridge["bridge_rows"]}

    assert bridge["id"] == "modelops-user-need-release-bridge"
    assert bridge["title"] == "ModelOps user-need release bridge"
    assert bridge["status"] == "review_required"
    assert bridge["summary"]["need_count"] >= 7
    assert bridge["summary"]["blocked_need_count"] == 0
    assert bridge["summary"]["review_required_need_count"] >= 1
    assert bridge["summary"]["implementation_blocked_count"] >= 1
    assert bridge["summary"]["high_priority_implementation_blocked_count"] == 0
    assert bridge["summary"]["default_change_allowed"] is True
    assert bridge["summary"]["maintainer_review_required"] is True
    assert "feedback-to-roadmap-loop" in bridge["review_need_ids"]
    assert "feedback-to-roadmap-loop" not in bridge["blocked_need_ids"]
    assert rows["feedback-to-roadmap-loop"]["release_bridge_status"] == "review_required"
    assert rows["feedback-to-roadmap-loop"]["release_decision_effect"] == "requires_maintainer_review"
    assert "missing-local-benchmark-coverage" in rows["feedback-to-roadmap-loop"]["implementation_blocker_codes"]


def test_model_ops_user_need_release_bridge_blocks_high_priority_implementation_blocker():
    bridge = ModelOpsUserNeedReleaseBridgeService().build_bridge(
        _base_signals(priority_band="high", implementation_status="blocked", route_status="ready")
    )
    row = bridge["bridge_rows"][0]

    assert bridge["status"] == "blocked"
    assert bridge["summary"]["blocked_need_count"] == 1
    assert bridge["summary"]["default_change_allowed"] is False
    assert bridge["blocking_check_ids"] == ["modelops-user-need-release-synthetic-need"]
    assert row["release_decision_effect"] == "blocks_default_changes"
    assert "high-priority-local-fixture-missing" in row["implementation_blocker_codes"]


def test_model_ops_user_need_release_bridge_blocks_high_priority_route_unmapped():
    bridge = ModelOpsUserNeedReleaseBridgeService().build_bridge(
        _base_signals(priority_band="high", implementation_status="ready", route_status="unmapped")
    )
    row = bridge["bridge_rows"][0]

    assert bridge["status"] == "blocked"
    assert bridge["summary"]["route_unmapped_need_count"] == 1
    assert bridge["summary"]["high_priority_route_blocked_count"] == 1
    assert row["release_decision_effect"] == "blocks_default_changes"
    assert "high_priority_route_unmapped" in row["route_blocker_codes"]


def test_model_ops_user_need_release_bridge_keeps_medium_implementation_blocker_as_review():
    bridge = ModelOpsUserNeedReleaseBridgeService().build_bridge(
        _base_signals(priority_band="medium", implementation_status="blocked", route_status="ready")
    )

    assert bridge["status"] == "review_required"
    assert bridge["summary"]["blocked_need_count"] == 0
    assert bridge["summary"]["default_change_allowed"] is True
    assert bridge["warning_check_ids"] == ["modelops-user-need-release-synthetic-need"]


def test_model_ops_user_need_release_bridge_ready_input_passes_without_network_or_raw_text():
    bridge = ModelOpsUserNeedReleaseBridgeService().build_bridge(_base_signals())
    serialized = str(bridge).lower()

    assert bridge["status"] == "ready"
    assert bridge["summary"]["ready_need_count"] == 1
    assert bridge["summary"]["configuration_written"] is False
    assert bridge["summary"]["network_called"] is False
    assert bridge["privacy_boundary"]["metadata_only"] is True
    assert bridge["privacy_boundary"]["model_calls"] is False
    assert bridge["privacy_boundary"]["gateway_calls"] is False
    assert bridge["privacy_boundary"]["returns_raw_legal_text"] is False
    assert bridge["claim_boundary"]["claims_public_benchmark_scores"] is False
    assert bridge["claim_boundary"]["claims_default_route_changed"] is False
    assert "service agreement. alpha service provider" not in serialized
    assert "borrower id number" not in serialized
    assert SENSITIVE_PATTERN.search(serialized) is None


def test_model_ops_user_need_release_bridge_aihub_route_returns_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models/user-need-release-bridge")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-user-need-release-bridge"
    assert payload["data"]["summary"]["network_called"] is False
    assert payload["data"]["source_boundaries"]["changes_default_routes"] is False
