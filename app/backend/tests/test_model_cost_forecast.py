from services.model_cost_forecast import ModelCostForecastService


def test_model_cost_forecast_estimates_monthly_savings_for_cheap_first_tasks():
    forecast = ModelCostForecastService().build_forecast()
    rows = {row["task"]: row for row in forecast["profiles"]}

    assert forecast["status"] == "ready"
    assert forecast["summary"]["profile_count"] >= 5
    assert rows["fast"]["initial_model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["premium_baseline_model"] == "gemini-2.5-pro"
    assert rows["fast"]["estimated_savings_ratio"] > 0.8
    assert rows["review"]["estimated_savings_ratio"] > 0
    assert "sk-" not in str(forecast)


def test_model_cost_forecast_keeps_pdf_as_explicit_premium_exception():
    forecast = ModelCostForecastService().build_forecast()
    rows = {row["task"]: row for row in forecast["profiles"]}

    assert rows["pdf"]["initial_model"] == "gemini-2.5-pro"
    assert rows["pdf"]["premium_baseline_model"] == "gemini-2.5-pro"
    assert rows["pdf"]["estimated_savings_ratio"] == 0
    assert "premium exception" in rows["pdf"]["recommended_action"]


def test_model_cost_forecast_summary_totals_are_priced_and_bounded():
    forecast = ModelCostForecastService().build_forecast()
    summary = forecast["summary"]

    assert summary["priced_profile_count"] == summary["profile_count"]
    assert summary["cheap_first_monthly_cost_usd"] > 0
    assert summary["premium_baseline_monthly_cost_usd"] >= summary["cheap_first_monthly_cost_usd"]
    assert 0 <= summary["estimated_savings_ratio"] <= 1


def test_model_ops_route_includes_cost_forecast():
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
    assert payload["cost_forecast"]["status"] == "ready"
    assert payload["cost_forecast"]["summary"]["profile_count"] >= 5
