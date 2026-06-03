import re

from services.case_team_access_policy import CaseTeamAccessPolicyService


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


def _policy() -> dict:
    return CaseTeamAccessPolicyService().build_policy()


def test_case_team_access_policy_covers_core_roles():
    policy = _policy()
    roles = {item["role"] for item in policy["role_matrix"]}

    assert policy["status"] == "ready"
    assert {"owner", "lawyer", "paralegal", "reviewer", "client"}.issubset(roles)
    assert policy["summary"]["role_count"] >= 5
    assert policy["summary"]["default_posture"] == "deny_by_default"


def test_client_permissions_are_minimized():
    policy = _policy()
    client_role = next(item for item in policy["role_matrix"] if item["role"] == "client")

    assert client_role["default_scope"] == "client_shared_items_only"
    assert set(client_role["allowed_actions"]) == {
        "view_shared_deliverables",
        "answer_fact_requests",
        "comment_on_shared_items",
    }
    assert "view_internal_notes" in client_role["denied_actions"]
    assert "run_ai_review" in client_role["denied_actions"]
    assert "export_full_case_file" in client_role["denied_actions"]
    assert "Client access is limited" in " ".join(policy["least_privilege_defaults"])


def test_sensitive_operations_require_audit():
    policy = _policy()
    sensitive_operations = policy["sensitive_operations"]

    assert sensitive_operations
    assert all(item["audit_required"] is True for item in sensitive_operations)
    assert any(item["operation"] == "external_share" and item["approval_required"] is True for item in sensitive_operations)
    assert any(item["operation"] == "bulk_delete_materials" and item["allowed_roles"] == ("owner",) for item in sensitive_operations)
    assert any(item["event"] == "sensitive_operation_attempted" for item in policy["audit_log_requirements"])


def test_policy_payload_has_no_sensitive_data_patterns():
    payload = _policy()

    assert not SENSITIVE_DATA_PATTERN.search(str(payload))
    assert "raw contact details" in " ".join(payload["privacy_and_firm_compliance"])
    assert payload["validation_commands"]


def test_case_team_access_policy_route_returns_policy():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/case-team-access-policy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["default_posture"] == "deny_by_default"
