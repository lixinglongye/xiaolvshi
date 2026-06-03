from services.model_cost_forecast import ModelCostForecastService
from services.model_cost_guardrails import CostGuardrailThresholds, ModelCostGuardrailService


def _usage_snapshot(
    *,
    requests: int = 10,
    failures: int = 0,
    estimated_cost_usd: float = 1.0,
    unpriced_model_count: int = 0,
    premium_requests: int = 0,
):
    cheap_requests = max(0, requests - premium_requests)
    return {
        "totals": {
            "requests": requests,
            "successes": max(0, requests - failures),
            "failures": failures,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": estimated_cost_usd,
            "priced_model_count": 1,
            "unpriced_model_count": unpriced_model_count,
        },
        "models": {
            "gemini-2.5-flash-lite": {
                "requests": cheap_requests,
                "estimated_cost_usd": estimated_cost_usd,
                "tasks": {"fast": cheap_requests},
            },
            "gemini-2.5-pro": {
                "requests": premium_requests,
                "estimated_cost_usd": 0.0,
                "tasks": {"pdf": premium_requests},
            },
        },
    }


def test_model_cost_guardrails_pass_when_usage_is_low_and_priced():
    forecast = ModelCostForecastService().build_forecast()
    result = ModelCostGuardrailService().evaluate(_usage_snapshot(), forecast)

    assert result["status"] == "pass"
    assert result["blocking_check_ids"] == []
    assert result["warning_check_ids"] == []
    assert "sk-" not in str(result)


def test_model_cost_guardrails_warn_on_unpriced_model():
    forecast = ModelCostForecastService().build_forecast()
    result = ModelCostGuardrailService().evaluate(
        _usage_snapshot(unpriced_model_count=1),
        forecast,
    )

    assert result["status"] == "warn"
    assert "unpriced-models" in result["warning_check_ids"]
    assert any("unpriced" in action for action in result["recommended_actions"])


def test_model_cost_guardrails_fail_on_budget_and_premium_ratio():
    forecast = ModelCostForecastService().build_forecast()
    result = ModelCostGuardrailService().evaluate(
        _usage_snapshot(requests=10, estimated_cost_usd=150, premium_requests=6),
        forecast,
        CostGuardrailThresholds(monthly_budget_usd=100),
    )

    assert result["status"] == "fail"
    assert "actual-cost-budget" in result["blocking_check_ids"]
    assert "premium-request-ratio" in result["blocking_check_ids"]


def test_model_cost_guardrails_fail_on_high_failure_rate():
    forecast = ModelCostForecastService().build_forecast()
    result = ModelCostGuardrailService().evaluate(
        _usage_snapshot(requests=10, failures=3),
        forecast,
    )

    assert result["status"] == "fail"
    assert "model-failure-rate" in result["blocking_check_ids"]


def test_model_ops_route_includes_cost_guardrails():
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
    assert payload["cost_guardrails"]["status"] in {"pass", "warn", "fail"}
    assert payload["cost_guardrails"]["checks"]
