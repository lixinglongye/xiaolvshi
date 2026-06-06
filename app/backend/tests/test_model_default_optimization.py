from services import model_catalog
from services.model_catalog import ModelProfile
from services.model_default_optimization import ModelDefaultOptimizationService


def test_default_optimization_passes_for_current_cheap_first_defaults():
    plan = ModelDefaultOptimizationService().build_plan()
    rows = {row["task"]: row for row in plan["recommendations"]}

    assert plan["status"] == "pass"
    assert rows["fast"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["classification"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["ocr"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["review"]["recommended_model"] == "gemini-2.5-flash"
    assert rows["agentic"]["status"] == "pass"
    assert rows["agentic"]["env_var"] == "APP_AI_AGENTIC_MODEL"
    assert rows["agentic"]["recommended_model"] == "gemini-3.1-flash-lite"
    assert rows["grounded-research"]["status"] == "pass"
    assert rows["grounded-research"]["env_var"] == "APP_AI_GROUNDED_RESEARCH_MODEL"
    assert rows["grounded-research"]["recommended_model"] == "gemini-3.1-flash-lite"
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


def test_default_optimization_follows_catalog_derived_future_cheaper_default(monkeypatch):
    future_model = ModelProfile(
        id="gemini-4.0-flash-lite",
        provider="google",
        family="gemini",
        cost_tier="lowest",
        latency_tier="fastest",
        capabilities=("text", "vision", "json", "ocr", "classification", "grounding", "agentic"),
        best_for=("routing", "ocr", "classification", "agentic-routing"),
        input_usd_per_million_tokens=0.05,
        output_usd_per_million_tokens=0.20,
        status="stable",
        context_window_tokens=1_000_000,
    )
    monkeypatch.setattr(
        model_catalog,
        "GEMINI_MODEL_CATALOG",
        (future_model, *model_catalog.GEMINI_MODEL_CATALOG),
    )

    plan = ModelDefaultOptimizationService().build_plan()
    rows = {row["task"]: row for row in plan["recommendations"]}

    assert plan["status"] == "warn"
    assert rows["fast"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["classification"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["ocr"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["agentic"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["fast"]["current_model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["requires_change"] is True
    assert any("APP_AI_FAST_MODEL=gemini-4.0-flash-lite" in action for action in plan["recommended_actions"])


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
