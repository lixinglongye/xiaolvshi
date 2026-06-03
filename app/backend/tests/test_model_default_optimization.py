from services import model_catalog
from services.model_default_optimization import ModelDefaultOptimizationService


def test_default_optimization_passes_for_current_cheap_first_defaults():
    plan = ModelDefaultOptimizationService().build_plan()
    rows = {row["task"]: row for row in plan["recommendations"]}

    assert plan["status"] == "pass"
    assert rows["fast"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["classification"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["ocr"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["review"]["recommended_model"] == "gemini-2.5-flash"
    assert rows["pdf"]["requires_operator_review"] is True
    assert "sk-" not in str(plan)


def test_default_optimization_fails_when_fast_default_exceeds_cost_ceiling(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "gemini-2.5-flash", raising=False)

    plan = ModelDefaultOptimizationService().build_plan()
    fast = {row["task"]: row for row in plan["recommendations"]}["fast"]

    assert plan["status"] == "fail"
    assert fast["status"] == "fail"
    assert fast["requires_change"] is True
    assert fast["env_var"] == "APP_AI_FAST_MODEL"
    assert fast["recommended_model"] == "gemini-2.5-flash-lite"
    assert fast["estimated_monthly_savings_usd"] > 0
    assert any("APP_AI_FAST_MODEL=gemini-2.5-flash-lite" in action for action in plan["recommended_actions"])


def test_default_optimization_fails_when_ocr_default_lacks_vision(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ocr_model", "gemini-3.1-flash-lite", raising=False)

    plan = ModelDefaultOptimizationService().build_plan()
    ocr = {row["task"]: row for row in plan["recommendations"]}["ocr"]

    assert plan["status"] == "fail"
    assert ocr["status"] == "fail"
    assert "ocr" in ocr["missing_required_capabilities"]


def test_model_ops_route_includes_default_optimization():
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
    assert payload["default_optimization"]["status"] in {"pass", "warn", "fail"}
    assert payload["default_optimization"]["summary"]["task_count"] >= 7
