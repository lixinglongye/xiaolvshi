from services import model_catalog
from services.model_request_cost_bounds import ModelRequestCostBoundsService


def test_request_cost_bounds_pass_for_default_cheap_first_tasks():
    result = ModelRequestCostBoundsService().evaluate()
    rows = {row["task"]: row for row in result["task_bounds"]}

    assert result["status"] == "pass"
    assert rows["fast"]["model"] == "gemini-2.5-flash-lite"
    assert rows["classification"]["model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["default_request_cost_usd"] < rows["fast"]["fail_default_cost_usd"]
    assert result["summary"]["priced_task_count"] == result["summary"]["task_count"]
    assert "sk-" not in str(result)


def test_request_cost_bounds_fail_when_fast_task_uses_expensive_model(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "gemini-2.5-pro", raising=False)

    result = ModelRequestCostBoundsService().evaluate()
    fast = {row["task"]: row for row in result["task_bounds"]}["fast"]

    assert result["status"] == "fail"
    assert fast["status"] == "fail"
    assert fast["cost_tier"] == "premium"
    assert "request-cost-bound-fast" in result["blocking_check_ids"]


def test_request_cost_bounds_warn_for_unknown_model_pricing(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_review_model", "gemini-custom-review", raising=False)

    result = ModelRequestCostBoundsService().evaluate()
    review = {row["task"]: row for row in result["task_bounds"]}["review"]

    assert result["status"] == "warn"
    assert review["status"] == "warn"
    assert review["is_priced"] is False
    assert "request-cost-bound-review" in result["warning_check_ids"]


def test_model_ops_route_includes_request_cost_bounds():
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
    assert payload["request_cost_bounds"]["status"] in {"pass", "warn", "fail"}
    assert payload["request_cost_bounds"]["task_bounds"]
