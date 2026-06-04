from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService
from services.route_telemetry_repository import RouteTelemetryRepositoryService


def _event(event_id: str, *, model: str = "gemini-2.5-flash-lite", success: bool = True, over_budget: bool = False) -> dict:
    return {
        "event_id": event_id,
        "event_type": "model_route_decision",
        "timestamp": "2026-06-04T08:00:00Z",
        "route_id": f"fast:{model}",
        "task": "fast",
        "inference_source": "explicit",
        "requested_model": "gemini-2.5-pro" if over_budget else model,
        "resolved_model": model,
        "gateway": "newapi",
        "provider": "google",
        "routed_to_recommended_model": over_budget,
        "is_over_budget": over_budget,
        "requires_operator_review": over_budget,
        "allow_over_budget_model": False,
        "is_known_model": model != "gateway/custom-unknown",
        "estimated_input_tokens": 1200,
        "estimated_output_tokens": 500,
        "estimated_cost_usd": 0.0012,
        "latency_ms": 860,
        "success": success,
        "stream": False,
        "cache_hit": False,
        "http_status": 200 if success else 500,
    }


def test_route_telemetry_ops_summary_is_ready_with_empty_repository(tmp_path):
    repository = RouteTelemetryRepositoryService(tmp_path).build_repository()
    result = RouteTelemetryOpsSummaryService().build_summary(repository)

    assert result["status"] == "ready"
    assert result["summary"]["empty_repository"] is True
    assert result["summary"]["request_count"] == 0
    assert result["blocking_check_ids"] == []
    assert "Collect sanitized staging route events" in result["recommended_actions"][0]
    assert "sk-" not in str(result)


def test_route_telemetry_ops_summary_passes_cheap_first_events(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events(
        [_event(f"route-event-{index:03d}", over_budget=index == 1) for index in range(20)]
    )

    result = RouteTelemetryOpsSummaryService().build_summary(repository)

    assert result["status"] == "pass"
    assert result["summary"]["request_count"] == 20
    assert result["summary"]["downgrade_count"] == 1
    assert result["summary"]["premium_request_count"] == 0
    assert result["summary"]["failure_rate"] == 0.0
    assert result["daily_rows"][0]["day"] == "2026-06-04"
    assert result["daily_rows"][0]["models"]["gemini-2.5-flash-lite"] == 20


def test_route_telemetry_ops_summary_fails_on_routing_drift(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events(
        [
            _event("route-event-001", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-002", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-003", model="gateway/custom-unknown", success=True),
        ]
    )

    result = RouteTelemetryOpsSummaryService().build_summary(repository)

    assert result["status"] == "fail"
    assert "failure-rate" in result["blocking_check_ids"]
    assert "over-budget-ratio" in result["blocking_check_ids"]
    assert "operator-review-ratio" in result["blocking_check_ids"]
    assert "premium-request-ratio" in result["blocking_check_ids"]
    assert "unknown-model-count" in result["warning_check_ids"]
    assert result["summary"]["premium_request_count"] == 2


def test_route_telemetry_ops_summary_routes_are_available(tmp_path, monkeypatch):
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from services import route_telemetry_repository
    from routers.maintenance import router

    monkeypatch.setattr(route_telemetry_repository.settings, "local_storage_dir", str(tmp_path))
    repository_service = RouteTelemetryRepositoryService(tmp_path / "model_ops" / "route_telemetry")
    repository_service.append_events([_event("route-event-001")])

    app = fastapi.FastAPI()
    app.include_router(router)
    response = testclient.TestClient(app).get("/api/v1/maintenance/route-telemetry-ops-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["request_count"] == 1


def test_model_ops_route_includes_route_telemetry_ops_summary(tmp_path, monkeypatch):
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from services import route_telemetry_repository
    from routers.aihub import router

    monkeypatch.setattr(route_telemetry_repository.settings, "local_storage_dir", str(tmp_path))
    app = fastapi.FastAPI()
    app.include_router(router)
    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["route_telemetry_ops_summary"]["status"] == "ready"
    assert any(
        check["source_key"] == "route_telemetry_ops_summary"
        for check in payload["model_ops_readiness"]["checks"]
    )
