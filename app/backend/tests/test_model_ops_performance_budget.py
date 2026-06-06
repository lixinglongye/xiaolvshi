import json
import re

import pytest

from services.model_ops_performance_budget import (
    ModelOpsPerformanceBudgetService,
    model_ops_performance_budget_registry,
)


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


@pytest.fixture(autouse=True)
def clear_model_ops_performance_observations():
    from routers.aihub import _clear_model_ops_payload_cache

    model_ops_performance_budget_registry.clear()
    _clear_model_ops_payload_cache()
    yield
    model_ops_performance_budget_registry.clear()
    _clear_model_ops_payload_cache()


def test_model_ops_performance_budget_passes_with_cache_timeout_and_deduped_load():
    budget = ModelOpsPerformanceBudgetService().build_budget()

    assert budget["status"] == "pass"
    assert budget["summary"]["models_payload_cache_enabled"] is True
    assert budget["summary"]["same_origin_fetch_first"] is True
    assert budget["summary"]["fallback_after_timeout_disabled"] is True
    assert budget["summary"]["frontend_total_timeout_ms"] <= budget["summary"]["frontend_request_timeout_ms"]
    assert budget["summary"]["duplicate_calibration_fetch_removed"] is True
    assert budget["summary"]["frontend_abort_controller_required"] is True
    assert budget["summary"]["frontend_request_timeout_ms"] >= 5_000
    assert "same-origin-fetch-first" in {check["id"] for check in budget["checks"]}
    assert "single-wall-clock-timeout" in {check["id"] for check in budget["checks"]}
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


def test_model_ops_performance_budget_fails_on_repeated_slow_observations():
    budget = ModelOpsPerformanceBudgetService().build_budget(
        {
            "observations": [
                {"metric": "model-ops-first-load", "duration_ms": 4_000, "budget_ms": 2_500},
                {"metric": "model-ops-cache-hit", "duration_ms": 1_200, "budget_ms": 750},
                {"metric": "model-ops-refresh", "duration_ms": 5_500, "budget_ms": 2_500},
            ]
        }
    )

    assert budget["status"] == "fail"
    assert budget["summary"]["slow_observation_count"] == 3
    assert "observed-load-within-budget" in budget["blocking_check_ids"]


def test_model_ops_performance_budget_fails_when_timeout_or_cache_guard_missing():
    budget = ModelOpsPerformanceBudgetService().build_budget(
        {
            "frontend_request_timeout_ms": 0,
            "frontend_total_timeout_ms": 60_000,
            "models_payload_cache_enabled": False,
            "same_origin_fetch_first": False,
            "fallback_after_timeout_disabled": False,
            "duplicate_calibration_fetch_removed": False,
            "frontend_abort_controller_required": False,
        },
        cache_ttl_seconds=0,
    )

    assert budget["status"] == "fail"
    assert "frontend-timeout-configured" in budget["blocking_check_ids"]
    assert "backend-models-cache-enabled" in budget["blocking_check_ids"]
    assert "same-origin-fetch-first" in budget["warning_check_ids"]
    assert "single-wall-clock-timeout" in budget["warning_check_ids"]
    assert "duplicate-calibration-fetch-removed" in budget["warning_check_ids"]
    assert "frontend-abort-controller" in budget["warning_check_ids"]


def test_model_ops_performance_budget_route_returns_metadata_only_payload():
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
    assert payload["data"]["summary"]["fallback_after_timeout_disabled"] is True
    assert payload["data"]["summary"]["duplicate_calibration_fetch_removed"] is True


def test_model_ops_performance_budget_post_reviews_sanitized_observations():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    secret = "s" + "k-" + ("Q" * 24)

    response = testclient.TestClient(app).post(
        "/api/v1/aihub/models/performance-budget",
        json={
            "observations": [
                {"metric": "model-ops-first-load", "duration_ms": 4_000, "budget_ms": 2_500},
                {"metric": f"{secret} client@example.com", "duration_ms": 100, "budget_ms": 200},
            ],
            "raw_payload": "must not echo",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["success"] is True
    assert payload["data"]["status"] == "warn"
    assert payload["data"]["summary"]["observation_count"] == 2
    assert "observed-load-within-budget" in payload["data"]["warning_check_ids"]
    assert "model-ops-performance-budget" in payload["model_ops_readiness"]["warning_check_ids"]
    release_check = next(
        check
        for check in payload["cheap_first_release_decision"]["checks"]
        if check["source_key"] == "model_ops_performance_budget"
    )
    assert release_check["status"] == "warn"
    assert "observed-load-within-budget" in release_check["source_warning_ids"]
    assert payload["cheap_first_release_decision"]["summary"]["maintainer_review_required"] is True
    assert payload["data"]["source"] == "latest_sanitized_performance_observation"
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert "must not echo" not in serialized
    assert not SECRET_PATTERN.search(serialized)


def test_model_ops_performance_budget_post_blocks_aggregate_on_repeated_slow_observations():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post(
        "/api/v1/aihub/models/performance-budget",
        json={
            "observations": [
                {"metric": "model-ops-first-load", "duration_ms": 4_000, "budget_ms": 2_500},
                {"metric": "model-ops-cache-hit", "duration_ms": 1_200, "budget_ms": 750},
                {"metric": "model-ops-refresh", "duration_ms": 5_500, "budget_ms": 2_500},
            ],
            "raw_payload": "must not echo",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["success"] is True
    assert payload["data"]["status"] == "fail"
    assert payload["data"]["source"] == "latest_sanitized_performance_observation"
    assert "observed-load-within-budget" in payload["data"]["blocking_check_ids"]
    assert payload["model_ops_readiness"]["status"] == "fail"
    assert "model-ops-performance-budget" in payload["model_ops_readiness"]["blocking_check_ids"]
    assert payload["cheap_first_release_decision"]["status"] == "fail"
    assert "performance-budget-review" in payload["cheap_first_release_decision"]["blocking_check_ids"]
    assert "must not echo" not in serialized
    assert not SECRET_PATTERN.search(serialized)

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["model_ops_performance_budget"]["status"] == "fail"
    assert models_payload["model_ops_performance_budget"]["source"] == "latest_sanitized_performance_observation"
    assert models_payload["model_ops_readiness"]["status"] == "fail"
    assert "model-ops-performance-budget" in models_payload["model_ops_readiness"]["blocking_check_ids"]
    assert models_payload["cheap_first_release_decision"]["status"] == "fail"
    assert "performance-budget-review" in models_payload["cheap_first_release_decision"]["blocking_check_ids"]
