import json
import re
from pathlib import Path

from services.case_role_permission_matrix import (
    DECISION_ALLOW,
    DECISION_DENY,
    DECISION_REQUIRES_APPROVAL,
    DECISIONS,
    OPERATIONS,
    ROLES,
    CaseRolePermissionMatrixService,
)


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\b\d{13,19}\b)",
    re.IGNORECASE,
)


def _payload() -> dict:
    return CaseRolePermissionMatrixService().build_privacy_safe_api_payload()


def test_case_role_permission_matrix_covers_required_roles_and_operations():
    payload = _payload()

    assert payload["status"] == "ready"
    assert payload["roles"] == ROLES
    assert payload["operations"] == OPERATIONS
    assert {"owner", "lawyer", "reviewer", "assistant", "client", "admin"}.issubset(payload["roles"])
    assert {"read", "write", "export", "share", "billing", "audit", "review"}.issubset(payload["operations"])
    assert payload["decision_values"] == DECISIONS
    assert payload["summary"]["permission_count"] == len(ROLES) * len(OPERATIONS)

    matrix = payload["matrix"]
    for role in ROLES:
        assert set(matrix[role]) == set(OPERATIONS)
        assert set(matrix[role].values()).issubset(set(DECISIONS))


def test_core_role_decisions_match_least_privilege_expectations():
    matrix = _payload()["matrix"]

    assert matrix["owner"]["read"] == DECISION_ALLOW
    assert matrix["owner"]["write"] == DECISION_ALLOW
    assert matrix["owner"]["billing"] == DECISION_ALLOW
    assert matrix["owner"]["export"] == DECISION_REQUIRES_APPROVAL
    assert matrix["owner"]["share"] == DECISION_REQUIRES_APPROVAL

    assert matrix["lawyer"]["read"] == DECISION_ALLOW
    assert matrix["lawyer"]["write"] == DECISION_ALLOW
    assert matrix["lawyer"]["review"] == DECISION_ALLOW
    assert matrix["lawyer"]["billing"] == DECISION_DENY
    assert matrix["lawyer"]["export"] == DECISION_REQUIRES_APPROVAL
    assert matrix["lawyer"]["share"] == DECISION_REQUIRES_APPROVAL

    assert matrix["reviewer"]["review"] == DECISION_ALLOW
    assert matrix["reviewer"]["write"] == DECISION_DENY
    assert matrix["assistant"]["write"] == DECISION_REQUIRES_APPROVAL
    assert matrix["client"]["write"] == DECISION_REQUIRES_APPROVAL
    assert matrix["admin"]["read"] == DECISION_REQUIRES_APPROVAL
    assert matrix["admin"]["billing"] == DECISION_ALLOW


def test_role_summaries_are_derived_from_matrix():
    payload = _payload()
    summaries = {item["role"]: item for item in payload["role_summaries"]}

    assert set(summaries) == set(ROLES)
    assert set(summaries["client"]["allowed_operations"]) == {"read"}
    assert set(summaries["client"]["approval_required_operations"]) == {"write"}
    assert {"export", "share", "billing", "audit", "review"}.issubset(summaries["client"]["denied_operations"])
    assert summaries["client"]["default_scope"] == "client_shared_items_only"
    assert "internal notes" in summaries["client"]["privacy_boundary"]

    assert summaries["assistant"]["approval_required_operations"] == ("write",)
    assert set(summaries["admin"]["allowed_operations"]) == {"billing", "audit"}


def test_forbidden_combinations_only_include_denied_rules():
    payload = _payload()
    forbidden = payload["forbidden_combinations"]
    forbidden_pairs = {(item["role"], item["operation"]) for item in forbidden}

    assert forbidden
    assert payload["summary"]["forbidden_combination_count"] == len(forbidden)
    assert all(item["decision"] == DECISION_DENY for item in forbidden)
    assert ("client", "export") in forbidden_pairs
    assert ("client", "audit") in forbidden_pairs
    assert ("assistant", "share") in forbidden_pairs
    assert ("admin", "export") in forbidden_pairs
    assert ("owner", "read") not in forbidden_pairs
    assert ("owner", "share") not in forbidden_pairs


def test_evaluate_permission_returns_privacy_safe_decisions():
    service = CaseRolePermissionMatrixService()

    approved = service.evaluate_permission("Lawyer", "Review")
    assert approved["status"] == "allowed"
    assert approved["decision"] == DECISION_ALLOW
    assert approved["privacy_safe"] is True

    gated = service.evaluate_permission("admin", "read")
    assert gated["status"] == "requires_approval"
    assert gated["approval_gate"] == "owner_or_security_break_glass_approval"

    denied = service.evaluate_permission("guest", "export")
    assert denied["status"] == "denied"
    assert denied["decision"] == DECISION_DENY
    assert denied["reason"] == "unknown_role_or_operation"
    assert denied["privacy_safe"] is True


def test_privacy_safe_api_payload_has_no_sensitive_data_patterns():
    payload = _payload()
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["summary"]["privacy_safe"] is True
    assert payload["privacy_safe_api_payload"]["forbidden_fields"]
    assert not SENSITIVE_DATA_PATTERN.search(serialized)
    assert "case_narratives" in payload["scope"]["does_not_include"]
    assert "direct_contact_details" in payload["privacy_safe_api_payload"]["forbidden_fields"]


def test_validation_commands_and_documentation_are_present():
    payload = _payload()
    commands = payload["validation_commands"]

    assert "python -m pytest tests/test_case_role_permission_matrix.py -q" in commands
    assert any("compileall" in command for command in commands)

    repo_root = Path(__file__).resolve().parents[3]
    doc = repo_root / "docs" / "CASE_ROLE_PERMISSION_MATRIX.md"
    content = doc.read_text(encoding="utf-8")

    assert "Case Role Permission Matrix" in content
    assert "owner/lawyer/reviewer/assistant/client/admin" in content
    assert "python -m pytest tests/test_case_role_permission_matrix.py -q" in content
    assert "python -m compileall services/case_role_permission_matrix.py tests/test_case_role_permission_matrix.py" in content


def test_case_role_permission_matrix_route_returns_matrix_and_decision():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/case-role-permission-matrix")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ready"

    decision = client.post(
        "/api/v1/maintenance/case-role-permission-matrix",
        json={"role": "lawyer", "operation": "review"},
    )

    assert decision.status_code == 200
    assert decision.json()["data"]["status"] == "allowed"
