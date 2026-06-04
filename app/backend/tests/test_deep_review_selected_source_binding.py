import json

import pytest

from services.deep_review_selected_source_binding import DeepReviewSelectedSourceBindingService


PRIVATE_TEXT = "PRIVATE_SELECTED_SOURCE_BINDING_TEXT_7d4a2b"
PRIVATE_EMAIL = "selected-source-binding@example.test"
PRIVATE_PHONE = "13812345678"


def _report(source_ids=None):
    source_ids = source_ids or ["law:contract-001"]
    return {
        "report_meta": {"report_id": "RPT-001"},
        "summary": PRIVATE_TEXT,
        "citation_map": {"sections": [{"source_ids": source_ids, "quote": PRIVATE_TEXT}]},
        "generation_plan": {"steps": [{"selected_source_binding_checked": True}]},
    }


def test_binding_attaches_ready_selected_source_validation_without_raw_echo():
    result = DeepReviewSelectedSourceBindingService().bind(
        report=_report(),
        request_metadata={"legal_rag_selected_source_ids": ["law:contract-001"]},
    )
    rendered_binding = json.dumps(result["binding"], ensure_ascii=False)

    assert result["status"] == "ready"
    assert result["report"]["report_meta"]["selected_source_validation"]["delivery_status"] == "ready"
    assert result["report"]["legal_rag"]["selected_source_validation"]["status"] == "pass"
    assert result["binding"]["selected_source_ids"] == ["law:contract-001"]
    assert PRIVATE_TEXT not in rendered_binding
    assert PRIVATE_EMAIL not in rendered_binding
    assert result["privacy_boundary"]["raw_legal_text_included"] is False


def test_binding_blocks_report_delivery_when_citations_do_not_match_selected_sources():
    result = DeepReviewSelectedSourceBindingService().bind(
        report=_report(["external-source"]),
        request_metadata={
            "legal_rag_selected_source_ids": ["law:contract-001"],
            "client_email": PRIVATE_EMAIL,
            "phone": PRIVATE_PHONE,
        },
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "blocked"
    assert "selected_source_validation_blocked" in result["report"]["delivery_blockers"]
    assert "unexpected_cited_source_ids" in result["binding"]["reason_codes"]
    assert "missing_selected_source_citations" in result["binding"]["reason_codes"]
    assert PRIVATE_EMAIL not in rendered
    assert PRIVATE_PHONE not in rendered


def test_binding_evaluate_returns_metadata_only_summary():
    result = DeepReviewSelectedSourceBindingService().evaluate(
        report={
            "citation_map": {"citations": [{"source_id": "law:contract-001", "quote": PRIVATE_TEXT}]},
            "raw_document_text": PRIVATE_TEXT,
        },
        request_metadata={"legal_rag_selected_source_ids": ["law:contract-001"]},
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "ready"
    assert "report" not in result
    assert PRIVATE_TEXT not in rendered
    assert result["binding"]["counts"]["selected_source_count"] == 1


def test_deep_review_selected_source_binding_route_is_metadata_only():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post(
        "/api/v1/maintenance/deep-review/selected-source-binding",
        json={
            "report": _report(),
            "request_metadata": {
                "legal_rag_selected_source_ids": ["law:contract-001"],
                "client_email": PRIVATE_EMAIL,
            },
            "raw_document_text": PRIVATE_TEXT,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ready"
    assert PRIVATE_TEXT not in response.text
    assert PRIVATE_EMAIL not in response.text
