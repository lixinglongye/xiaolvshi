from services import model_catalog
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_catalog import ModelProfile


def test_capability_matrix_recommends_cheapest_fast_and_ocr_models():
    matrix = ModelCapabilityMatrixService().build_matrix()
    rows = {row["task"]: row for row in matrix["tasks"]}

    assert rows["fast"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["ocr"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["classification"]["recommended_model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["runtime_default_is_recommended"] is True
    assert rows["ocr"]["runtime_default_is_recommended"] is True
    assert rows["classification"]["runtime_default_is_recommended"] is True


def test_capability_matrix_keeps_premium_as_pdf_exception():
    matrix = ModelCapabilityMatrixService().build_matrix()
    rows = {row["task"]: row for row in matrix["tasks"]}

    assert rows["pdf"]["recommended_model"] == "gemini-2.5-pro"
    assert "pdf" in matrix["coverage"]["premium_exception_tasks"]
    assert rows["pdf"]["candidates"][0]["cost_tier"] == "premium"


def test_capability_matrix_supports_gemini_3_agentic_and_grounding_tasks():
    matrix = ModelCapabilityMatrixService().build_matrix()
    rows = {row["task"]: row for row in matrix["tasks"]}

    assert rows["agentic"]["recommended_model"] == "gemini-3.1-flash-lite"
    assert rows["agentic"]["runtime_default_is_recommended"] is True
    assert rows["grounded-research"]["recommended_model"] == "gemini-3.1-flash-lite"
    assert rows["grounded-research"]["runtime_default_is_recommended"] is True
    assert "gemini-3.1-flash-lite" in matrix["coverage"]["recommended_models"]
    assert "sk-" not in str(matrix)


def test_capability_matrix_recommendation_follows_catalog_derived_selector(monkeypatch):
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

    matrix = ModelCapabilityMatrixService().build_matrix()
    rows = {row["task"]: row for row in matrix["tasks"]}

    assert rows["fast"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["ocr"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["agentic"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert rows["fast"]["runtime_default_model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["runtime_default_is_recommended"] is False


def test_model_ops_route_includes_capability_matrix():
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
    assert payload["capability_matrix"]["status"] == "ready"
    assert payload["capability_matrix"]["coverage"]["task_count"] >= 6
