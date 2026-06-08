import re

from services.model_ops_user_need_cheap_first_handoff import ModelOpsUserNeedCheapFirstHandoffService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+"
)


def _base_signals(
    *,
    priority_band: str = "high",
    implementation_status: str = "ready",
    route_status: str = "ready",
):
    need_id = "synthetic-need"
    release_status = "blocked" if priority_band == "high" and route_status in {"blocked", "unmapped"} else "ready"
    if implementation_status == "blocked" and priority_band == "high":
        release_status = "blocked"
    if release_status != "blocked" and (implementation_status == "review_required" or route_status == "review_required"):
        release_status = "review_required"
    implementation_blockers = ["high-priority-local-fixture-missing"] if implementation_status == "blocked" else []
    route_blockers = ["high_priority_route_unmapped"] if route_status in {"blocked", "unmapped"} else []
    release_effect = "blocks_default_changes" if release_status == "blocked" else "supports_current_defaults"

    return {
        "user_need_benchmark_coverage": {
            "status": "ready",
            "summary": {"need_count": 1, "high_priority_need_count": 1 if priority_band == "high" else 0},
        },
        "user_need_implementation_priority_queue": {
            "status": implementation_status,
            "summary": {
                "queue_item_count": 1,
                "blocked_action_count": 1 if implementation_status == "blocked" else 0,
                "review_required_action_count": 1 if implementation_status == "review_required" else 0,
            },
            "blocked_need_ids": [need_id] if implementation_status == "blocked" else [],
            "review_need_ids": [need_id] if implementation_status == "review_required" else [],
        },
        "user_need_gemini_route_coverage": {
            "status": route_status,
            "summary": {
                "need_count": 1,
                "high_priority_route_protected_count": 1 if route_status == "ready" else 0,
                "premium_exception_need_count": 0,
            },
            "blocked_need_ids": [need_id] if route_status in {"blocked", "unmapped"} else [],
            "review_need_ids": [need_id] if route_status == "review_required" else [],
        },
        "user_need_release_bridge": {
            "id": "modelops-user-need-release-bridge",
            "status": release_status,
            "summary": {
                "need_count": 1,
                "default_change_allowed": release_status != "blocked",
                "maintainer_review_required": release_status == "review_required",
            },
            "bridge_rows": [
                {
                    "id": f"modelops-user-need-release-{need_id}",
                    "need_id": need_id,
                    "title": "Synthetic need",
                    "category": "release",
                    "priority_band": priority_band,
                    "priority_score": 90,
                    "release_priority_score": 100 if release_status == "blocked" else 75,
                    "release_bridge_status": release_status,
                    "release_decision_effect": release_effect,
                    "default_allowed_without_review": release_status == "ready",
                    "high_frequency_route_ready": route_status == "ready",
                    "implementation_action_status": implementation_status,
                    "route_coverage_status": route_status,
                    "linked_route_tasks": ["fast", "classification"],
                    "linked_default_models": ["gemini-2.5-flash-lite"],
                    "linked_release_gates": ["modelops-user-need-release-bridge"],
                    "implementation_blocker_codes": implementation_blockers,
                    "route_blocker_codes": route_blockers,
                    "review_reason_codes": [],
                    "next_action": "Keep route coverage attached.",
                }
            ],
        },
    }


def test_model_ops_user_need_cheap_first_handoff_summarizes_current_review_state():
    handoff = ModelOpsUserNeedCheapFirstHandoffService().build_handoff()
    rows = {row["need_id"]: row for row in handoff["handoff_rows"]}

    assert handoff["id"] == "modelops-user-need-cheap-first-handoff"
    assert handoff["title"] == "ModelOps user-need cheap-first handoff"
    assert handoff["status"] == "review_required"
    assert handoff["summary"]["need_count"] >= 7
    assert handoff["summary"]["blocked_need_count"] == 0
    assert handoff["summary"]["review_required_need_count"] >= 1
    assert handoff["summary"]["default_change_allowed"] is True
    assert handoff["summary"]["maintainer_review_required"] is True
    assert handoff["summary"]["gateway_called"] is False
    assert handoff["summary"]["configuration_written"] is False
    assert handoff["reviewer_handoff"]["primary_endpoint"] == "/api/v1/aihub/models/user-need-cheap-first-handoff"
    assert len(handoff["handoff_sections"]) == 4
    assert {
        section["id"] for section in handoff["handoff_sections"]
    } == {
        "user-need-benchmark-coverage",
        "user-need-implementation-priority-queue",
        "user-need-gemini-route-coverage",
        "modelops-user-need-release-bridge",
    }

    feedback = rows["feedback-to-roadmap-loop"]
    assert feedback["handoff_status"] == "review_required"
    assert feedback["cheap_first_route_protected"] is True
    assert "modelops-user-need-release-bridge" in feedback["linked_release_gates"]


def test_model_ops_user_need_cheap_first_handoff_blocks_high_priority_route_gap():
    handoff = ModelOpsUserNeedCheapFirstHandoffService().build_handoff(
        _base_signals(priority_band="high", implementation_status="ready", route_status="unmapped")
    )
    row = handoff["handoff_rows"][0]

    assert handoff["status"] == "blocked"
    assert handoff["summary"]["default_change_allowed"] is False
    assert handoff["summary"]["default_change_blocked"] is True
    assert row["release_decision_effect"] == "blocks_default_changes"
    assert row["reviewer_action"] == "Clear blocking implementation or route evidence before cheap-first default promotion."
    assert "high_priority_route_unmapped" in row["route_blocker_codes"]


def test_model_ops_user_need_cheap_first_handoff_ready_input_is_metadata_only():
    handoff = ModelOpsUserNeedCheapFirstHandoffService().build_handoff(_base_signals())
    serialized = str(handoff).lower()

    assert handoff["status"] == "ready"
    assert handoff["summary"]["ready_need_count"] == 1
    assert handoff["summary"]["cheap_first_route_protected_need_count"] == 1
    assert handoff["summary"]["model_calls"] == "not_required"
    assert handoff["summary"]["network_called"] is False
    assert handoff["summary"]["traffic_shifted"] is False
    assert handoff["privacy_boundary"]["metadata_only"] is True
    assert handoff["privacy_boundary"]["model_calls"] is False
    assert handoff["privacy_boundary"]["gateway_calls"] is False
    assert handoff["privacy_boundary"]["returns_raw_legal_text"] is False
    assert handoff["claim_boundary"]["claims_public_benchmark_scores"] is False
    assert handoff["claim_boundary"]["claims_default_route_changed"] is False
    assert "service agreement. alpha service provider" not in serialized
    assert "borrower id number" not in serialized
    assert SENSITIVE_PATTERN.search(serialized) is None


def test_model_ops_user_need_cheap_first_handoff_scrubs_sensitive_signal_labels():
    signals = _base_signals()
    bridge_row = signals["user_need_release_bridge"]["bridge_rows"][0]
    bridge_row["need_id"] = "owner@example.com"
    bridge_row["title"] = "api_key " + "sk-" + "abcdefghijklmnopqrstuvwxyz123456"
    bridge_row["linked_default_models"] = ["gemini-2.5-flash-lite", "ops@example.com"]

    handoff = ModelOpsUserNeedCheapFirstHandoffService().build_handoff(signals)
    serialized = str(handoff)

    assert handoff["handoff_rows"][0]["need_id"] == "unknown"
    assert handoff["handoff_rows"][0]["title"] == "Untitled user need"
    assert "ops@example.com" not in serialized
    assert SENSITIVE_PATTERN.search(serialized) is None


def test_model_ops_user_need_cheap_first_handoff_routes_return_payloads():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router
    from routers.maintenance import router as maintenance_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    app.include_router(maintenance_router)
    client = testclient.TestClient(app)

    aihub_response = client.get("/api/v1/aihub/models/user-need-cheap-first-handoff")
    maintenance_response = client.get("/api/v1/maintenance/user-needs/cheap-first-evidence-handoff")

    assert aihub_response.status_code == 200
    assert maintenance_response.status_code == 200
    assert aihub_response.json()["data"]["id"] == "modelops-user-need-cheap-first-handoff"
    assert maintenance_response.json()["data"]["id"] == "modelops-user-need-cheap-first-handoff"
    assert aihub_response.json()["data"]["source_boundaries"]["changes_default_routes"] is False
    assert maintenance_response.json()["data"]["privacy_boundary"]["network_access"] is False
