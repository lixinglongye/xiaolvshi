import json

import pytest

from services.case_export_readiness import CaseExportReadinessService


PRIVATE_TEXT = "PRIVATE_EXPORT_READINESS_TEXT"


def test_case_export_readiness_allows_complete_report():
    result = CaseExportReadinessService().evaluate(
        {
            "report_meta": {"selected_source_validation": {"delivery_status": "ready"}},
            "risk_scoring": {"overall_score": 20},
            "citations": [{"source_id": "law:001"}],
            "evidence": [{"evidence_id": "E-1"}],
            "release_decision": {"status": "ready"},
            "raw_document_text": PRIVATE_TEXT,
        }
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "ready"
    assert result["missing_sections"] == []
    assert PRIVATE_TEXT not in rendered


def test_case_export_readiness_blocks_missing_and_selected_source_failure():
    result = CaseExportReadinessService().evaluate(
        {
            "report_meta": {"selected_source_validation": {"delivery_status": "blocked"}},
            "release_decision": {"status": "blocked"},
        }
    )

    assert result["status"] == "blocked"
    assert "missing_required_export_sections" in result["reason_codes"]
    assert "selected_source_validation_blocked" in result["reason_codes"]
    assert "release_decision_blocked" in result["reason_codes"]


def test_case_export_readiness_route():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/case/export-readiness",
        json={"report": {"report_meta": {"selected_source_validation": {"delivery_status": "ready"}}}},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "blocked"
