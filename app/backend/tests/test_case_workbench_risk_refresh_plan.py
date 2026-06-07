import json

from services.case_workbench_risk_refresh_plan import CaseWorkbenchRiskRefreshPlanService


def test_risk_refresh_plan_is_empty_without_runtime_state():
    plan = CaseWorkbenchRiskRefreshPlanService().build_plan({"sections": {}})

    assert plan["id"] == "case-workbench-risk-refresh-plan"
    assert plan["status"] == "empty"
    assert plan["summary"]["refresh_required_count"] == 0
    assert plan["summary"]["risk_state_badge_count"] == 1
    assert plan["risk_state_badge_summary"]["watch_count"] == 1
    assert plan["risk_state_badges"][0]["id"] == "risk-state-empty"
    assert plan["risk_state_badges"][0]["writes_risk_state"] is False
    assert plan["summary"]["risk_state_written"] is False
    assert plan["summary"]["evidence_graph_written"] is False
    assert plan["privacy_boundary"]["returns_raw_event_payload"] is False
    assert plan["claim_boundary"]["live_risk_state_updated"] is False


def test_risk_refresh_plan_flags_blocking_task_and_fact_event_without_echoing_raw_payload():
    plan = CaseWorkbenchRiskRefreshPlanService().build_plan(
        {
            "sections": {
                "tasks": {
                    "status": "ready",
                    "state_version": 3,
                    "latest_event_id": "event-task-003",
                    "validation_status": "pass",
                    "summary": {"task_count": 1, "active_count": 1, "review_required_count": 1},
                    "collection_counts": {"task_states": 1},
                    "state": {
                        "task_states": [
                            {
                                "task_ref_hash": "task_hash_refresh_001",
                                "status": "blocked",
                                "priority": "high",
                                "blocker_codes": ["missing_evidence_link"],
                            }
                        ]
                    },
                },
                "facts": {
                    "status": "ready",
                    "state_version": 2,
                    "latest_event_id": "event-fact-002",
                    "validation_status": "pass",
                    "summary": {"fact_count": 1, "review_required_count": 0},
                    "collection_counts": {"fact_states": 1},
                    "state": {},
                },
            }
        },
        [
            {
                "event_id": "event-fact-002",
                "section": "facts",
                "operation": "upsert_snapshot",
                "state_version": 2,
                "validation_status": "pass",
                "event_json": {
                    "changed_item_refs": ["fact_hash_001"],
                    "changed_field_names": ["fact_ref_hash", "materiality", "source_evidence_refs"],
                    "output_text": "raw text must not leak",
                },
            }
        ],
    )
    serialized = json.dumps(plan, ensure_ascii=False)

    assert plan["status"] == "blocked"
    assert "tasks" in plan["blocking_section_ids"]
    assert "facts" in plan["refresh_required_section_ids"]
    assert "event-fact-002" in plan["risk_affecting_event_ids"]
    assert "event-fact-002" in plan["evidence_graph_affecting_event_ids"]
    assert plan["summary"]["task_blocked_count"] == 1
    assert plan["summary"]["risk_affecting_event_count"] == 1
    assert plan["risk_state_badge_summary"]["critical_count"] == 1
    assert plan["risk_state_badge_summary"]["warning_count"] == 1
    badge_ids = {badge["id"] for badge in plan["risk_state_badges"]}
    assert "blocked-task-review" in badge_ids
    assert "runtime-event-risk-refresh" in badge_ids
    blocked_badge = next(badge for badge in plan["risk_state_badges"] if badge["id"] == "blocked-task-review")
    assert blocked_badge["severity"] == "critical"
    assert blocked_badge["source"] == "tasks"
    assert blocked_badge["raw_content_returned"] is False
    assert plan["evidence_graph_plan"]["status"] == "refresh_required"
    assert "raw text must not leak" not in serialized
    assert "output_text" not in serialized
    assert "event_json" not in serialized


def test_risk_refresh_plan_keeps_privacy_and_claim_boundaries_closed():
    plan = CaseWorkbenchRiskRefreshPlanService().build_plan(
        {
            "sections": {
                "evidence_graph": {
                    "status": "ready",
                    "state_version": 1,
                    "summary": {"node_count": 2, "edge_count": 1, "blocking_gap_count": 1},
                    "collection_counts": {"graph_nodes": 2, "graph_edges": 1},
                    "state": {},
                }
            }
        }
    )

    assert plan["status"] == "blocked"
    badge = next(item for item in plan["risk_state_badges"] if item["id"] == "blocking-evidence-gap")
    assert badge["severity"] == "critical"
    assert badge["count"] == 1
    assert badge["writes_evidence_graph"] is False
    assert plan["privacy_boundary"]["returns_raw_evidence_text"] is False
    assert plan["privacy_boundary"]["returns_risk_state_badges"] is True
    assert plan["privacy_boundary"]["writes_evidence_graph"] is False
    assert plan["privacy_boundary"]["sends_notifications"] is False
    assert plan["claim_boundary"]["evidence_graph_refreshed"] is False
    assert plan["claim_boundary"]["client_notification_sent"] is False
