import json
import re

from services.case_task_notification_policy import CaseTaskNotificationPolicyService


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


def _policy(tasks=None) -> dict:
    return CaseTaskNotificationPolicyService().build_policy(tasks)


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
