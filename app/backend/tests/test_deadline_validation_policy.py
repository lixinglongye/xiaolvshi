import json
import re

from services.deadline_validation_policy import DeadlineValidationPolicyService


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


def _policy(deadlines=None, reference_date="2026-06-04") -> dict:
    return DeadlineValidationPolicyService().build_policy(deadlines, reference_date=reference_date)


def test_default_examples_use_fixed_local_dates():
    payload = _policy()

    assert payload["reference_date"] == "2026-06-04"
    assert payload["summary"]["check_count"] == 4
    assert payload["summary"]["deterministic"] is True
    assert payload["risk_bands"]
    assert payload["recommended_actions"]
    assert payload["privacy_note"]
    assert payload["validation_commands"]


def test_clear_contract_deadline_does_not_require_reminder_or_review():
    payload = _policy(
        [
            {
                "deadline_id": "contract-1",
                "deadline_type": "contract_performance_deadline",
                "contract_performance_date": "2026-07-01",
            }
        ]
    )

    check = payload["checks"][0]
    assert payload["status"] == "ready"
    assert payload["summary"]["ok_count"] == 1
    assert payload["summary"]["reminder_count"] == 0
    assert payload["summary"]["lawyer_review_count"] == 0
    assert check["risk_band"] == "clear"
    assert check["requires_reminder"] is False
    assert check["requires_lawyer_review"] is False


def test_near_evidence_deadline_requires_case_team_reminder():
    payload = _policy(
        [
            {
                "deadline_id": "evidence-1",
                "deadline_type": "evidence_deadline",
                "evidence_due_date": "2026-06-10",
            }
        ]
    )

    check = payload["checks"][0]
    assert payload["status"] == "reminder_required"
    assert payload["summary"]["near_count"] == 1
    assert payload["summary"]["reminder_count"] == 1
    assert check["days_until_due"] == 6
    assert check["risk_band"] == "near"
    assert check["requires_reminder"] is True
    assert check["requires_lawyer_review"] is False
    assert "case-team-reminder" in check["recommended_action_ids"]


def test_overdue_appeal_deadline_requires_lawyer_review_and_escalation():
    payload = _policy(
        [
            {
                "deadline_id": "appeal-1",
                "deadline_type": "appeal_deadline",
                "appeal_due_date": "2026-06-01",
            }
        ]
    )

    check = payload["checks"][0]
    assert payload["status"] == "lawyer_review_required"
    assert payload["summary"]["overdue_count"] == 1
    assert payload["summary"]["lawyer_review_count"] == 1
    assert check["days_until_due"] == -3
    assert check["risk_band"] == "overdue"
    assert check["requires_reminder"] is True
    assert check["requires_lawyer_review"] is True
    assert "same-day-escalation" in check["recommended_action_ids"]
    assert "preservation-review" in check["recommended_action_ids"]


def test_missing_date_requires_date_verification_and_lawyer_review():
    payload = _policy(
        [
            {
                "deadline_id": "case-date-1",
                "deadline_type": "case_date",
            }
        ]
    )

    check = payload["checks"][0]
    assert payload["status"] == "needs_date_verification"
    assert payload["summary"]["missing_date_count"] == 1
    assert check["date_present"] is False
    assert check["date_valid"] is False
    assert check["days_until_due"] is None
    assert check["risk_band"] == "missing_date"
    assert check["requires_reminder"] is False
    assert check["requires_lawyer_review"] is True
    assert "collect-controlling-date" in check["recommended_action_ids"]


def test_sensitive_input_is_not_leaked_in_policy_output():
    payload = _policy(
        [
            {
                "deadline_id": "s" + "k-" + "123456789012345678901234",
                "deadline_type": "service_date",
                "service_date": "2026-06-05",
                "title": "client user@example.com password secret",
            }
        ]
    )
    serialized = json.dumps(payload, ensure_ascii=False)

    assert not SENSITIVE_DATA_PATTERN.search(serialized)
    check = payload["checks"][0]
    assert check["deadline_id"] == "redacted-id"
    assert check["safe_label"] == "[redacted]"
    assert check["risk_band"] == "urgent"
    assert check["requires_lawyer_review"] is True


def test_deadline_validation_policy_route_evaluates_deadlines():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/deadline-validation-policy",
        json={
            "reference_date": "2026-06-04",
            "deadlines": [
                {
                    "deadline_id": "evidence-1",
                    "deadline_type": "evidence_deadline",
                    "evidence_due_date": "2026-06-10",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["near_count"] == 1
