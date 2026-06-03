import json
import re

from services.case_task_notification_policy import CaseTaskNotificationPolicyService


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


def _policy(tasks=None) -> dict:
    return CaseTaskNotificationPolicyService().build_policy(tasks)


def _runtime_summary(events=None) -> dict:
    return CaseTaskNotificationPolicyService().build_runtime_event_policy_summary(events)


def test_policy_contains_required_metadata_sections():
    policy = _policy()

    assert policy["status"] == "ready"
    assert policy["policy_id"] == "case-task-notification-policy-v1"
    assert policy["notification_channels"]
    assert policy["trigger_rules"]
    assert policy["escalation_rules"]
    assert policy["owner_assignment_requirements"]
    assert policy["blocking_urgent_tasks"] == []
    assert policy["low_resource_validation_commands"]
    assert policy["privacy_notes"]


def test_days_until_due_one_triggers_urgent_escalation():
    policy = _policy(
        [
            {
                "case_id": "case-1",
                "task_id": "task-urgent",
                "status": "open",
                "priority": "normal",
                "days_until_due": 1,
                "owner_id": "member-1",
            }
        ]
    )

    assert policy["summary"]["urgent_escalation_count"] == 1
    assert policy["summary"]["blocking_urgent_count"] == 1
    urgent_task = policy["blocking_urgent_tasks"][0]
    assert urgent_task["task_id"] == "task-urgent"
    assert urgent_task["urgent_escalation"] is True
    assert "urgent-deadline-escalation" in urgent_task["triggers"]
    assert "team_escalation" in urgent_task["recommended_channels"]


def test_missing_owner_triggers_blocker():
    policy = _policy(
        [
            {
                "case_id": "case-2",
                "task_id": "task-ownerless",
                "status": "in_progress",
                "priority": "normal",
                "days_until_due": 5,
            }
        ]
    )

    assert policy["summary"]["missing_owner_count"] == 1
    blocker = policy["blocking_urgent_tasks"][0]
    assert blocker["task_id"] == "task-ownerless"
    assert blocker["owner_missing"] is True
    assert "missing-owner-blocker" in blocker["triggers"]
    assert "missing_owner" in blocker["blocking_reasons"]


def test_done_task_does_not_trigger_notification_or_blocker():
    policy = _policy(
        [
            {
                "case_id": "case-3",
                "task_id": "task-done",
                "status": "done",
                "priority": "critical",
                "days_until_due": 0,
            }
        ]
    )

    assert policy["summary"]["done_task_count"] == 1
    assert policy["summary"]["active_task_count"] == 0
    assert policy["summary"]["urgent_escalation_count"] == 0
    assert policy["notification_queue"] == []
    assert policy["blocking_urgent_tasks"] == []
    assert policy["evaluated_tasks"][0]["done"] is True
    assert policy["evaluated_tasks"][0]["triggers"] == []


def test_client_material_and_lawyer_review_reminders_are_visible():
    policy = _policy(
        [
            {
                "case_id": "case-4",
                "task_id": "task-client-materials",
                "status": "waiting_client",
                "priority": "normal",
                "days_until_due": 2,
                "owner_role": "lawyer",
                "requires_client_materials": True,
            },
            {
                "case_id": "case-4",
                "task_id": "task-review",
                "status": "review_needed",
                "priority": "high",
                "days_until_due": 4,
                "owner_role": "reviewer",
                "requires_lawyer_review": True,
            },
        ]
    )

    queued = {task["task_id"]: task for task in policy["notification_queue"]}

    assert "client-material-reminder" in queued["task-client-materials"]["triggers"]
    assert "client_portal" in queued["task-client-materials"]["recommended_channels"]
    assert "lawyer-review-reminder" in queued["task-review"]["triggers"]
    assert "review_queue" in queued["task-review"]["recommended_channels"]


def test_policy_payload_has_no_sensitive_data_patterns():
    payload = _policy(
        [
            {
                "case_id": "case-5",
                "task_id": "task-safe",
                "status": "open",
                "priority": "normal",
                "days_until_due": 3,
                "owner_role": "lawyer",
            }
        ]
    )
    serialized = json.dumps(payload, ensure_ascii=False)

    assert not SENSITIVE_DATA_PATTERN.search(serialized)


def test_runtime_task_status_event_builds_policy_suggestion_summary_without_dispatch():
    event = {
        "event_id": "cwp-event-task-status-001",
        "event_type": "case_workbench_state_event",
        "case_ref_hash": "case_hash_task_status_abcdefghijkl",
        "section": "tasks",
        "operation": "append_delta",
        "state_version": 3,
        "payload_kind": "metadata_delta",
        "changed_item_refs": ["task_hash_status_abcdefghijkl"],
        "changed_field_names": ["status", "priority", "due_date_status"],
        "state_delta": {
            "task_states": [
                {
                    "task_ref_hash": "task_hash_status_abcdefghijkl",
                    "task_type": "lawyer_review",
                    "status": "review_needed",
                    "priority": "normal",
                    "owner_role": "lawyer",
                    "due_date_status": "urgent",
                    "escalation_status": "requested",
                    "blocker_codes": ["evidence_gap"],
                    "review_required": True,
                    "raw_content": "Client narrative must not be copied",
                }
            ],
        },
        "message": "Do not notify someone@example.test with password details",
    }

    summary = _runtime_summary([event])
    serialized = json.dumps(summary, ensure_ascii=False)

    assert summary["status"] == "ready"
    assert summary["summary_id"] == "case-task-runtime-event-notification-summary-v1"
    assert summary["summary"]["task_status_event_count"] == 1
    assert summary["summary"]["task_state_count"] == 1
    assert summary["summary"]["dispatch_performed"] is False
    assert summary["summary"]["raw_text_stored"] is False
    assert summary["task_event_summaries"][0]["changed_task_refs"] == ["task_hash_status_abcdefghijkl"]
    assert summary["notification_suggestions"][0]["task_id"] == "task_hash_status_abcdefghijkl"
    escalation = summary["escalation_suggestions"][0]
    assert "urgent-deadline-escalation" in escalation["triggers"]
    assert "lawyer-review-reminder" in escalation["triggers"]
    assert "runtime-task-blocker-escalation" in escalation["triggers"]
    assert "team_escalation" in escalation["recommended_channels"]
    assert "Client narrative" not in serialized
    assert "someone@example.test" not in serialized
    assert "password" not in serialized


def test_runtime_summary_ignores_non_task_events_and_unsafe_refs():
    summary = _runtime_summary(
        [
            {
                "event_id": "cwp-event-facts-001",
                "case_ref_hash": "case_hash_facts_abcdefghijkl",
                "section": "facts",
                "operation": "append_delta",
                "state_version": 1,
                "payload_kind": "metadata_delta",
                "state_delta": {
                    "fact_states": [
                        {
                            "fact_ref_hash": "fact_hash_abcdefghijkl",
                            "fact_text": "Raw fact prose must not be copied",
                        }
                    ]
                },
            },
            {
                "event_id": "cwp-event-task-status-unsafe-001",
                "case_ref_hash": "case_hash_runtime_abcdefghijkl",
                "section": "tasks",
                "operation": "append_delta",
                "state_version": 2,
                "payload_kind": "metadata_delta",
                "changed_item_refs": ["bad ref with spaces"],
                "changed_field_names": ["status"],
                "state_delta": {
                    "task_states": [
                        {
                            "task_ref_hash": "raw task label with spaces",
                            "task_type": "client_material_request",
                            "status": "waiting_client",
                            "priority": "normal",
                            "owner_role": "lawyer",
                            "due_date_status": "near",
                        }
                    ]
                },
            },
        ]
    )
    serialized = json.dumps(summary, ensure_ascii=False)

    assert summary["summary"]["ignored_event_count"] == 1
    assert summary["summary"]["task_state_count"] == 1
    assert summary["task_event_summaries"][0]["changed_task_refs"] == []
    assert summary["notification_suggestions"][0]["task_id"] == "unknown-task-1"
    assert "client-material-reminder" in summary["notification_suggestions"][0]["triggers"]
    assert "due-soon-reminder" in summary["notification_suggestions"][0]["triggers"]
    assert "Raw fact prose" not in serialized
    assert "raw task label with spaces" not in serialized


def test_case_task_notification_policy_route_returns_template_and_escalation():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/case-task-notification-policy")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["policy_id"] == "case-task-notification-policy-v1"

    post_response = client.post(
        "/api/v1/maintenance/case-task-notification-policy",
        json=[
            {
                "case_id": "case-1",
                "task_id": "task-urgent",
                "status": "open",
                "days_until_due": 1,
                "owner_role": "lawyer",
            }
        ],
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["summary"]["urgent_escalation_count"] == 1
