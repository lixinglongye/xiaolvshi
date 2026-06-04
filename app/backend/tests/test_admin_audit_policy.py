import json

import pytest

from services.admin_audit_policy import AdminAuditPolicyService


PRIVATE_EMAIL = "admin-audit@example.test"


def test_admin_audit_policy_requires_approval_for_sensitive_actions_without_pii_echo():
    result = AdminAuditPolicyService().evaluate(
        [
            {"action_type": "delete_case", "actor_role": "assistant", "payload": PRIVATE_EMAIL},
            {"action_type": "view_dashboard", "actor_role": "admin"},
        ]
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "review_required"
    assert result["summary"]["approval_required_count"] == 1
    assert result["checks"][0]["risk_level"] == "high"
    assert "sensitive_action_requires_approval" in result["checks"][0]["reason_codes"]
    assert PRIVATE_EMAIL not in rendered


def test_admin_audit_policy_route():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/admin/audit-policy",
        json={"actions": [{"action_type": "override_quota", "actor_role": "admin"}]},
    )

    assert response.status_code == 200
    assert response.json()["data"]["summary"]["approval_required_count"] == 1
