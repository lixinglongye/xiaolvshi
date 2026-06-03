import json
import re

from services.document_delivery_package_manifest import DocumentDeliveryPackageManifestService


SENSITIVE_PATTERN = re.compile(
    "|".join(
        [
            r"sk-[A-Za-z0-9]{20,}",
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            r"C:\\",
            "pass" + "word",
            "sec" + "ret",
            "tok" + "en",
            "raw_document_text",
            "private_note",
            "client_contact",
        ]
    ),
    re.IGNORECASE,
)


def _manifest(payload: dict | None = None) -> dict:
    return DocumentDeliveryPackageManifestService().build_manifest(payload)


def _valid_payload() -> dict:
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
                "checksum": "sha256:<redacted>",
            }
        ],
        "source_support": {
            "status": "complete",
            "citation_count": 4,
            "unsupported_claim_count": 0,
            "evidence_links": ["evidence-001", "evidence-002"],
        },
        "missing_facts": {
            "status": "resolved",
            "items": [],
        },
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
        "export": {
            "formats": ["pdf", "docx"],
            "final_format": "pdf",
            "version_locked": True,
        },
        "version_notes": {
            "current_version_id": "version-002",
            "previous_version_id": "version-001",
            "summary_present": True,
            "generated_at": "2026-06-04T08:05:00Z",
        },
    }


def test_document_delivery_package_manifest_returns_template_contract():
    manifest = _manifest()
    section_ids = {section["id"] for section in manifest["manifest_sections"]}

    assert manifest["status"] == "template"
    assert manifest["summary"]["ready_for_delivery"] is False
    assert manifest["risk_flags"] == []
    assert manifest["recommended_actions"]
    assert manifest["privacy_note"]
    assert manifest["validation_commands"]
    assert {
        "documents",
        "source-support",
        "missing-facts",
        "lawyer-review",
        "client-transparency-notice",
        "export-formats",
        "version-notes",
    }.issubset(section_ids)


def test_document_delivery_package_manifest_allows_complete_package():
    manifest = _manifest(_valid_payload())

    assert manifest["status"] == "ready"
    assert manifest["summary"]["ready_for_delivery"] is True
    assert manifest["summary"]["blocking_risk_count"] == 0
    assert manifest["risk_flags"] == []
    assert {section["status"] for section in manifest["manifest_sections"]} == {"pass"}
    assert manifest["recommended_actions"][0]["id"] == "approve-delivery-manifest"


def test_document_delivery_package_manifest_blocks_missing_documents_and_sources():
    payload = _valid_payload()
    payload["documents"] = []
    payload["source_support"] = {
        "status": "pending",
        "citation_count": 0,
        "unsupported_claim_count": 2,
    }

    manifest = _manifest(payload)
    risk_ids = {flag["id"] for flag in manifest["risk_flags"]}

    assert manifest["status"] == "blocked"
    assert "documents_missing" in risk_ids
    assert "source_support_not_complete" in risk_ids
    assert "source_anchor_missing" in risk_ids
    assert "unsupported_claims_present" in risk_ids
    assert manifest["summary"]["ready_for_delivery"] is False


def test_document_delivery_package_manifest_blocks_unresolved_facts_and_pending_review():
    payload = _valid_payload()
    payload["missing_facts"] = {
        "status": "pending",
        "items": [{"field": "delivery_date", "status": "open"}],
    }
    payload["lawyer_review"]["status"] = "pending"

    manifest = _manifest(payload)
    risk_ids = {flag["id"] for flag in manifest["risk_flags"]}
    action_ids = {action["id"] for action in manifest["recommended_actions"]}

    assert manifest["status"] == "blocked"
    assert "unresolved_missing_facts" in risk_ids
    assert "missing_fact_status_not_clear" in risk_ids
    assert "lawyer_review_not_approved" in risk_ids
    assert "resolve-missing-facts" in action_ids
    assert "resolve-lawyer-review" in action_ids


def test_document_delivery_package_manifest_blocks_notice_export_and_version_gaps():
    payload = _valid_payload()
    payload["client_transparency"]["client_visible"] = False
    payload["client_transparency"]["scope_limits_included"] = False
    payload["export"]["final_format"] = "exe"
    payload["export"]["version_locked"] = False
    payload["version_notes"]["current_version_id"] = "version-001"
    payload["version_notes"]["summary_present"] = False

    manifest = _manifest(payload)
    risk_ids = {flag["id"] for flag in manifest["risk_flags"]}

    assert manifest["status"] == "blocked"
    assert "client_notice_not_visible" in risk_ids
    assert "scope_limits_missing" in risk_ids
    assert "unsupported_export_format" in risk_ids
    assert "export_version_not_locked" in risk_ids
    assert "version_notes_missing" in risk_ids
    assert "version_notes_version_mismatch" in risk_ids


def test_document_delivery_package_manifest_output_is_metadata_only():
    payload = _valid_payload()
    payload["client_transparency"]["client_contact"] = "client" + "@example.com"
    payload["client_transparency"]["private_note"] = "case " + "sec" + "ret"
    payload["documents"][0]["local_path"] = "C:\\cases\\client\\draft.docx"
    payload["documents"][0]["raw_document_text"] = "Full narrative with " + "pass" + "word"
    payload["export"]["credential"] = "sk-" + "a" * 24

    serialized = json.dumps(_manifest(payload), ensure_ascii=False)

    assert SENSITIVE_PATTERN.search(serialized) is None
    assert "local_path" not in serialized
    assert "credential" not in serialized


def test_document_delivery_package_manifest_validation_commands_are_local():
    manifest = _manifest(_valid_payload())
    commands = {item["id"]: item["command"] for item in manifest["validation_commands"]}

    assert commands["document-delivery-package-manifest-tests"] == (
        "python -m pytest tests/test_document_delivery_package_manifest.py -q"
    )
    assert commands["document-delivery-package-manifest-compile"] == (
        "python -m compileall services/document_delivery_package_manifest.py"
    )


def test_document_delivery_package_manifest_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/document-delivery-package-manifest")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "template"

    reviewed = client.post("/api/v1/maintenance/document-delivery-package-manifest", json=_valid_payload())

    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["status"] == "ready"
