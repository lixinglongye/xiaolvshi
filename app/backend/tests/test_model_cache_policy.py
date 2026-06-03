from services import model_cache_policy
from services.model_cache_policy import ModelCachePolicyService


def test_model_cache_policy_passes_for_default_rules():
    result = ModelCachePolicyService().build_policy()
    rows = {row["task"]: row for row in result["rules"]}

    assert result["status"] == "pass"
    assert rows["fast"]["enabled_by_default"] is True
    assert rows["classification"]["cache_mode"] == "hashed-material-fingerprint"
    assert rows["pdf"]["enabled_by_default"] is False
    assert result["summary"]["estimated_monthly_savings_usd"] > 0
    assert "sk-" not in str(result)


def test_model_cache_policy_estimates_savings_from_cost_forecast():
    result = ModelCachePolicyService().build_policy()
    fast = {row["task"]: row for row in result["rules"]}["fast"]

    assert fast["forecast_monthly_cost_usd"] > 0
    assert fast["estimated_monthly_savings_usd"] == round(
        fast["forecast_monthly_cost_usd"] * fast["expected_hit_rate"],
        6,
    )


def test_model_cache_policy_warns_when_forecast_is_missing():
    result = ModelCachePolicyService().build_policy({"profiles": []})
    rows = {row["task"]: row for row in result["rules"]}

    assert result["status"] == "warn"
    assert rows["fast"]["status"] == "warn"
    assert "cache-policy-fast" in result["warning_check_ids"]


def test_model_cache_policy_fails_when_enabled_task_is_not_deterministic(monkeypatch):
    original = model_cache_policy.resolve_generation_request_policy

    def fake_policy(*, task):
        decision = original(task=task)
        if task == "classification":
            return decision.__class__(
                task=decision.task,
                requested_temperature=decision.requested_temperature,
                effective_temperature=0.7,
                requested_max_tokens=decision.requested_max_tokens,
                effective_max_tokens=decision.effective_max_tokens,
                temperature_adjusted=decision.temperature_adjusted,
                max_tokens_adjusted=decision.max_tokens_adjusted,
                response_format_mode=decision.response_format_mode,
                cost_mode=decision.cost_mode,
                reason=decision.reason,
            )
        return decision

    monkeypatch.setattr(model_cache_policy, "resolve_generation_request_policy", fake_policy)

    result = ModelCachePolicyService().build_policy()
    classification = {row["task"]: row for row in result["rules"]}["classification"]

    assert result["status"] == "fail"
    assert classification["status"] == "fail"
    assert "cache-policy-classification" in result["blocking_check_ids"]


def test_model_ops_route_includes_cache_policy():
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
    assert payload["cache_policy"]["status"] in {"pass", "warn", "fail"}
    assert payload["cache_policy"]["rules"]
