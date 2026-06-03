import json
import re

from services.lawyer_review_workflow_policy import (
    REVIEW_WORKFLOW_STATUSES,
    LawyerReviewWorkflowPolicyService,
)


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    + "pass"
    + r"word)",
    re.IGNORECASE,
)


def _policy(payload: dict | None = None) -> dict:
    return LawyerReviewWorkflowPolicyService().build_policy(payload)


def test_lawyer_review_workflow_policy_contains_required_sections():
    policy = _policy()
    statuses = {item["status"] for item in policy["state_enumeration"]}

    assert policy["status"] == "ready"
    assert policy["policy_id"] == "lawyer-review-workflow-policy-v1"
    assert statuses == set(REVIEW_WORKFLOW_STATUSES)
    assert policy["allowed_state_transitions"]
    assert policy["forbidden_state_transitions"]
    assert policy["role_requirements"]
    assert policy["audit_log_requirements"]
    assert policy["low_resource_validation_commands"]
    assert policy["privacy_notes"]


def test_draft_cannot_transition_directly_to_client_deliverable():
    policy = _policy()
    direct_transition = [
        item
        for item in policy["allowed_state_transitions"]
        if item["from_status"] == "draft" and item["to_status"] == "client_deliverable"
    ]
    forbidden = [
        item
        for item in policy["forbidden_state_transitions"]
        if item["from_status"] == "draft" and item["to_status"] == "client_deliverable"
    ]

    assert direct_transition == []
    assert forbidden
    assert policy["summary"]["draft_direct_to_client_deliverable_allowed"] is False

    evaluated = _policy(
        {
            "from_status": "draft",
            "to_status": "client_deliverable",
            "actor_role": "lawyer",
            "artifact_id": "artifact-001",
        }
    )

    assert any(item["code"] == "transition_not_allowed" for item in evaluated["blocking_conditions"])


def test_approved_to_client_deliverable_requires_lawyer_role():
    policy = _policy()
    release_transition = next(
        item
        for item in policy["allowed_state_transitions"]
        if item["from_status"] == "approved" and item["to_status"] == "client_deliverable"
    )

    assert set(release_transition["allowed_roles"]) == {"lawyer", "owner"}
    assert "paralegal" not in release_transition["allowed_roles"]

    denied = _policy(
        {
            "from_status": "approved",
            "to_status": "client_deliverable",
            "actor_role": "paralegal",
            "artifact_id": "artifact-001",
            "approved_at": "2026-06-04T08:00:00Z",
            "release_channel": "client_portal",
        }
    )
    approved = _policy(
        {
            "from_status": "approved",
            "to_status": "client_deliverable",
            "actor_role": "lawyer",
            "artifact_id": "artifact-001",
            "approved_at": "2026-06-04T08:00:00Z",
            "release_channel": "client_portal",
        }
    )

    assert any(item["code"] == "role_not_allowed" for item in denied["blocking_conditions"])
    assert approved["blocking_conditions"] == []


def test_reject_and_revise_required_transitions_require_reason():
    policy = _policy()
    decision_transitions = [
        item
        for item in policy["allowed_state_transitions"]
        if item["to_status"] in {"rejected", "revise_required"}
    ]

    assert {item["to_status"] for item in decision_transitions} == {"rejected", "revise_required"}
    assert all(item["reason_required"] is True for item in decision_transitions)
    assert all("reason" in item["required_fields"] for item in decision_transitions)

    for target_status in ("rejected", "revise_required"):
        evaluated = _policy(
            {
                "from_status": "lawyer_review",
                "to_status": target_status,
                "actor_role": "lawyer",
                "artifact_id": "artifact-001",
                "reviewer_id": "reviewer-001",
            }
        )
        blocker_codes = {item["code"] for item in evaluated["blocking_conditions"]}

        assert "reason_required" in blocker_codes
        assert "missing_required_fields" in blocker_codes


def test_lawyer_review_workflow_payload_has_no_sensitive_data_patterns():
    payload = json.dumps(_policy(), ensure_ascii=False)

    assert not SENSITIVE_DATA_PATTERN.search(payload)


def test_lawyer_review_workflow_policy_route_returns_policy_and_blocker():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/lawyer-review-workflow-policy")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["summary"]["draft_direct_to_client_deliverable_allowed"] is False

    post_response = client.post(
        "/api/v1/maintenance/lawyer-review-workflow-policy",
        json={"from_status": "draft", "to_status": "client_deliverable", "actor_role": "lawyer"},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["blocking_conditions"][0]["code"] == "transition_not_allowed"
