import re

from services.case_timeline_deadline_risk import CaseTimelineDeadlineRiskService


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


def _assessment(events=None) -> dict:
    return CaseTimelineDeadlineRiskService().build_assessment(events=events)


def test_no_input_returns_template():
    payload = _assessment()

    assert payload["status"] == "template"
    assert payload["summary"]["assessed_event_count"] == 0
    assert payload["risk_flags"] == []
    assert payload["blocking_urgent_items"] == []
    assert payload["event_template"]["event_type"] == "answer_deadline"
    assert any(item["event_type"] == "limitation_period_deadline" for item in payload["event_type_standards"])
    assert any(rule["rule_id"] == "urgent-window-le-3-days" for rule in payload["deadline_rules_metadata"])


def test_days_until_deadline_le_three_triggers_urgent_blocking_item():
    payload = _assessment(
        [
            {
                "event_id": "answer-1",
                "event_type": "answer_deadline",
                "title": "Answer deadline",
                "key_date": "2026-06-06",
                "days_until_deadline": 3,
            }
        ]
    )

    assert payload["status"] == "ready"
    assert payload["summary"]["blocking_urgent_count"] == 1
    assert payload["blocking_urgent_items"][0]["event_id"] == "answer-1"
    urgent_flags = [item for item in payload["risk_flags"] if item["risk_type"] == "urgent_deadline"]
    assert len(urgent_flags) == 1
    assert urgent_flags[0]["severity"] == "urgent"
    assert urgent_flags[0]["blocking"] is True


def test_explicit_urgency_triggers_urgent_even_without_computed_days():
    payload = _assessment(
        [
            {
                "event_id": "limitation-1",
                "event_type": "limitation_period_deadline",
                "title": "Limitation review",
                "key_date": "2026-06-08",
                "urgency": "critical",
            }
        ]
    )

    assert payload["summary"]["blocking_urgent_count"] == 1
    assert any(item["event_id"] == "limitation-1" for item in payload["blocking_urgent_items"])


def test_missing_key_date_triggers_missing_fact():
    payload = _assessment(
        [
            {
                "event_id": "evidence-1",
                "event_type": "evidence_deadline",
                "title": "Evidence submission",
                "days_until_deadline": 10,
            }
        ]
    )

    assert payload["summary"]["missing_fact_count"] >= 1
    missing_flags = [item for item in payload["risk_flags"] if item["risk_type"] == "missing_fact"]
    assert missing_flags
    assert "key date" in missing_flags[0]["reason"].lower()


def test_payload_has_no_sensitive_data_patterns_and_redacts_input_text():
    payload = _assessment(
        [
            {
                "event_id": "secret-event",
                "event_type": "appeal_deadline",
                "title": "Contact placeholder credential marker",
                "key_date": "2026-06-09",
                "days_until_deadline": 4,
            }
        ]
    )

    assert not SENSITIVE_DATA_PATTERN.search(str(payload))
    assert payload["validation_commands"]


def test_case_timeline_deadline_risk_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/case-timeline-deadline-risk")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "template"

    post_response = client.post(
        "/api/v1/maintenance/case-timeline-deadline-risk",
        json=[
            {
                "event_id": "answer-1",
                "event_type": "answer_deadline",
                "key_date": "2026-06-06",
                "days_until_deadline": 2,
            }
        ],
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["summary"]["blocking_urgent_count"] == 1
