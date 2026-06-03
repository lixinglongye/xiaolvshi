import json
import re

from services.client_delivery_transparency_policy import ClientDeliveryTransparencyPolicyService


SENSITIVE_PATTERN = re.compile(
    "|".join(
        [
            r"sk-[A-Za-z0-9]{20,}",
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            r"1[3-9]\d{9}",
            "pass" + "word",
            "sec" + "ret",
            "tok" + "en",
        ]
    ),
    re.IGNORECASE,
)


def _policy(payload: dict | None = None) -> dict:
    return ClientDeliveryTransparencyPolicyService().build_policy(payload)


def _valid_payload() -> dict:
    return {
        "artifact": {
            "artifact_id": "artifact-001",
            "current_version_id": "version-002",
            "previous_version_id": "version-001",
            "review_status": "approved",
        },
        "client_confirmation": {
            "status": "confirmed",
            "confirmed_at": "2026-06-04T08:00:00Z",
            "confirmed_version_id": "version-002",
            "method": "client_portal",
        },
        "version_diff": {
            "previous_version_id": "version-001",
            "summary_available": True,
            "client_visible": True,
            "diff_acknowledged": True,
            "material_change_count": 2,
        },
        "risk_notice": {
            "present": True,
            "client_visible": True,
            "acknowledged": True,
            "risk_level": "medium",
            "scope_limits": ["jurisdiction", "deadline"],
        },
        "delivery_record": {
            "record_id": "delivery-001",
            "delivery_channel": "client_portal",
            "prepared_at": "2026-06-04T08:10:00Z",
            "package_version_id": "version-002",
            "accountable_actor": "lawyer-001",
        },
        "follow_up_tasks": [
            {
                "task_id": "task-001",
                "owner_role": "lawyer",
                "due_at": "2026-06-05",
                "status": "open",
            }
        ],
    }


def test_client_delivery_transparency_policy_passes_complete_payload():
    policy = _policy(_valid_payload())
    statuses = {check["id"]: check["status"] for check in policy["checks"]}

    assert policy["status"] == "pass"
    assert policy["summary"]["delivery_allowed"] is True
    assert policy["summary"]["fail_count"] == 0
    assert set(statuses.values()) == {"pass"}
    assert all(gate["release_effect"] == "allow" for gate in policy["delivery_gates"])
    assert policy["recommended_actions"][0]["id"] == "release-with-transparent-audit"
    assert policy["privacy_note"]
    assert policy["validation_commands"]


def test_missing_client_confirmation_fails_delivery_gate():
    payload = _valid_payload()
    payload["client_confirmation"] = {}

    policy = _policy(payload)
    confirmation_check = next(check for check in policy["checks"] if check["id"] == "client-confirmation")
    confirmation_gate = next(gate for gate in policy["delivery_gates"] if gate["check_id"] == "client-confirmation")

    assert policy["status"] == "fail"
    assert policy["summary"]["delivery_allowed"] is False
    assert confirmation_check["status"] == "fail"
    assert "client_confirmation_missing" in confirmation_check["issue_codes"]
    assert "client_confirmation.status" in confirmation_check["missing_fields"]
    assert confirmation_gate["release_effect"] == "block"


def test_missing_risk_notice_fails_delivery_gate():
    payload = _valid_payload()
    payload["risk_notice"] = {"present": False, "client_visible": False, "acknowledged": False}

    policy = _policy(payload)
    risk_check = next(check for check in policy["checks"] if check["id"] == "risk-notice")

    assert policy["status"] == "fail"
    assert risk_check["status"] == "fail"
    assert {"risk_notice_missing", "risk_notice_not_client_visible", "risk_notice_not_acknowledged"}.issubset(
        set(risk_check["issue_codes"])
    )
    assert any(action["id"] == "resolve-risk-notice" for action in policy["recommended_actions"])


def test_missing_optional_follow_up_tasks_warns_when_not_required():
    payload = _valid_payload()
    payload.pop("follow_up_tasks")

    policy = _policy(payload)
    follow_up_check = next(check for check in policy["checks"] if check["id"] == "follow-up-tasks")

    assert policy["status"] == "warn"
    assert policy["summary"]["delivery_allowed"] is False
    assert follow_up_check["status"] == "warn"
    assert "follow_up_tasks_not_recorded" in follow_up_check["issue_codes"]
    assert any(gate["release_effect"] == "warn" for gate in policy["delivery_gates"])


def test_missing_required_follow_up_tasks_fails_when_marked_required():
    payload = _valid_payload()
    payload["follow_up_required"] = True
    payload["follow_up_tasks"] = []

    policy = _policy(payload)
    follow_up_check = next(check for check in policy["checks"] if check["id"] == "follow-up-tasks")

    assert policy["status"] == "fail"
    assert follow_up_check["status"] == "fail"
    assert "follow_up_tasks_missing" in follow_up_check["issue_codes"]


def test_policy_output_does_not_leak_sensitive_payload_values():
    payload = _valid_payload()
    payload["client_confirmation"]["client_contact"] = "client" + "@example.com"
    payload["client_confirmation"]["phone"] = "13800138000"
    payload["delivery_record"]["private_note"] = "case " + "sec" + "ret"
    payload["delivery_record"]["credential"] = "sk-" + "a" * 24
    payload["delivery_record"]["raw_document_text"] = "Client narrative with " + "pass" + "word"

    serialized = json.dumps(_policy(payload), ensure_ascii=False)

    assert SENSITIVE_PATTERN.search(serialized) is None
    assert "raw_document_text" not in serialized
    assert "private_note" not in serialized
    assert "client_contact" not in serialized


def test_client_delivery_transparency_policy_route_evaluates_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/client-delivery-transparency-policy",
        json=_valid_payload(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "pass"
