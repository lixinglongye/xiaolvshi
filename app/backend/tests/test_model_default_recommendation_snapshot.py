import re

from services import model_catalog
from services.model_default_recommendation_snapshot import ModelDefaultRecommendationSnapshotService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password", re.IGNORECASE)


def test_model_default_recommendation_snapshot_passes_for_current_defaults():
    snapshot = ModelDefaultRecommendationSnapshotService().build_snapshot()
    rows = {row["role"]: row for row in snapshot["role_recommendations"]}

    assert snapshot["status"] in {"pass", "warn"}
    assert rows["fast"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["classification"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["ocr"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["review"]["recommended_model"] == "gemini-2.5-flash"
    assert rows["agentic"]["recommended_model"] == "gemini-3.1-flash-lite"
    assert rows["agentic"]["status"] == "pass"
    assert rows["grounded-research"]["recommended_model"] == "gemini-3.1-flash-lite"
    assert rows["grounded-research"]["status"] == "pass"
    assert rows["pdf"]["operator_review_required"] is True
    assert not SECRET_PATTERN.search(str(snapshot))


def test_model_default_recommendation_snapshot_blocks_premium_fast_default(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "gemini-2.5-pro", raising=False)

    snapshot = ModelDefaultRecommendationSnapshotService().build_snapshot()
    fast = {row["role"]: row for row in snapshot["role_recommendations"]}["fast"]

    assert snapshot["status"] == "fail"
    assert fast["status"] == "fail"
    assert fast["recommended_model"] == "gemini-2.5-flash-lite"
    assert "high-volume" in fast["reason"]
    assert "fast" in snapshot["blocked_default_roles"]


def test_model_default_recommendation_snapshot_warns_unknown_gemini_like_models():
    snapshot = ModelDefaultRecommendationSnapshotService().build_snapshot(
        ["newapi/gemini-4-flash-lite", {"id": "models/gemini-2.5-flash-lite"}]
    )
    observed = {row["model"]: row for row in snapshot["observed_gateway_models"]}

    assert observed["newapi/gemini-4-flash-lite"]["status"] == "catalog_review"
    assert observed["models/gemini-2.5-flash-lite"]["status"] == "known"
    assert "newapi/gemini-4-flash-lite" in snapshot["catalog_review_models"]


def test_model_default_recommendation_snapshot_prefix_examples_are_supported():
    snapshot = ModelDefaultRecommendationSnapshotService().build_snapshot()

    assert "models/gemini-2.5-flash-lite" in snapshot["newapi_prefix_compatibility"]
    assert "openrouter/google/gemini-2.5-flash-lite" in snapshot["newapi_prefix_compatibility"]
    assert any(row["env_var"] == "APP_AI_FAST_MODEL" for row in snapshot["recommended_env"])
    assert any(row["env_var"] == "APP_AI_AGENTIC_MODEL" for row in snapshot["recommended_env"])
    assert any(row["env_var"] == "APP_AI_GROUNDED_RESEARCH_MODEL" for row in snapshot["recommended_env"])


def test_model_ops_route_includes_default_recommendation_snapshot():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["default_recommendation_snapshot"]["summary"]["role_count"] >= 6
    assert payload["default_recommendation_snapshot"]["summary"]["cheap_first_ready"] in {True, False}
