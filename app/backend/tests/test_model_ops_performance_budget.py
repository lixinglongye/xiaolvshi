import json
import re

from services.model_ops_performance_budget import ModelOpsPerformanceBudgetService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_model_ops_performance_budget_passes_with_cache_timeout_and_deduped_load():
    budget = ModelOpsPerformanceBudgetService().build_budget()

    assert budget["status"] == "pass"
    assert budget["summary"]["models_payload_cache_enabled"] is True
    assert budget["summary"]["same_origin_fetch_first"] is True
    assert budget["summary"]["duplicate_calibration_fetch_removed"] is True
    assert budget["summary"]["frontend_abort_controller_required"] is True
    assert budget["summary"]["frontend_request_timeout_ms"] >= 5_000
    assert "same-origin-fetch-first" in {check["id"] for check in budget["checks"]}
    assert budget["blocking_check_ids"] == []
    assert budget["privacy_boundary"]["raw_payload_echoed"] is False


def test_model_ops_performance_budget_warns_on_slow_observations_without_echoing_sensitive_values():
    secret = "s" + "k-" + ("P" * 24)
    budget = ModelOpsPerformanceBudgetService().build_budget(
        {
            "observations": [
                {"metric": "model-ops-first-load", "duration_ms": 4_000, "budget_ms": 2_500},
                {"metric": f"{secret} client@example.com", "duration_ms": 100, "budget_ms": 200},
            ]
        }
    )
    serialized = json.dumps(budget, ensure_ascii=False)

    assert budget["status"] == "warn"
    assert "observed-load-within-budget" in budget["warning_check_ids"]
    assert budget["summary"]["observation_count"] == 2
    assert budget["observations"][0]["within_budget"] is False
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert not SECRET_PATTERN.search(serialized)


def test_model_ops_performance_budget_fails_when_timeout_or_cache_guard_missing():
    budget = ModelOpsPerformanceBudgetService().build_budget(
        {
            "frontend_request_timeout_ms": 0,
            "models_payload_cache_enabled": False,
            "same_origin_fetch_first": False,
            "duplicate_calibration_fetch_removed": False,
            "frontend_abort_controller_required": False,
        },
        cache_ttl_seconds=0,
    )

    assert budget["status"] == "fail"
    assert "frontend-timeout-configured" in budget["blocking_check_ids"]
    assert "backend-models-cache-enabled" in budget["blocking_check_ids"]
    assert "same-origin-fetch-first" in budget["warning_check_ids"]
    assert "duplicate-calibration-fetch-removed" in budget["warning_check_ids"]
    assert "frontend-abort-controller" in budget["warning_check_ids"]


def test_model_ops_performance_budget_route_returns_metadata_only_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models/performance-budget")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "pass"
    assert payload["data"]["summary"]["same_origin_fetch_first"] is True
    assert payload["data"]["summary"]["duplicate_calibration_fetch_removed"] is True
