import re

from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService
from services.route_telemetry_remediation_plan import RouteTelemetryRemediationPlanService
from services.route_telemetry_repository import RouteTelemetryRepositoryService
from services.route_telemetry_result_archive import RouteTelemetryResultArchiveService
from services.route_telemetry_triage_queue import RouteTelemetryTriageQueueService


SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{12,}|client@example\.com|UNSAFE_PROMPT|UNSAFE_OUTPUT)",
    re.IGNORECASE,
)


def _event(
    event_id: str,
    *,
    day: str = "2026-06-04",
    model: str = "gemini-2.5-flash-lite",
    success: bool = True,
    over_budget: bool = False,
    estimated_cost_usd: float = 0.0012,
) -> dict:
    if model == "gateway/custom-unknown":
        reason_codes = ["unknown_catalog_model", "unverified_price_tier", "gateway_passthrough"]
    elif over_budget:
        reason_codes = [
            "known_catalog_model",
            "over_task_budget",
            "operator_review_required",
            "routed_to_recommended_model",
        ]
    else:
        reason_codes = ["known_catalog_model", "within_task_budget"]
    return {
        "event_id": event_id,
        "event_type": "model_route_decision",
        "timestamp": f"{day}T08:00:00Z",
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
        "estimated_cost_usd": estimated_cost_usd,
        "latency_ms": 860,
        "success": success,
        "stream": False,
        "cache_hit": False,
        "http_status": 200 if success else 500,
        "reason_codes": reason_codes,
    }


def _archive_from_repository(repository: dict) -> dict:
    ops = RouteTelemetryOpsSummaryService().build_summary(repository)
    triage = RouteTelemetryTriageQueueService().build_queue(ops)
    remediation = RouteTelemetryRemediationPlanService().build_plan(triage)
    return RouteTelemetryResultArchiveService().build_archive(
        {
            "route_telemetry_repository": repository,
            "route_telemetry_ops_summary": ops,
            "route_telemetry_triage": triage,
            "route_telemetry_remediation": remediation,
        }
    )


def test_route_telemetry_result_archive_is_ready_with_empty_repository(tmp_path):
    repository = RouteTelemetryRepositoryService(tmp_path).build_repository()

    result = _archive_from_repository(repository)

    assert result["id"] == "route-telemetry-result-archive"
    assert result["status"] == "ready"
    assert result["summary"]["empty_repository"] is True
    assert result["summary"]["archive_day_count"] == 0
    assert result["summary"]["cost_ledger_row_count"] == 0
    assert result["summary"]["configuration_written"] is False
    assert result["summary"]["model_calls"] == "not_required"
    assert result["privacy_boundary"]["metadata_only"] is True
    assert result["privacy_boundary"]["returns_raw_prompts"] is False
    assert result["source_boundaries"]["changes_default_routes"] is False
    assert "Collect sanitized staging route events" in result["recommended_actions"][0]
    assert not SECRET_PATTERN.search(str(result))


def test_route_telemetry_result_archive_builds_daily_archive_and_cost_ledger(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events(
        [
            *[_event(f"route-event-04-{index:03d}", day="2026-06-04") for index in range(19)],
            *[_event(f"route-event-05-{index:03d}", day="2026-06-05") for index in range(19)],
            _event("route-event-05-019", day="2026-06-05", over_budget=True, estimated_cost_usd=0.002),
        ]
    )

    result = _archive_from_repository(repository)

    assert result["status"] == "pass"
    assert result["summary"]["request_count"] == 39
    assert result["summary"]["archive_day_count"] == 2
    assert result["summary"]["cost_ledger_row_count"] == 1
    assert result["summary"]["estimated_cost_usd_sum"] == 0.0476
    assert result["archive_rows"][0]["day"] == "2026-06-04"
    assert result["archive_rows"][0]["request_count"] == 19
    assert result["archive_rows"][1]["archive_status"] == "cheap_first_review"
    assert result["cost_ledger_rows"][0]["resolved_model"] == "gemini-2.5-flash-lite"
    assert result["cost_ledger_rows"][0]["request_count"] == 39
    assert result["cost_ledger_rows"][0]["downgrade_count"] == 1
    assert result["cost_ledger_rows"][0]["cost_ledger_status"] == "review_required"
    assert result["blocking_check_ids"] == []
    assert not SECRET_PATTERN.search(str(result))


def test_route_telemetry_result_archive_flags_unknown_and_premium_drift(tmp_path):
    repository_service = RouteTelemetryRepositoryService(tmp_path)
    repository = repository_service.append_events(
        [
            _event("route-event-001", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-002", model="gemini-2.5-pro", success=False, over_budget=True),
            _event("route-event-003", model="gateway/custom-unknown"),
        ]
    )

    result = _archive_from_repository(repository)

    assert result["status"] == "fail"
    assert result["summary"]["blocking_item_count"] > 0
    assert result["summary"]["manual_review_step_count"] > 0
    assert "failure-rate" in result["blocking_check_ids"]
    assert any(row["cost_ledger_status"] == "unknown_model_review" for row in result["cost_ledger_rows"])
    assert any(row["requires_operator_review"] for row in result["release_review_rows"])
    assert result["privacy_boundary"]["returns_raw_model_output"] is False
    assert result["claim_boundary"]["claims_production_health"] is False


def test_route_telemetry_result_archive_routes_are_available(tmp_path, monkeypatch):
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from services import route_telemetry_repository
    from routers.aihub import _clear_model_ops_payload_cache, router as aihub_router
    from routers.maintenance import router as maintenance_router

    _clear_model_ops_payload_cache()
    monkeypatch.setattr(route_telemetry_repository.settings, "local_storage_dir", str(tmp_path))
    repository_service = RouteTelemetryRepositoryService(tmp_path / "model_ops" / "route_telemetry")
    repository_service.append_events([_event("route-event-001")])

    app = fastapi.FastAPI()
    app.include_router(maintenance_router)
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    maintenance_response = client.get("/api/v1/maintenance/route-telemetry-result-archive")
    assert maintenance_response.status_code == 200
    maintenance_payload = maintenance_response.json()
    assert maintenance_payload["success"] is True
    assert maintenance_payload["data"]["summary"]["request_count"] == 1

    aihub_response = client.get("/api/v1/aihub/models/route-telemetry-result-archive")
    assert aihub_response.status_code == 200
    aihub_payload = aihub_response.json()
    assert aihub_payload["success"] is True
    assert aihub_payload["data"]["id"] == "route-telemetry-result-archive"
    assert aihub_payload["data"]["summary"]["request_count"] == 1
    assert aihub_payload["data"]["source_boundaries"]["calls_newapi"] is False
    _clear_model_ops_payload_cache()


def test_model_ops_route_includes_route_telemetry_result_archive(tmp_path, monkeypatch):
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from services import route_telemetry_repository
    from routers.aihub import _clear_model_ops_payload_cache, router

    _clear_model_ops_payload_cache()
    monkeypatch.setattr(route_telemetry_repository.settings, "local_storage_dir", str(tmp_path))
    app = fastapi.FastAPI()
    app.include_router(router)
    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["route_telemetry_result_archive"]["id"] == "route-telemetry-result-archive"
    assert payload["route_telemetry_result_archive"]["summary"]["model_calls"] == "not_required"
    assert any(
        check["source_key"] == "route_telemetry_result_archive"
        for check in payload["model_ops_readiness"]["checks"]
    )
    _clear_model_ops_payload_cache()
