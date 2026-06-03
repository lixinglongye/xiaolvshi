import re

from services.product_feature_gap_radar import (
    ProductFeatureGapRadarService,
    priority_band,
    priority_score,
)


def test_product_feature_gap_radar_is_incomplete_and_product_wide():
    radar = ProductFeatureGapRadarService().build_radar()

    assert radar["status"] == "incomplete"
    assert radar["summary"]["ready_for_public_feature_claim"] is False
    assert radar["summary"]["feature_gap_count"] >= 11
    assert radar["summary"]["high_priority_count"] >= 8
    assert {
        "case_management",
        "document_generation",
        "contract_review",
        "evidence",
        "document_intake",
        "collaboration",
        "billing",
        "feedback",
        "model_ops",
        "legal_knowledge",
        "safety",
    }.issubset(set(radar["summary"]["modules"]))


def test_product_feature_gap_radar_prioritizes_by_score():
    radar = ProductFeatureGapRadarService().build_radar()
    gaps = radar["feature_gaps"]
    scores = [gap["priority_score"] for gap in gaps]

    assert scores == sorted(scores, reverse=True)
    assert gaps[0]["priority_band"] == "critical"
    assert "case-workbench" in radar["summary"]["top_gap_ids"]
    assert "safety-compliance" in radar["summary"]["top_gap_ids"]
    assert "legal-knowledge-rag" in radar["summary"]["top_gap_ids"]


def test_product_feature_gap_radar_has_evidence_paths_and_delivery_phases():
    radar = ProductFeatureGapRadarService().build_radar()

    assert all(gap["evidence_paths"] for gap in radar["feature_gaps"])
    assert all(
        path.startswith(("app/backend/", "app/frontend/", "docs/"))
        for gap in radar["feature_gaps"]
        for path in gap["evidence_paths"]
    )
    assert [phase["id"] for phase in radar["delivery_phases"]] == [
        "phase-1-core-legal-workflow",
        "phase-2-quality-and-ops",
        "phase-3-commercial-workspace",
    ]
    assert any("tests/test_product_feature_gap_radar.py" in command for command in radar["validation_commands"])


def test_product_feature_gap_radar_has_no_secret_material():
    radar = ProductFeatureGapRadarService().build_radar()

    assert "privacy" in radar["privacy_note"].lower()
    assert not re.search(r"sk-[A-Za-z0-9]{20,}", str(radar))
    assert "password" in radar["privacy_note"].lower()


def test_priority_score_and_band_are_bounded():
    assert priority_score(10, 10, 0, 10) == 100
    assert priority_score(1, 1, 10, 1) == 0
    assert priority_band(90) == "critical"
    assert priority_band(75) == "high"
    assert priority_band(55) == "medium"
    assert priority_band(54) == "low"


def test_product_feature_gap_radar_route_returns_gaps():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/product-feature-gaps")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "incomplete"
    assert payload["data"]["summary"]["ready_for_public_feature_claim"] is False
