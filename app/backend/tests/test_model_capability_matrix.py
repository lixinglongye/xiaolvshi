from services.model_capability_matrix import ModelCapabilityMatrixService


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
    assert rows["grounded-research"]["recommended_model"] in {"gemini-3.1-flash-lite", "gemini-3.5-flash"}
    assert "gemini-3.1-flash-lite" in matrix["coverage"]["recommended_models"]
    assert "sk-" not in str(matrix)


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
