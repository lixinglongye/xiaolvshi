import json
import re

from services.final_document_delivery_release_gate import FinalDocumentDeliveryReleaseGateService


SECRET_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|C:\\cases\\private",
    re.IGNORECASE,
)


def _delivery_package() -> dict:
    return {
        "package": {
            "package_id": "package-001",
            "case_id": "case-001",
            "current_version_id": "version-002",
            "delivery_channel": "client_portal",
        },
        "documents": [
            {
                "document_id": "doc-001",
                "document_type": "complaint",
                "version_id": "version-002",
                "export_formats": ["pdf", "docx"],
            }
        ],
        "source_support": {
            "status": "complete",
            "citation_count": 4,
            "unsupported_claim_count": 0,
            "evidence_links": ["evidence-001", "evidence-002"],
        },
        "missing_facts": {"status": "resolved", "items": []},
        "lawyer_review": {
            "status": "approved",
            "reviewer_id": "lawyer-001",
            "reviewed_at": "2026-06-04T08:00:00Z",
            "reviewed_version_id": "version-002",
        },
        "client_transparency": {
            "notice_present": True,
            "client_visible": True,
            "risk_notice_included": True,
            "scope_limits_included": True,
        },
        "export": {"formats": ["pdf", "docx"], "final_format": "pdf", "version_locked": True},
        "version_notes": {
            "current_version_id": "version-002",
            "previous_version_id": "version-001",
            "summary_present": True,
            "generated_at": "2026-06-04T08:05:00Z",
        },
    }


def _version_diff() -> dict:
    return {
        "version_id": "version-002",
        "previous_version_id": "version-001",
        "change_summary": "Clarified payment deadline and source support.",
        "changed_sections": ["payment", "evidence"],
        "reviewer_role": "lawyer",
        "client_visible_summary": "Payment deadline language was clarified.",
        "risk_change_summary": "No risk level change.",
        "source_support_status": "complete",
    }


def _export_readiness() -> dict:
    return {
        "required_fields_complete": True,
        "blockers_cleared": True,
        "lawyer_review_status": "approved",
        "source_support_complete": True,
        "privacy_redaction_status": "pass",
        "version_locked": True,
        "export_format": "pdf",
    }


def _quota_summary() -> dict:
    return {
        "decision_status": "ready",
        "can_create_report": True,
        "reports_remaining": 3,
        "report_quota_monthly": 20,
        "quota_window": "2026-06",
    }


def _ready_payload() -> dict:
    return {
        "action": "deliver_to_client",
        "delivery_package": _delivery_package(),
        "version_diff": _version_diff(),
        "export_readiness": _export_readiness(),
        "quota_summary": _quota_summary(),
    }


def _gate(payload: dict | None = None) -> dict:
    return FinalDocumentDeliveryReleaseGateService().build_gate(payload)


def test_final_document_delivery_release_gate_returns_template_contract():
    gate = _gate()

    assert gate["status"] == "template"
    assert gate["summary"]["package_release_allowed"] is False
    assert gate["summary"]["ready_component_count"] == 0
    assert {item["id"] for item in gate["component_gates"]} == {
        "document-delivery-package-manifest",
        "document-version-diff-checklist",
        "legal-document-export-readiness",
        "quota-delivery-decision",
    }
    assert gate["privacy_boundary"]["model_calls"] is False
    assert gate["claim_boundary"]["client_delivery_sent"] is False


def test_final_document_delivery_release_gate_allows_complete_metadata_only_package():
    gate = _gate(_ready_payload())

    assert gate["status"] == "ready"
    assert gate["summary"]["package_release_allowed"] is True
    assert gate["summary"]["final_export_allowed"] is True
    assert gate["summary"]["client_delivery_allowed"] is True
    assert gate["summary"]["blocking_component_ids"] == []
    assert {item["status"] for item in gate["component_gates"]} == {"ready"}
    assert gate["release_decision"]["materializes_export"] is False
    assert gate["release_decision"]["sends_client_delivery"] is False


def test_final_document_delivery_release_gate_blocks_manifest_and_diff_gaps():
    payload = _ready_payload()
    payload["delivery_package"]["lawyer_review"]["status"] = "pending"
    payload["version_diff"]["source_support_status"] = "pending"

    gate = _gate(payload)
    components = {item["id"]: item for item in gate["component_gates"]}

    assert gate["status"] == "blocked"
    assert "document-delivery-package-manifest" in gate["summary"]["blocking_component_ids"]
    assert "document-version-diff-checklist" in gate["summary"]["blocking_component_ids"]
    assert "lawyer_review_not_approved" in components["document-delivery-package-manifest"]["blocker_ids"]
    assert "source-support-not-ready" in components["document-version-diff-checklist"]["blocker_ids"]
    assert gate["release_decision"]["client_delivery_allowed"] is False


def test_final_document_delivery_release_gate_blocks_export_and_quota_gaps():
    payload = _ready_payload()
    payload["export_readiness"]["export_format"] = "exe"
    payload["quota_summary"]["reports_remaining"] = 0
    payload["quota_summary"]["decision_status"] = "blocked"
    payload["quota_summary"]["can_create_report"] = False

    gate = _gate(payload)
    components = {item["id"]: item for item in gate["component_gates"]}

    assert gate["status"] == "blocked"
    assert "legal-document-export-readiness" in gate["summary"]["blocking_component_ids"]
    assert "quota-delivery-decision" in gate["summary"]["blocking_component_ids"]
    assert "supported-export-format" in components["legal-document-export-readiness"]["blocker_ids"]
    assert "report_quota_blocked" in components["quota-delivery-decision"]["blocker_ids"]


def test_final_document_delivery_release_gate_requires_quota_summary():
    payload = _ready_payload()
    payload.pop("quota_summary")

    gate = _gate(payload)
    quota = next(item for item in gate["component_gates"] if item["id"] == "quota-delivery-decision")

    assert gate["status"] == "blocked"
    assert quota["quota_metadata_present"] is False
    assert quota["blocker_ids"] == ["quota_summary_missing"]


def test_final_document_delivery_release_gate_output_is_metadata_only():
    payload = _ready_payload()
    payload["delivery_package"]["documents"][0]["raw_document_text"] = "RAW_DOCUMENT_SHOULD_NOT_LEAK"
    payload["delivery_package"]["documents"][0]["local_path"] = "C:\\cases\\private\\draft.docx"
    payload["delivery_package"]["client_transparency"]["client_contact"] = "client@example.com"
    payload["version_diff"]["change_summary"] = "secret " + "sk-" + "a" * 24
    payload["version_diff"]["raw_document_text"] = "UNSAFE_RAW_DIFF"
    payload["export_readiness"]["raw_model_output"] = "UNSAFE_MODEL_OUTPUT"
    payload["quota_summary"]["billing_provider_payload"] = {"unsafe": "provider-payload"}

    rendered = json.dumps(_gate(payload), ensure_ascii=False)

    assert "RAW_DOCUMENT_SHOULD_NOT_LEAK" not in rendered
    assert "UNSAFE_RAW_DIFF" not in rendered
    assert "UNSAFE_MODEL_OUTPUT" not in rendered
    assert "provider-payload" not in rendered
    assert not SECRET_PATTERN.search(rendered)
    assert "raw_document_text_included" in rendered
    assert "credential_material_included" in rendered


def test_final_document_delivery_release_gate_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template = client.get("/api/v1/maintenance/final-document-delivery-release-gate")
    assert template.status_code == 200
    assert template.json()["data"]["status"] == "template"

    reviewed = client.post("/api/v1/maintenance/final-document-delivery-release-gate", json=_ready_payload())
    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["status"] == "ready"
