import pytest


fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")


def _client():
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    return testclient.TestClient(app)


def test_maintenance_selected_source_validation_route_passes_metadata_only_payload():
    response = _client().post(
        "/api/v1/maintenance/legal-rag/selected-source-validation",
        json={
            "metadata": {
                "legal_rag_selected_source_ids": ["law:contract-001", "case_ref_002"],
            },
            "citation_map": {
                "sections": [
                    {"source_id": "law:contract-001"},
                    {"source_ids": ["case_ref_002"]},
                ],
            },
            "generation_plan": {
                "review_steps": [{"selected_source_binding_checked": True}],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    assert payload["success"] is True
    assert data["status"] == "pass"
    assert data["selected_source_ids"] == ["law:contract-001", "case_ref_002"]
    assert data["cited_source_ids"] == ["law:contract-001", "case_ref_002"]
    assert data["reason_codes"] == []
    assert data["privacy_boundary"]["raw_legal_text_included"] is False


def test_maintenance_selected_source_validation_route_blocks_invalid_source_states():
    response = _client().post(
        "/api/v1/maintenance/legal-rag/selected-source-validation",
        json={
            "metadata": {
                "legal_rag_selected_source_ids": [
                    "law:contract-001",
                    "stale-statute",
                    "unknown-guidance",
                    "missing-template",
                ],
                "legal_rag": {
                    "stale_source_ids": ["stale-statute"],
                    "unknown_source_ids": ["unknown-guidance"],
                },
            },
            "citation_map": {
                "citations": [
                    {"source_id": "law:contract-001"},
                    {"source_id": "stale-statute"},
                    {"source_id": "unknown-guidance"},
                    {"source_id": "external-source"},
                ],
            },
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["status"] == "blocked"
    assert data["unexpected_source_ids"] == ["external-source"]
    assert data["missing_selected_source_ids"] == ["missing-template"]
    assert data["stale_source_ids"] == ["stale-statute"]
    assert data["unknown_source_ids"] == ["unknown-guidance", "external-source"]
    assert set(data["reason_codes"]) == {
        "unexpected_cited_source_ids",
        "stale_cited_source_ids",
        "unknown_cited_source_ids",
        "missing_selected_source_citations",
    }


def test_maintenance_selected_source_validation_route_does_not_echo_raw_text_claim_or_pii():
    raw_legal_text = "UNSAFE RAW LEGAL TEXT SHOULD NOT LEAK FROM MAINTENANCE ROUTE"
    user_claim = "UNSAFE USER CLAIM SHOULD NOT LEAK FROM MAINTENANCE ROUTE"
    email = "maintenance-client@example.test"
    phone = "13812345678"

    response = _client().post(
        "/api/v1/maintenance/legal-rag/selected-source-validation",
        json={
            "raw_document_text": raw_legal_text,
            "metadata": {
                "legal_rag_selected_source_ids": ["law:contract-001"],
                "raw_legal_text": raw_legal_text,
                "user_claim": user_claim,
                "client_email": email,
                "phone": phone,
            },
            "citation_map": {
                "citations": [
                    {"source_id": "law:contract-001", "quote": raw_legal_text},
                    {"source_id": raw_legal_text},
                    {"source_id": email},
                    {"source_id": phone},
                ],
                "claim": user_claim,
                "pii": {"email": email, "phone": phone},
            },
            "generation_plan": {
                "claim": user_claim,
                "draft_summary": raw_legal_text,
                "contact": email,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["status"] == "pass_with_warnings"
    assert data["selected_source_ids"] == ["law:contract-001"]
    assert data["cited_source_ids"] == ["law:contract-001"]
    assert data["counts"]["invalid_cited_source_id_count"] == 3
    assert raw_legal_text not in response.text
    assert user_claim not in response.text
    assert email not in response.text
    assert phone not in response.text
