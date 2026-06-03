from services.model_route_guardrails import ModelRouteGuardrailService, RouteGuardrailThresholds
from services.model_route_telemetry import ModelRouteTelemetryRegistry, model_route_telemetry_registry


def _snapshot(
    *,
    requests: int = 10,
    failures: int = 0,
    downgraded: int = 0,
    over_budget: int = 0,
    operator_review: int = 0,
    allowed_over_budget: int = 0,
    unknown_price: int = 0,
) -> dict:
    return {
        "status": "ready",
        "summary": {
            "request_count": requests,
            "auto_inferred_ratio": 0.0,
            "downgrade_ratio": downgraded / requests if requests else 0.0,
            "over_budget_request_ratio": over_budget / requests if requests else 0.0,
            "failure_rate": failures / requests if requests else 0.0,
            "operator_review_request_count": operator_review,
            "allowed_over_budget_count": allowed_over_budget,
            "unknown_price_model_count": unknown_price,
        },
        "totals": {
            "requests": requests,
            "successes": max(0, requests - failures),
            "failures": failures,
            "auto_inferred": 0,
            "explicit_task": requests,
            "downgraded_to_recommended": downgraded,
            "over_budget_requested": over_budget,
            "operator_review_requested": operator_review,
            "allowed_over_budget": allowed_over_budget,
            "unknown_price_model": unknown_price,
            "stream_requests": 0,
            "last_seen_at": 0.0,
            "models": {"gemini-2.5-flash-lite": requests},
        },
        "by_task": {},
        "by_inference_source": {},
    }


def test_model_route_guardrails_pass_with_empty_telemetry():
    telemetry = ModelRouteTelemetryRegistry().snapshot()
    result = ModelRouteGuardrailService().evaluate(telemetry)

    assert result["status"] == "pass"
    assert result["summary"]["request_count"] == 0
    assert result["blocking_check_ids"] == []
    assert result["warning_check_ids"] == []
    assert "staging traffic" in result["checks"][1]["reason"]
    assert "sk-" not in str(result)


def test_model_route_guardrails_fail_on_routing_drift():
    result = ModelRouteGuardrailService().evaluate(
        _snapshot(
            requests=10,
            failures=3,
            downgraded=4,
            over_budget=3,
            operator_review=3,
        )
    )

    assert result["status"] == "fail"
    assert "route-failure-rate" in result["blocking_check_ids"]
    assert "over-budget-route-ratio" in result["blocking_check_ids"]
    assert "downgrade-ratio" in result["blocking_check_ids"]
    assert "operator-review-route-ratio" in result["blocking_check_ids"]


def test_model_route_guardrails_warn_on_unknown_and_allowed_over_budget():
    result = ModelRouteGuardrailService().evaluate(
        _snapshot(
            requests=10,
            allowed_over_budget=1,
            unknown_price=1,
        )
    )

    assert result["status"] == "warn"
    assert result["blocking_check_ids"] == []
    assert "unknown-price-route-count" in result["warning_check_ids"]
    assert "allowed-over-budget-count" in result["warning_check_ids"]


def test_model_route_guardrails_accept_custom_thresholds():
    result = ModelRouteGuardrailService().evaluate(
        _snapshot(requests=10, over_budget=1),
        RouteGuardrailThresholds(
            warn_over_budget_route_ratio=0.2,
            fail_over_budget_route_ratio=0.4,
        ),
    )

    assert result["status"] == "pass"
    assert result["summary"]["over_budget_route_ratio"] == 0.1


def test_model_ops_route_includes_route_guardrails():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    model_route_telemetry_registry.reset()

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["route_guardrails"]["status"] == "pass"
    assert payload["route_guardrails"]["checks"]
