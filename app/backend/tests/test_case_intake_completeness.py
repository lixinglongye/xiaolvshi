import re

from services.case_intake_completeness import CaseIntakeCompletenessService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password", re.IGNORECASE)


def _complete_intake() -> dict:
    return {
        "client_name": "Client A",
        "opposing_party": "Company B",
        "party_roles": ["plaintiff", "defendant"],
        "jurisdiction": "PRC",
        "venue_or_court": "Example District Court",
        "case_type": "contract dispute",
        "key_dates": ["2026-01-10"],
        "deadline_risks": ["limitation review needed"],
        "claims": ["payment default"],
        "requested_remedy": "repayment",
        "desired_outcome": "settlement or filing",
        "evidence_items": ["contract", "payment record"],
        "source_citations": ["contract clause 3"],
        "known_risks": ["evidence authenticity pending"],
        "lawyer_review_required": True,
        "client_disclosure_acknowledged": True,
    }


def test_case_intake_completeness_returns_template():
    checklist = CaseIntakeCompletenessService().build_checklist()

    assert checklist["status"] == "template"
    assert checklist["summary"]["requirement_count"] >= 6
    assert checklist["summary"]["ready_for_document_generation"] is False
    assert any(item["id"] == "evidence-inventory" for item in checklist["requirements"])


def test_case_intake_completeness_blocks_missing_core_fields():
    checklist = CaseIntakeCompletenessService().build_checklist(
        {
            "client_name": "Client A",
            "case_type": "contract dispute",
            "claims": ["payment default"],
        }
    )

    assert checklist["status"] == "blocked"
    assert checklist["summary"]["blocking_requirement_count"] >= 3
    assert checklist["summary"]["ready_for_document_generation"] is False
    assert any("source_citations" in item["missing_fields"] for item in checklist["blocking_items"])


def test_case_intake_completeness_marks_complete_intake_ready():
    checklist = CaseIntakeCompletenessService().build_checklist(_complete_intake())

    assert checklist["status"] == "ready"
    assert checklist["summary"]["blocking_requirement_count"] == 0
    assert checklist["summary"]["ready_for_document_generation"] is True
    assert checklist["summary"]["ready_for_lawyer_review"] is True


def test_case_intake_completeness_uses_safe_metadata_only():
    checklist = CaseIntakeCompletenessService().build_checklist(_complete_intake())

    assert "raw client documents" in checklist["privacy_note"]
    assert not SECRET_PATTERN.search(str(checklist))


def test_case_intake_completeness_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/case-intake-completeness")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "template"

    post_response = client.post("/api/v1/maintenance/case-intake-completeness", json=_complete_intake())
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
