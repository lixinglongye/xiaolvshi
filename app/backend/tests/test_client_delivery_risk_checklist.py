import json
import re

from services.client_delivery_risk_checklist import ClientDeliveryRiskChecklistService


def test_client_delivery_risk_checklist_contains_required_sections():
    checklist = ClientDeliveryRiskChecklistService().build_checklist()

    assert checklist["status"] == "ready"
    assert checklist["delivery_allowed_by_default"] is False
    assert checklist["blocking_items"]
    assert checklist["client_disclosures"]
    assert checklist["lawyer_review_items"]
    assert checklist["audit_record_requirements"]
    assert checklist["low_resource_validation_commands"]
    assert checklist["privacy_notes"]


def test_client_delivery_risk_checklist_blocks_missing_citation_or_evidence():
    checklist = ClientDeliveryRiskChecklistService().build_checklist()

    evidence_blockers = [
        item
        for item in checklist["blocking_items"]
        if any("citation" in evidence or "evidence" in evidence for evidence in item["required_evidence"])
    ]

    assert evidence_blockers
    assert any(item["id"] == "citation-evidence-required" for item in evidence_blockers)
    assert any("Unsupported conclusions are blocked" in criterion for item in evidence_blockers for criterion in item["acceptance_criteria"])


def test_client_delivery_risk_checklist_includes_i18n_not_legal_advice_signal():
    checklist = ClientDeliveryRiskChecklistService().build_checklist()
    serialized = json.dumps(checklist, ensure_ascii=False).lower()

    assert "not legal advice" in serialized
    assert "delivery.disclosure.not_legal_advice" in serialized
    assert any(
        disclosure["i18n_key"] == "delivery.disclosure.not_legal_advice"
        for disclosure in checklist["client_disclosures"]
    )


def test_client_delivery_risk_checklist_has_distinct_client_and_lawyer_views():
    checklist = ClientDeliveryRiskChecklistService().build_checklist()

    client_view = checklist["perspectives"]["client"]
    lawyer_view = checklist["perspectives"]["lawyer"]

    assert "must_see_before_delivery" in client_view
    assert "must_confirm_before_delivery" in lawyer_view
    assert len(client_view["must_see_before_delivery"]) >= 3
    assert len(lawyer_view["must_confirm_before_delivery"]) >= 3


def test_client_delivery_risk_checklist_payload_has_no_credentials_or_addresses():
    checklist = ClientDeliveryRiskChecklistService().build_checklist()
    serialized = json.dumps(checklist, ensure_ascii=False)
    address_pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    credential_patterns = [
        r"sk-[A-Za-z0-9]{20,}",
        r"(?i)(pwd|pass\s*word|token)\s*[:=]",
    ]

    assert not re.search(address_pattern, serialized)
    assert all(not re.search(pattern, serialized) for pattern in credential_patterns)


def test_client_delivery_risk_checklist_route_returns_checklist():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/client-delivery-risk-checklist")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["delivery_allowed_by_default"] is False
