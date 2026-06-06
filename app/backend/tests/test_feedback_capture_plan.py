import re
from types import SimpleNamespace

from services.feedback_capture_plan import FeedbackCapturePlanService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_feedback_capture_plan_links_legal_quality_feedback_without_raw_echo():
    raw_feedback = "The generated report has an incorrect citation in the indemnity section."
    plan = FeedbackCapturePlanService().build_plan(
        category="report_quality",
        content=raw_feedback,
        affected_artifact_id="report_123",
    )
    payload_text = str(plan)

    assert plan["status"] == "ready_to_create"
    assert plan["capture_summary"]["priority"] == "P1"
    assert plan["capture_summary"]["linked_need_id"] == "traceable-legal-review"
    assert "citation_audit" in plan["capture_summary"]["release_gate_links"]
    assert plan["ticket_defaults"]["status"] == "triaged"
    assert "traceable-legal-review" in plan["ticket_defaults"]["resolution_note"]
    assert "Lifecycle blockers: none" in plan["ticket_defaults"]["resolution_note"]
    assert plan["lifecycle"]["state"] == "triage"
    assert plan["lifecycle"]["current_transition_blocking_check_ids"] == []
    assert raw_feedback not in plan["ticket_defaults"]["resolution_note"]
    assert plan["privacy_boundary"]["returns_raw_feedback_text"] is False
    assert plan["privacy_boundary"]["calls_ai_model"] is False
    assert plan["privacy_boundary"]["calls_external_network"] is False
    assert not SECRET_PATTERN.search(payload_text)


def test_feedback_capture_plan_marks_missing_context_for_high_risk_artifact_link():
    plan = FeedbackCapturePlanService().build_plan(
        category="report_quality",
        content="The answer included a hallucination and incorrect citation.",
    )

    assert plan["status"] == "needs_context"
    assert plan["capture_summary"]["high_risk"] is True
    assert "affected_artifact_id" in plan["capture_summary"]["missing_required_fields"]
    assert any(question["field"] == "affected_artifact_id" for question in plan["intake_questions"])
    assert plan["lifecycle"]["next_allowed_states"] == ["linked_gap"]


def test_feedback_capture_plan_enriches_ticket_payload_with_lifecycle_summary():
    payload = {
        "category": "upload_pipeline",
        "content": "PDF upload failed and OCR returned blank output.",
        "status": "open",
        "resolution_note": "User-facing ticket created.",
    }

    enriched = FeedbackCapturePlanService().enrich_ticket_payload(payload)

    assert enriched["status"] == "open"
    assert enriched["priority"] == "P2"
    assert enriched["assignee"] == "engineering"
    assert "User-facing ticket created." in enriched["resolution_note"]
    assert "Roadmap need: robust-extraction-quality" in enriched["resolution_note"]
    assert "Lifecycle blockers: none" in enriched["resolution_note"]
    assert "PDF upload failed" not in enriched["resolution_note"]


def test_feedback_capture_plan_route_returns_preview_without_writing_ticket():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from dependencies.auth import get_current_user
    from routers.feedback_tickets import router

    app = fastapi.FastAPI()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="dev-user")
    app.include_router(router)

    response = testclient.TestClient(app).post(
        "/api/v1/entities/feedback_tickets/capture-plan",
        json={
            "category": "template_export",
            "content": "Please add a better export template workflow.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["capture_summary"]["priority"] == "P3"
    assert payload["privacy_boundary"]["writes_database"] is False
    assert payload["ticket_defaults"]["assignee"] == "product_maintainer"
