from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService
from services.route_telemetry_remediation_plan import RouteTelemetryRemediationPlanService
from services.route_telemetry_repository import RouteTelemetryRepositoryService
from services.route_telemetry_triage_queue import RouteTelemetryTriageQueueService


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


def _remediation_from_repository(repository: dict) -> dict:
    summary = RouteTelemetryOpsSummaryService().build_summary(repository)
    triage = RouteTelemetryTriageQueueService().build_queue(summary)
    return RouteTelemetryRemediationPlanService().build_plan(triage)


def test_route_telemetry_remediation_is_ready_with_empty_repository(tmp_path):
    repository = RouteTelemetryRepositoryService(tmp_path).build_repository()

    result = _remediation_from_repository(repository)

    assert result["status"] == "ready"
    assert result["summary"]["source_triage_status"] == "ready"
    assert result["summary"]["remediation_step_count"] == 1
    assert result["summary"]["configuration_written"] is False
    assert result["summary"]["newapi_called"] is False
    assert result["remediation_steps"][0]["requires_env_change"] is False
    assert "Collect sanitized staging route events" in result["recommended_actions"][0]
    assert "sk-" not in str(result)


def test_route_telemetry_remediation_passes_without_changes(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events([_event(f"route-event-{index:03d}") for index in range(12)])

    result = _remediation_from_repository(repository)

    assert result["status"] == "pass"
    assert result["summary"]["blocking_step_count"] == 0
    assert result["summary"]["env_change_count"] == 0
    assert result["recommended_env"] == []
    assert result["remediation_steps"][0]["id"] == "remediate-route-telemetry-no-action"


def test_route_telemetry_remediation_prioritizes_premium_drift(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events(
        [
            _event("route-event-001", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-002", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-003", model="gateway/custom-unknown", success=True),
        ]
    )

    result = _remediation_from_repository(repository)

    assert result["status"] == "fail"
    assert result["summary"]["blocking_step_count"] > 0
    assert result["summary"]["manual_review_step_count"] > 0
    assert any(step["task"] == "fast" for step in result["remediation_steps"])
    assert any(step["task"] == "review" for step in result["remediation_steps"])
    assert any("route telemetry" in step["reason"].lower() for step in result["remediation_steps"])
    assert any("cheap-first" in action for action in result["recommended_actions"])


def test_route_telemetry_remediation_routes_are_available(tmp_path, monkeypatch):
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
    response = testclient.TestClient(app).get("/api/v1/maintenance/route-telemetry-remediation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["source_triage_item_count"] == 0


def test_model_ops_route_includes_route_telemetry_remediation(tmp_path, monkeypatch):
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
    assert payload["route_telemetry_remediation"]["status"] == "ready"
    assert any(
        check["source_key"] == "route_telemetry_remediation"
        for check in payload["model_ops_readiness"]["checks"]
    )
