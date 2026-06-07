import json

import pytest

from services.legal_rag_export_readiness_packet import LegalRagExportReadinessPacketService


PRIVATE_TEXT = "PRIVATE_LEGAL_RAG_EXPORT_PACKET_TEXT_91c2"
PRIVATE_EMAIL = "rag-export-packet@example.test"
PRIVATE_PHONE = "13900001111"


def _ready_report() -> dict:
    return {
        "report_meta": {"report_id": "RAG-EXPORT-READY"},
        "risk_scoring": {"overall_score": 18, "overall_level": "low"},
        "citations": [{"source_id": "law:contract-001"}],
        "citation_map": {"sections": [{"source_id": "law:contract-001", "quote": PRIVATE_TEXT}]},
        "generation_plan": {"outline": [{"selected_source_binding_checked": True}]},
        "evidence": [{"evidence_id": "EV-001"}],
        "release_decision": {"status": "ready"},
        "raw_document_text": PRIVATE_TEXT,
        "client_email": PRIVATE_EMAIL,
    }


def test_export_readiness_packet_allows_ready_metadata_without_raw_report_echo():
    result = LegalRagExportReadinessPacketService().build_packet(
        report=_ready_report(),
        request_metadata={"legal_rag_selected_source_ids": ["law:contract-001"], "phone": PRIVATE_PHONE},
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "ready"
    assert result["release_action"] == "allow_export_after_reviewer_confirmation"
    assert result["summary"]["selected_source_count"] == 1
    assert result["summary"]["missing_required_section_count"] == 0
    assert "deep-review-export-readiness-route-gate" in result["linked_release_gates"]
    assert "report" not in result
    assert PRIVATE_TEXT not in rendered
    assert PRIVATE_EMAIL not in rendered
    assert PRIVATE_PHONE not in rendered
    assert result["privacy_boundary"]["raw_report_returned"] is False
    assert result["privacy_boundary"]["newapi_called"] is False
    assert result["privacy_boundary"]["gemini_called"] is False


def test_export_readiness_packet_blocks_mismatched_sources_and_missing_sections():
    result = LegalRagExportReadinessPacketService().build_packet(
        report={
            "report_meta": {"report_id": "RAG-EXPORT-BLOCKED"},
            "citation_map": {"citations": [{"source_id": "external-source", "quote": PRIVATE_TEXT}]},
            "release_decision": {"status": "blocked", "blocking_reasons": [PRIVATE_TEXT]},
            "raw_document_text": PRIVATE_TEXT,
        },
        request_metadata={"legal_rag_selected_source_ids": ["law:contract-001"]},
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "blocked"
    assert result["release_action"] == "block_export_until_selected_sources_are_fixed"
    assert "unexpected_cited_source_ids" in result["reason_codes"]
    assert "missing_required_export_sections" in result["reason_codes"]
    assert "release_decision_blocked" in result["reason_codes"]
    assert "deep_review_export_not_ready" in result["reason_codes"]
    assert result["summary"]["blocked_check_count"] >= 3
    assert result["selected_source_binding"]["unexpected_source_ids"] == ["external-source"]
    assert PRIVATE_TEXT not in rendered


def test_export_readiness_packet_route_is_metadata_only():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/legal-rag/export-readiness-packet",
        json={
            "report": _ready_report(),
            "request_metadata": {
                "legal_rag_selected_source_ids": ["law:contract-001"],
                "client_email": PRIVATE_EMAIL,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == "legal-rag-export-readiness-packet"
    assert data["status"] == "ready"
    assert PRIVATE_TEXT not in response.text
    assert PRIVATE_EMAIL not in response.text
