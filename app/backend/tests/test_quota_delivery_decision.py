import json

import pytest

from services.quota_delivery_decision import QuotaDeliveryDecisionService


PRIVATE_TEXT = "PRIVATE_QUOTA_DELIVERY_TEXT_5e8c11"
PRIVATE_EMAIL = "quota-delivery@example.test"


def test_quota_delivery_decision_allows_ready_export():
    result = QuotaDeliveryDecisionService().decide(
        action="export_report",
        quota_summary={
            "decision_status": "ready",
            "reports_remaining": 3,
            "report_quota_monthly": 20,
            "quota_window": "2026-06",
        },
    )

    assert result["status"] == "ready"
    assert result["action"] == "export_report"
    assert result["reason_codes"] == []
    assert result["reports_remaining"] == 3
    assert result["privacy_boundary"]["raw_document_text_included"] is False


def test_quota_delivery_decision_blocks_exhausted_client_delivery_without_pii_echo():
    result = QuotaDeliveryDecisionService().decide(
        action="deliver_to_client",
        quota_summary={
            "decision_status": "blocked",
            "reason_codes": ["report_quota_exhausted"],
            "reports_remaining": 0,
            "raw_document_text": PRIVATE_TEXT,
            "email": PRIVATE_EMAIL,
        },
        release_decision={"status": "blocked", "reason": PRIVATE_TEXT},
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "blocked"
    assert result["action"] == "deliver_to_client"
    assert "report_quota_blocked" in result["reason_codes"]
    assert "report_quota_exhausted" in result["reason_codes"]
    assert "release_decision_blocked" in result["reason_codes"]
    assert PRIVATE_TEXT not in rendered
    assert PRIVATE_EMAIL not in rendered


def test_quota_delivery_decision_routes_lawyer_review_to_manual_review():
    result = QuotaDeliveryDecisionService().decide(
        action="account_plan_review",
        quota_summary={"decision_status": "ready", "reports_remaining": 5},
        release_decision={"lawyer_review_required": True},
    )

    assert result["status"] == "review_required"
    assert result["action"] == "account_plan_review"
    assert result["reason_codes"] == ["lawyer_review_required"]


def test_quota_delivery_decision_route_is_sanitized():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post(
        "/api/v1/maintenance/billing/quota-delivery-decision",
        json={
            "action": "deliver_to_client",
            "quota_summary": {
                "decision_status": "blocked",
                "reports_remaining": 0,
                "raw_document_text": PRIVATE_TEXT,
                "client_email": PRIVATE_EMAIL,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "blocked"
    assert PRIVATE_TEXT not in response.text
    assert PRIVATE_EMAIL not in response.text
