import json
from types import SimpleNamespace

import pytest

from routers.deep_review import (
    _deep_review_export_blocker_detail,
    _deep_review_export_readiness,
)


PRIVATE_TEXT = "PRIVATE_DEEP_REVIEW_EXPORT_TEXT_74af5b"
PRIVATE_EMAIL = "deep-review-export@example.test"


def _ready_report() -> dict:
    return {
        "report_meta": {
            "report_id": "deep-review-ready",
            "selected_source_validation": {"delivery_status": "ready"},
        },
        "risk_scoring": {"overall_score": 22, "overall_level": "low", "counts": {"low": 1}},
        "citation_audit": {
            "status": "pass",
            "source_count": 1,
            "citation_count": 1,
            "verified_source_count": 1,
            "reviewable_source_count": 1,
        },
        "evidence_audit": {
            "status": "pass",
            "risk_count": 1,
            "risk_evidence_coverage": 1,
            "blocking_pending_fact_count": 0,
        },
        "release_decision": {"status": "ready_for_spot_check"},
        "legal_authority_appendix": [{"source_id": "law:contract:001"}],
        "risk_items": [{"risk_id": "R-001", "risk_level": "low"}],
        "raw_document_text": "Ready report content can be exported after the gate passes.",
    }


def _blocked_report() -> dict:
    return {
        "report_meta": {
            "report_id": "deep-review-blocked",
            "selected_source_validation": {
                "delivery_status": "blocked",
                "private_note": PRIVATE_TEXT,
            },
        },
        "release_decision": {
            "status": "blocked",
            "blocking_reasons": [PRIVATE_TEXT],
        },
        "raw_document_text": PRIVATE_TEXT,
        "client_email": PRIVATE_EMAIL,
    }


def test_deep_review_export_readiness_allows_complete_metadata():
    result = _deep_review_export_readiness(_ready_report())

    assert result["status"] == "ready"
    assert result["missing_sections"] == []
    assert result["selected_source_validation_status"] == "ready"


def test_deep_review_export_blocker_detail_is_metadata_only():
    readiness = _deep_review_export_readiness(_blocked_report())
    detail = _deep_review_export_blocker_detail(readiness)
    rendered = json.dumps(detail, ensure_ascii=False)

    assert detail["status"] == "blocked"
    assert "missing_required_export_sections" in detail["reason_codes"]
    assert "release_decision_blocked" in detail["reason_codes"]
    assert "selected_source_validation_blocked" in detail["reason_codes"]
    assert detail["privacy_boundary"]["raw_document_text_included"] is False
    assert PRIVATE_TEXT not in rendered
    assert PRIVATE_EMAIL not in rendered


@pytest.fixture
def app(monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    import routers.deep_review as deep_review_router

    class FakeDeepReviewService:
        def prepare_report_for_display(self, report):
            return report

    class FakeReviewReportsService:
        def __init__(self, db):
            self.db = db

        async def get_by_id(self, report_id, user_id=None):
            return SimpleNamespace(
                id=report_id,
                full_report_json=json.dumps(deep_review_router._test_stored_report, ensure_ascii=False),
            )

    monkeypatch.setattr(deep_review_router, "DeepReviewService", FakeDeepReviewService)
    monkeypatch.setattr(deep_review_router, "Review_reportsService", FakeReviewReportsService)
    deep_review_router._test_stored_report = _ready_report()

    test_app = fastapi.FastAPI()
    test_app.include_router(deep_review_router.router)

    async def override_get_export_user():
        return SimpleNamespace(id="deep-review-export-user")

    async def override_get_db():
        yield object()

    test_app.dependency_overrides[deep_review_router.get_export_user] = override_get_export_user
    test_app.dependency_overrides[deep_review_router.get_db] = override_get_db
    test_app.state.deep_review_router = deep_review_router
    yield test_app
    test_app.dependency_overrides.clear()


async def _request(app, path: str):
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": [(b"host", b"testserver")],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "root_path": "",
    }
    sent = []
    received = False

    async def receive():
        nonlocal received
        if received:
            return {"type": "http.disconnect"}
        received = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    status_code = next(message["status"] for message in sent if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    return SimpleNamespace(
        status_code=status_code,
        content=body,
        json=lambda: json.loads(body.decode("utf-8")),
    )


@pytest.mark.asyncio
async def test_deep_review_export_route_downloads_after_readiness_passes(app):
    app.state.deep_review_router._test_stored_report = _ready_report()

    response = await _request(app, "/api/v1/deep-review/reports/7/export/json")

    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert b"deep-review-ready" in response.content


@pytest.mark.asyncio
async def test_deep_review_export_route_blocks_before_serializing_private_report(app):
    app.state.deep_review_router._test_stored_report = _blocked_report()

    response = await _request(app, "/api/v1/deep-review/reports/8/export/json")
    rendered = json.dumps(response.json(), ensure_ascii=False)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "deep_review_export_not_ready"
    assert "selected_source_validation_blocked" in response.json()["detail"]["reason_codes"]
    assert response.json()["detail"]["privacy_boundary"]["raw_document_text_included"] is False
    assert PRIVATE_TEXT not in rendered
    assert PRIVATE_EMAIL not in rendered
