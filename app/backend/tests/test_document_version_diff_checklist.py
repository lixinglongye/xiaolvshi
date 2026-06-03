import re

from services.document_version_diff_checklist import DocumentVersionDiffChecklistService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _valid_diff() -> dict:
    return {
        "version_id": "v2",
        "previous_version_id": "v1",
        "change_summary": "Clarified payment deadline and source support.",
        "changed_sections": ["payment", "evidence"],
        "reviewer_role": "lawyer",
        "client_visible_summary": "Payment deadline language was clarified.",
        "risk_change_summary": "No risk level change.",
        "source_support_status": "complete",
    }


def test_document_version_diff_checklist_returns_template():
    payload = DocumentVersionDiffChecklistService().build_checklist()

    assert payload["status"] == "template"
    assert payload["summary"]["ready_for_client_visibility"] is False
    assert payload["diff_review"] is None
    assert any(item["id"] == "client-visible-summary" for item in payload["checklist_items"])


def test_document_version_diff_checklist_accepts_complete_diff():
    payload = DocumentVersionDiffChecklistService().build_checklist(_valid_diff())

    assert payload["status"] == "ready"
    assert payload["summary"]["ready_for_client_visibility"] is True
    assert payload["summary"]["changed_section_count"] == 2
    assert payload["risk_flags"] == []


def test_document_version_diff_checklist_blocks_missing_fields_and_same_version():
    diff = _valid_diff()
    diff["version_id"] = "v1"
    diff["client_visible_summary"] = ""
    diff["changed_sections"] = []

    payload = DocumentVersionDiffChecklistService().build_checklist(diff)
    flag_ids = {flag["id"] for flag in payload["risk_flags"]}

    assert payload["status"] == "blocked"
    assert "missing-required-diff-fields" in flag_ids
    assert "version-id-not-advanced" in flag_ids
    assert "changed-sections-empty" in flag_ids


def test_document_version_diff_checklist_blocks_source_support_gap():
    diff = _valid_diff()
    diff["source_support_status"] = "pending"

    payload = DocumentVersionDiffChecklistService().build_checklist(diff)

    assert payload["status"] == "blocked"
    assert any(flag["id"] == "source-support-not-ready" for flag in payload["risk_flags"])


def test_document_version_diff_checklist_sanitizes_sensitive_values():
    diff = _valid_diff()
    diff["change_summary"] = "client@example.com password " + "s" + "k-" + "a" * 24
    diff["raw_document_text"] = "UNSAFE_RAW_TEXT"

    payload = DocumentVersionDiffChecklistService().build_checklist(diff)
    rendered = str(payload)

    assert "[redacted]" in rendered
    assert "UNSAFE_RAW_TEXT" not in rendered
    assert not SECRET_PATTERN.search(rendered)
    assert any(flag["id"] == "unsupported-diff-fields-ignored" for flag in payload["risk_flags"])


def test_document_version_diff_checklist_validation_commands_are_local():
    payload = DocumentVersionDiffChecklistService().build_checklist()

    assert payload["validation_commands"] == [
        "python -m pytest tests/test_document_version_diff_checklist.py -q",
        "python -m compileall services/document_version_diff_checklist.py tests/test_document_version_diff_checklist.py",
    ]


def test_document_version_diff_checklist_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/document-version-diff-checklist")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "template"

    reviewed = client.post("/api/v1/maintenance/document-version-diff-checklist", json=_valid_diff())

    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["status"] == "ready"
