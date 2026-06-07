from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService
from services.route_telemetry_repository import RouteTelemetryRepositoryService
from services.route_telemetry_triage_queue import RouteTelemetryTriageQueueService


def _event(
    event_id: str,
    *,
    model: str = "gemini-2.5-flash-lite",
    success: bool = True,
    over_budget: bool = False,
    reason_codes=None,
) -> dict:
    if reason_codes is None:
        if over_budget:
            reason_codes = [
                "known_catalog_model",
                "over_task_budget",
                "operator_review_required",
                "routed_to_recommended_model",
                "resolved_to_recommended_model",
            ]
        elif model == "gateway/custom-unknown":
            reason_codes = ["unknown_catalog_model", "unverified_price_tier", "gateway_passthrough"]
        else:
            reason_codes = ["known_catalog_model", "within_task_budget"]
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
        "reason_codes": reason_codes,
    }


def test_route_telemetry_triage_queue_is_ready_with_empty_repository(tmp_path):
    repository = RouteTelemetryRepositoryService(tmp_path).build_repository()
    summary = RouteTelemetryOpsSummaryService().build_summary(repository)

    result = RouteTelemetryTriageQueueService().build_queue(summary)

    assert result["status"] == "ready"
    assert result["summary"]["empty_repository"] is True
    assert result["summary"]["blocking_item_count"] == 0
    assert result["summary"]["info_item_count"] == 1
    assert result["triage_items"][0]["id"] == "route-telemetry-collect-staging-events"
    assert result["privacy_boundary"]["raw_payload_storage_allowed"] is False
    assert "sk-" not in str(result)


def test_route_telemetry_triage_queue_passes_without_actions(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events([_event(f"route-event-{index:03d}") for index in range(12)])
    summary = RouteTelemetryOpsSummaryService().build_summary(repository)

    result = RouteTelemetryTriageQueueService().build_queue(summary)

    assert result["status"] == "pass"
    assert result["summary"]["triage_item_count"] == 0
    assert result["recommended_actions"] == [
        "No route telemetry triage actions are currently blocking cheap-first model operations."
    ]


def test_route_telemetry_triage_queue_prioritizes_drift(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events(
        [
            _event("route-event-001", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-002", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-003", model="gateway/custom-unknown", success=True),
        ]
    )
    summary = RouteTelemetryOpsSummaryService().build_summary(repository)

    result = RouteTelemetryTriageQueueService().build_queue(summary)

    assert result["status"] == "fail"
    assert result["summary"]["blocking_item_count"] >= 4
    assert result["summary"]["cheap_first_action_count"] >= 4
    assert result["triage_items"][0]["severity"] == "fail"
    assert "route-telemetry-failure-rate" in result["blocking_item_ids"]
    assert "route-telemetry-premium-request-ratio" in result["blocking_item_ids"]
    assert any(item["check_id"] == "daily-route-hotspot" for item in result["triage_items"])
    reason_hotspots = [item for item in result["triage_items"] if item["check_id"] == "reason-code-hotspot"]
    assert reason_hotspots
    assert {"over_task_budget", "operator_review_required", "unknown_catalog_model"}.issubset(
        {item["reason_code"] for item in reason_hotspots}
    )
    assert all("reason_code_counts" in item for item in reason_hotspots)
    assert any("cheap-first" in action for action in result["recommended_actions"])


def test_route_telemetry_triage_queue_prioritizes_unknown_reason_codes(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events(
        [_event("route-event-001", reason_codes=["unknown_reason_code"])]
    )
    summary = RouteTelemetryOpsSummaryService().build_summary(repository)

    result = RouteTelemetryTriageQueueService().build_queue(summary)

    assert result["status"] == "warn"
    assert "route-telemetry-unknown-reason-code-count" in result["warning_item_ids"]
    assert any(
        item["check_id"] == "reason-code-hotspot"
        and item["reason_code"] == "unknown_reason_code"
        and item["source_day"] == "2026-06-04"
        for item in result["triage_items"]
    )
    assert any("allowlist" in action for action in result["recommended_actions"])


def test_route_telemetry_triage_routes_are_available(tmp_path, monkeypatch):
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
    response = testclient.TestClient(app).get("/api/v1/maintenance/route-telemetry-triage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["source_request_count"] == 1
    assert payload["data"]["summary"]["cheap_first_action_count"] == 0


def test_model_ops_route_includes_route_telemetry_triage(tmp_path, monkeypatch):
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
    assert payload["route_telemetry_triage"]["status"] == "ready"
    assert payload["route_telemetry_triage"]["summary"]["triage_item_count"] == 1
    assert any(
        check["source_key"] == "route_telemetry_triage"
        for check in payload["model_ops_readiness"]["checks"]
    )
