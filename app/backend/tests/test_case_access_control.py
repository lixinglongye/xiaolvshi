import json
from types import SimpleNamespace

from models.cases import Cases
from services.case_access_control import CaseAccessControlService


def _user(user_id: str, email: str = "user@example.test", name: str = "User", role: str = "user"):
    return SimpleNamespace(id=user_id, email=email, name=name, role=role)


def _case(**overrides):
    data = {
        "id": 101,
        "user_id": "owner-user",
        "title": "Runtime permission case",
        "team_members": json.dumps(
            [
                {"user_id": "lawyer-user", "role": "lawyer"},
                {"email": "reviewer@example.test", "role": "reviewer"},
                {"name": "Case Assistant", "role": "paralegal"},
                {"user_id": "client-user", "role": "client"},
            ]
        ),
    }
    data.update(overrides)
    return Cases(**data)


def test_case_access_control_resolves_owner_and_team_roles_without_echoing_members():
    service = CaseAccessControlService()
    case = _case()

    owner = service.evaluate(case, _user("owner-user"), "write")
    lawyer = service.evaluate(case, _user("lawyer-user"), "write")
    reviewer = service.evaluate(case, _user("reviewer-user", "reviewer@example.test"), "write")
    assistant = service.evaluate(case, _user("assistant-user", name="Case Assistant"), "write")
    client_export = service.evaluate(case, _user("client-user"), "export")

    assert owner["allowed"] is True
    assert owner["actor_role"] == "owner"
    assert lawyer["allowed"] is True
    assert lawyer["actor_role"] == "lawyer"
    assert reviewer["allowed"] is False
    assert reviewer["status"] == "denied"
    assert assistant["allowed"] is False
    assert assistant["status"] == "requires_approval"
    assert assistant["approval_gate"] == "lawyer_or_owner_write_approval"
    assert client_export["allowed"] is False
    assert client_export["status"] == "denied"

    rendered = json.dumps(service.build_permissions_summary(case, _user("lawyer-user")), ensure_ascii=False)
    assert "reviewer@example.test" not in rendered
    assert "Case Assistant" not in rendered
    assert "Runtime permission case" not in rendered
    assert "team_member_raw_text" in rendered


def test_unknown_case_actor_is_denied_by_default():
    decision = CaseAccessControlService().evaluate(_case(), _user("outsider-user"), "read")

    assert decision["allowed"] is False
    assert decision["status"] == "denied"
    assert decision["actor_role"] == "unknown"
    assert decision["role_source"] == "no_case_assignment"
    assert decision["privacy_safe"] is True


def test_unknown_operation_is_denied_instead_of_falling_back_to_read():
    decision = CaseAccessControlService().evaluate(_case(), _user("lawyer-user"), "dangerous_bulk_action")

    assert decision["allowed"] is False
    assert decision["status"] == "denied"
    assert decision["operation"] == "dangerous_bulk_action"
    assert decision["reason"] == "unknown_role_or_operation"


def test_case_access_control_accepts_legacy_comma_team_member_format():
    case = _case(
        team_members=(
            "legacy-lawyer:lawyer, reviewer@example.test (reviewer), "
            "paralegal-user assistant, chinese-lawyer \u5f8b\u5e08"
        )
    )
    service = CaseAccessControlService()

    assert service.evaluate(case, _user("legacy-lawyer"), "write")["allowed"] is True
    assert service.evaluate(case, _user("chinese-lawyer"), "write")["actor_role"] == "lawyer"
    assert service.evaluate(case, _user("reviewer-id", "reviewer@example.test"), "review")["allowed"] is True
    assistant = service.evaluate(case, _user("paralegal-user"), "write")
    assert assistant["status"] == "requires_approval"
