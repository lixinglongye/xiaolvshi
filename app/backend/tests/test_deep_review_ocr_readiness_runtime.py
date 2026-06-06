import json
from types import SimpleNamespace

import pytest

import routers.deep_review as deep_review_router
from routers.deep_review import _build_uploaded_ocr_readiness


PRIVATE_ERROR = "OCR PRIVATE_TEXT client@example.test C:\\Users\\client\\contract.pdf failed"


def test_uploaded_ocr_readiness_marks_completed_ocr_as_parsed_with_signal():
    readiness = _build_uploaded_ocr_readiness(
        {
            "parser": "pymupdf+ocr",
            "page_count": 2,
            "char_count": 2800,
            "text_layer_pages": [2],
            "low_text_pages": [1],
            "ocr_pages": [1],
        },
        enable_ocr=True,
    )

    assert readiness["status"] == "parsed"
    assert readiness["summary"]["ready_for_parse"] is True
    assert readiness["summary"]["ocr_required"] is True
    assert readiness["summary"]["ocr_attempt_count"] == 1
    assert readiness["scanned_or_low_text_detection"]["scanned_page_count"] >= 1


def test_uploaded_ocr_readiness_failure_uses_safe_failure_code():
    readiness = _build_uploaded_ocr_readiness(
        {},
        enable_ocr=True,
        extraction_error=PRIVATE_ERROR,
    )
    rendered = json.dumps(readiness, ensure_ascii=False)

    assert readiness["status"] == "ocr_failed"
    assert readiness["retry_state"]["latest_failure_reason"] == "ocr_failed"
    assert "PRIVATE_TEXT" not in rendered
    assert "client@example.test" not in rendered
    assert "contract.pdf" not in rendered


@pytest.mark.asyncio
async def test_uploaded_document_status_returns_ocr_readiness(monkeypatch):
    deep_review_router._RUNNING_REVIEW_PROGRESS.clear()
    extraction = {
        "parser": "pymupdf+ocr",
        "page_count": 3,
        "char_count": 3600,
        "text_layer_pages": [2, 3],
        "low_text_pages": [1],
        "ocr_pages": [1],
    }

    class FakeDocumentsService:
        def __init__(self, db):
            self.db = db

        async def get_by_id(self, document_id, user_id=None):
            return SimpleNamespace(
                id=document_id,
                status="extracting",
                extraction_metadata_json=json.dumps(extraction),
                extraction_error="",
            )

    monkeypatch.setattr(deep_review_router, "DocumentsService", FakeDocumentsService)

    response = await deep_review_router.get_uploaded_document_analysis_status(
        42,
        current_user=SimpleNamespace(id="ocr-runtime-user"),
        db=object(),
    )

    assert response.success is True
    assert response.ocr_readiness["status"] == "parsed"
    assert response.ocr_readiness["summary"]["ocr_required"] is True
    assert response.ocr_readiness["summary"]["ocr_attempt_count"] == 1


@pytest.mark.asyncio
async def test_failed_uploaded_document_status_sanitizes_ocr_error(monkeypatch):
    deep_review_router._RUNNING_REVIEW_PROGRESS.clear()

    class FakeDocumentsService:
        def __init__(self, db):
            self.db = db

        async def get_by_id(self, document_id, user_id=None):
            return SimpleNamespace(
                id=document_id,
                status="failed",
                extraction_metadata_json="{}",
                extraction_error=PRIVATE_ERROR,
            )

    monkeypatch.setattr(deep_review_router, "DocumentsService", FakeDocumentsService)

    response = await deep_review_router.get_uploaded_document_analysis_status(
        43,
        current_user=SimpleNamespace(id="ocr-runtime-user"),
        db=object(),
    )
    rendered = json.dumps(response.model_dump(), ensure_ascii=False)

    assert response.success is True
    assert response.error == "ocr_failed"
    assert response.ocr_readiness["status"] == "ocr_failed"
    assert response.ocr_readiness["retry_state"]["latest_failure_reason"] == "ocr_failed"
    assert "PRIVATE_TEXT" not in rendered
    assert "client@example.test" not in rendered
    assert "contract.pdf" not in rendered
    assert "C:\\Users\\client" not in rendered
