import json
import re

from services.case_workbench_payload import CaseWorkbenchPayloadService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret",
    re.IGNORECASE,
)


def _ready_intake() -> dict:
    return {
        "client_name": "Client A",
        "opposing_parties": ["Company B"],
        "matter_type": "contract dispute",
        "jurisdiction": "PRC",
        "claim_objective": "recover payment",
        "facts_summary": "metadata-only placeholder",
        "key_dates": ["2026-01-10"],
        "deadline_assessment": "limitation reviewed",
        "evidence_items": ["contract", "payment record"],
        "identity_materials": ["client id reference"],
        "authorization_materials": ["engagement letter reference"],
        "engagement_scope_acknowledged": True,
        "conflict_search_completed": True,
        "conflict_result": "clear",
        "risk_level": "low",
        "lawyer_review_required": False,
    }


def _supported_report() -> dict:
    return {
        "professional_review_framework": {
            "evidence_checklist": ["Signed contract", "Payment records"],
        },
        "legal_authority_appendix": [
            {
                "source_id": "civil-code-509",
                "source_name": "Civil Code Article 509",
            }
        ],
        "risk_items": [
            {
                "risk_id": "R-001",
                "title": "Payment default",
                "risk_level": "high",
                "legal_analysis": {
                    "evidence_suggestion": ["Keep signed contract.", "Keep transfer records."],
                },
                "citations": [
                    {
                        "source_id": "civil-code-509",
                        "source_name": "Civil Code Article 509",
                    }
                ],
            }
        ],
    }


def test_case_workbench_payload_returns_frontend_empty_state_without_inputs():
    payload = CaseWorkbenchPayloadService().build_payload()

    assert payload["payload_id"] == "case-workbench-payload-v1"
    assert payload["status"] == "template"
    assert payload["dashboard"]["evaluated_section_count"] == 0
    assert [section["id"] for section in payload["sections"]] == [
        "matter_intake",
        "deadline_validation",
        "timeline_risk",
        "task_notifications",
        "evidence_graph",
    ]
    assert payload["blockers"] == []
    assert payload["next_actions"]
    assert all(section["input_state"] == "not_supplied" for section in payload["sections"])


def test_case_workbench_payload_marks_ready_when_all_sources_are_clear():
    payload = CaseWorkbenchPayloadService().build_payload(
        case_id="case-1",
        matter_id="matter-1",
        intake=_ready_intake(),
        deadlines=[
            {
                "deadline_id": "contract-1",
                "deadline_type": "contract_performance_deadline",
                "contract_performance_date": "2026-07-01",
            }
        ],
        timeline_events=[
            {
                "event_id": "hearing-1",
                "event_type": "hearing",
                "key_date": "2026-07-01",
                "days_until_deadline": 20,
            }
        ],
        tasks=[
            {
                "case_id": "case-1",
                "task_id": "task-done",
                "status": "done",
                "priority": "critical",
                "days_until_due": 0,
            }
        ],
        evidence_report=_supported_report(),
    )

    assert payload["status"] == "ready"
    assert payload["dashboard"]["blocker_count"] == 0
    assert payload["blockers"] == []
    assert {section["status"] for section in payload["sections"]} == {"ready"}
    assert payload["dashboard"]["cards"][0]["section_id"] == "matter_intake"


def test_case_workbench_payload_consolidates_blockers_from_all_sources():
    blocked_report = _supported_report()
    blocked_report["risk_items"][0]["legal_analysis"]["evidence_suggestion"] = []
    blocked_report["risk_items"][0]["citations"] = []

    payload = CaseWorkbenchPayloadService().build_payload(
        intake={
            "client_name": "Client A",
            "matter_type": "contract dispute",
            "conflict_search_completed": True,
            "conflict_result": "confirmed",
            "lawyer_review_required": True,
        },
        deadlines=[
            {
                "deadline_id": "appeal-1",
                "deadline_type": "appeal_deadline",
                "appeal_due_date": "2026-06-01",
            }
        ],
        timeline_events=[
            {
                "event_id": "answer-1",
                "event_type": "answer_deadline",
                "key_date": "2026-06-06",
                "days_until_deadline": 2,
            }
        ],
        tasks=[
            {
                "case_id": "case-1",
                "task_id": "task-ownerless",
                "status": "open",
                "priority": "normal",
                "days_until_due": 1,
            }
        ],
        evidence_report=blocked_report,
    )

    sections_with_blockers = {item["source_section"] for item in payload["blockers"]}

    assert payload["status"] == "blocked"
    assert payload["dashboard"]["blocker_count"] >= 5
    assert sections_with_blockers == {
        "matter_intake",
        "deadline_validation",
        "timeline_risk",
        "task_notifications",
        "evidence_graph",
    }
    assert payload["dashboard"]["primary_blocker"]["source_section"] == "matter_intake"
    assert payload["next_actions"][0]["priority"] == "critical"


def test_case_workbench_payload_sanitizes_sensitive_input_from_ui_contract():
    payload = CaseWorkbenchPayloadService().build_payload(
        case_id="s" + "k-123456789012345678901234",
        matter_id="user@example.com",
        deadlines=[
            {
                "deadline_id": "s" + "k-123456789012345678901234",
                "deadline_type": "service_date",
                "service_date": "2026-06-05",
                "title": "client user@example.com password secret",
            }
        ],
        timeline_events=[
            {
                "event_id": "password",
                "event_type": "appeal_deadline",
                "title": "secret user@example.com",
                "key_date": "2026-06-09",
                "days_until_deadline": 2,
            }
        ],
        tasks=[
            {
                "case_id": "user@example.com",
                "task_id": "password",
                "status": "open",
                "priority": "normal",
                "days_until_due": 1,
                "owner_role": "lawyer",
            }
        ],
    )
    serialized = json.dumps(payload, ensure_ascii=False)

    assert payload["case_ref"] == "case-unspecified"
    assert payload["matter_ref"] == "matter-unspecified"
    assert not SENSITIVE_PATTERN.search(serialized)


def test_case_workbench_payload_is_deterministic_for_same_inputs():
    service = CaseWorkbenchPayloadService()
    kwargs = {
        "intake": _ready_intake(),
        "deadlines": [
            {
                "deadline_id": "evidence-1",
                "deadline_type": "evidence_deadline",
                "evidence_due_date": "2026-06-10",
            }
        ],
        "timeline_events": [
            {
                "event_id": "evidence-1",
                "event_type": "evidence_deadline",
                "key_date": "2026-06-10",
                "days_until_deadline": 6,
            }
        ],
        "tasks": [
            {
                "case_id": "case-1",
                "task_id": "task-client",
                "status": "waiting_client",
                "days_until_due": 2,
                "owner_role": "lawyer",
            }
        ],
        "evidence_report": _supported_report(),
    }

    assert service.build_payload(**kwargs) == service.build_payload(**kwargs)


def test_case_workbench_payload_route_returns_template_and_metadata_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/case-workbench-payload")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "template"

    reviewed = client.post(
        "/api/v1/maintenance/case-workbench-payload",
        json={"case_id": "case-1", "intake": _ready_intake()},
    )

    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["case_ref"] == "case-1"
