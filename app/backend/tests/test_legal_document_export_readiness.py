import re

from services.legal_document_export_readiness import LegalDocumentExportReadinessService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password", re.IGNORECASE)


def _ready_payload() -> dict:
    return {
        "required_fields_complete": True,
        "blockers_cleared": True,
        "lawyer_review_status": "approved",
        "source_support_complete": True,
        "privacy_redaction_status": "pass",
        "version_locked": True,
        "export_format": "pdf",
    }


def test_legal_document_export_readiness_returns_template():
    readiness = LegalDocumentExportReadinessService().build_readiness()

    assert readiness["status"] == "template"
    assert readiness["summary"]["ready_for_final_export"] is False
    assert "pdf" in readiness["summary"]["supported_export_formats"]
    assert readiness["blocking_items"]


def test_legal_document_export_readiness_blocks_unreviewed_document():
    payload = _ready_payload()
    payload["lawyer_review_status"] = "pending"

    readiness = LegalDocumentExportReadinessService().build_readiness(payload)
    blocker_ids = {item["id"] for item in readiness["blocking_items"]}

    assert readiness["status"] == "blocked"
    assert "lawyer-review-passed" in blocker_ids
    assert readiness["summary"]["ready_for_final_export"] is False


def test_legal_document_export_readiness_blocks_unsupported_format():
    payload = _ready_payload()
    payload["export_format"] = "exe"

    readiness = LegalDocumentExportReadinessService().build_readiness(payload)

    assert readiness["status"] == "blocked"
    assert readiness["format_gate"]["blocks_export"] is True
    assert readiness["format_gate"]["observed_value"] == "exe"


def test_legal_document_export_readiness_allows_ready_payload():
    readiness = LegalDocumentExportReadinessService().build_readiness(_ready_payload())

    assert readiness["status"] == "ready"
    assert readiness["summary"]["blocking_gate_count"] == 0
    assert readiness["summary"]["ready_for_final_export"] is True


def test_legal_document_export_readiness_uses_safe_metadata_only():
    readiness = LegalDocumentExportReadinessService().build_readiness(_ready_payload())

    assert "raw legal text" in readiness["privacy_note"]
    assert not SECRET_PATTERN.search(str(readiness))


def test_legal_document_export_readiness_route_returns_template_and_readiness():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-document-export-readiness")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "template"

    post_response = client.post("/api/v1/maintenance/legal-document-export-readiness", json=_ready_payload())
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
