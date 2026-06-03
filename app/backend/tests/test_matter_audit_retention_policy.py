import re

from services.matter_audit_retention_policy import MatterAuditRetentionPolicyService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password", re.IGNORECASE)


def _ready_events() -> list[dict]:
    return [
        {
            "event_type": "case_access_changed",
            "event_id": "event-1",
            "matter_id": "matter-1",
            "actor_id": "user-1",
            "target_member_id": "user-2",
            "role": "lawyer",
            "decision": "granted",
            "timestamp": "2026-06-03T00:00:00Z",
        },
        {
            "event_type": "ai_review_started",
            "event_id": "event-2",
            "matter_id": "matter-1",
            "actor_id": "user-1",
            "route_id": "cheap-first",
            "purpose": "contract-review",
            "timestamp": "2026-06-03T00:01:00Z",
        },
        {
            "event_type": "lawyer_review_decision",
            "event_id": "event-3",
            "matter_id": "matter-1",
            "reviewer_id": "lawyer-1",
            "decision": "approved",
            "version_id": "version-1",
            "timestamp": "2026-06-03T00:02:00Z",
        },
        {
            "event_type": "client_delivery_exported",
            "event_id": "event-4",
            "matter_id": "matter-1",
            "actor_id": "lawyer-1",
            "version_id": "version-1",
            "export_format": "pdf",
            "redaction_status": "pass",
            "timestamp": "2026-06-03T00:03:00Z",
        },
        {
            "event_type": "sensitive_operation_denied",
            "event_id": "event-5",
            "matter_id": "matter-1",
            "actor_id": "assistant-1",
            "operation": "external_share",
            "reason": "insufficient_role",
            "timestamp": "2026-06-03T00:04:00Z",
        },
    ]


def test_matter_audit_retention_policy_returns_template():
    policy = MatterAuditRetentionPolicyService().build_policy()

    assert policy["status"] == "template"
    assert policy["summary"]["event_type_count"] >= 5
    assert policy["summary"]["privacy_minimized"] is True
    assert any(item["event_type"] == "client_delivery_exported" for item in policy["event_policies"])


def test_matter_audit_retention_policy_accepts_ready_metadata():
    policy = MatterAuditRetentionPolicyService().build_policy(_ready_events())

    assert policy["status"] == "ready"
    assert policy["summary"]["blocking_issue_count"] == 0
    assert all(item["status"] == "pass" for item in policy["event_policies"])


def test_matter_audit_retention_policy_blocks_missing_required_fields():
    events = _ready_events()
    events[2].pop("reviewer_id")

    policy = MatterAuditRetentionPolicyService().build_policy(events)
    blockers = {item["event_type"]: item for item in policy["blocking_items"]}

    assert policy["status"] == "blocked"
    assert "lawyer_review_decision" in blockers
    assert "reviewer_id" in blockers["lawyer_review_decision"]["missing_fields"]


def test_matter_audit_retention_policy_blocks_forbidden_fields():
    events = _ready_events()
    events[1]["raw_prompt"] = "full prompt should not be stored"

    policy = MatterAuditRetentionPolicyService().build_policy(events)
    blockers = {item["event_type"]: item for item in policy["blocking_items"]}

    assert policy["status"] == "blocked"
    assert "ai_review_started" in blockers
    assert "raw_prompt" in blockers["ai_review_started"]["forbidden_fields_present"]


def test_matter_audit_retention_policy_has_no_secret_patterns():
    policy = MatterAuditRetentionPolicyService().build_policy(_ready_events())

    assert "metadata-only" in policy["privacy_note"]
    assert not SECRET_PATTERN.search(str(policy))


def test_matter_audit_retention_policy_route_returns_template_and_evaluation():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/matter-audit-retention-policy")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "template"

    post_response = client.post("/api/v1/maintenance/matter-audit-retention-policy", json=_ready_events())
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
