import json
import re

from services.model_catalog import estimate_token_cost_usd
from services.model_runtime_router import resolve_runtime_model
from services.model_task_inference import TaskInference
from services.route_telemetry_repository import RouteTelemetryRepositoryService


SECRET_PATTERN = re.compile(r"s[k]-[A-Za-z0-9_-]{12,}|[^@\s]+@[^@\s]+\.[^@\s]+", re.IGNORECASE)


def _event(event_id: str = "route-event-001") -> dict:
    return {
        "event_id": event_id,
        "event_type": "model_route_decision",
        "timestamp": "2026-06-04T08:00:00Z",
        "route_id": "cheap-first-fast",
        "task": "fast",
        "inference_source": "explicit",
        "requested_model": "gemini-2.5-pro",
        "resolved_model": "gemini-2.5-flash-lite",
        "gateway": "newapi",
        "provider": "google",
        "routed_to_recommended_model": True,
        "is_over_budget": True,
        "requires_operator_review": False,
        "allow_over_budget_model": False,
        "is_known_model": True,
        "estimated_input_tokens": 1200,
        "estimated_output_tokens": 500,
        "estimated_cost_usd": 0.0012,
        "latency_ms": 860,
        "success": True,
        "error_category": "",
        "stream": False,
        "cache_hit": False,
        "http_status": 200,
    }


def test_route_telemetry_repository_starts_empty(tmp_path):
    result = RouteTelemetryRepositoryService(tmp_path).build_repository()

    assert result["status"] == "ready"
    assert result["summary"]["stored_event_count"] == 0
    assert result["summary"]["raw_payload_storage_allowed"] is False
    assert result["totals"]["request_count"] == 0
    assert result["totals"]["unknown_model_count"] == 0
    assert result["totals"]["unpriced_model_count"] == 0
    assert not SECRET_PATTERN.search(str(result))


def test_route_telemetry_repository_persists_sanitized_events_and_aggregates(tmp_path):
    service = RouteTelemetryRepositoryService(tmp_path)
    result = service.append_events([_event(), {**_event("route-event-002"), "success": False, "estimated_cost_usd": 0.002}])

    assert result["status"] == "pass"
    assert result["summary"]["accepted_event_count"] == 2
    assert result["summary"]["stored_event_count"] == 2
    assert result["totals"]["request_count"] == 2
    assert result["totals"]["success_count"] == 1
    assert result["totals"]["failure_count"] == 1
    assert result["totals"]["downgrade_count"] == 2
    assert result["totals"]["estimated_cost_usd_sum"] == 0.0032
    assert len(result["daily_buckets"]) == 2
    assert service.events_path.exists()
    assert service.aggregates_path.exists()

    stored_lines = [json.loads(line) for line in service.events_path.read_text(encoding="utf-8").splitlines()]
    assert stored_lines[0]["day"] == "2026-06-04"
    assert stored_lines[0]["resolved_model"] == "gemini-2.5-flash-lite"
    assert "raw_prompt" not in str(stored_lines)


def test_route_telemetry_repository_estimates_catalog_route_costs(tmp_path):
    service = RouteTelemetryRepositoryService(tmp_path)
    route = resolve_runtime_model("gemini-2.5-pro", task="fast")
    expected_cost = estimate_token_cost_usd("gemini-2.5-flash-lite", 1000, 1000)
    result = service.append_route_decision(
        route=route,
        task_inference=TaskInference(
            requested_task="fast",
            task="fast",
            source="explicit",
            confidence=1.0,
            signals=("requested:fast",),
            reason="test",
        ),
        success=True,
        usage={"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000},
        latency_ms=50,
    )

    assert result["status"] == "pass"
    assert result["summary"]["accepted_event_count"] == 1
    assert result["accepted_events"][0]["resolved_model"] == "gemini-2.5-flash-lite"
    assert result["accepted_events"][0]["estimated_input_tokens"] == 1000
    assert result["accepted_events"][0]["estimated_output_tokens"] == 1000
    assert result["accepted_events"][0]["estimated_cost_usd"] == expected_cost
    assert result["totals"]["estimated_cost_usd_sum"] == expected_cost
    assert result["daily_buckets"][0]["estimated_cost_usd_sum"] == expected_cost


def test_route_telemetry_repository_estimates_prefixed_catalog_route_costs(tmp_path):
    service = RouteTelemetryRepositoryService(tmp_path)
    route = resolve_runtime_model("google/gemini-2.5-flash", task="review")
    expected_cost = estimate_token_cost_usd("gemini-2.5-flash", 1000, 1000)
    result = service.append_route_decision(
        route=route,
        task_inference=TaskInference(
            requested_task="review",
            task="review",
            source="explicit",
            confidence=1.0,
            signals=("requested:review",),
            reason="test",
        ),
        success=True,
        usage={"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000},
        latency_ms=50,
    )

    assert result["status"] == "pass"
    assert result["accepted_events"][0]["resolved_model"] == "google/gemini-2.5-flash"
    assert result["accepted_events"][0]["is_known_model"] is True
    assert result["accepted_events"][0]["estimated_cost_usd"] == expected_cost
    assert result["totals"]["estimated_cost_usd_sum"] == expected_cost
    assert result["totals"]["unpriced_model_count"] == 0


def test_route_telemetry_repository_keeps_unknown_gateway_route_unpriced(tmp_path):
    service = RouteTelemetryRepositoryService(tmp_path)
    route = resolve_runtime_model("gateway/custom-unknown", task="fast")
    result = service.append_route_decision(
        route=route,
        task_inference=TaskInference(
            requested_task="fast",
            task="fast",
            source="explicit",
            confidence=1.0,
            signals=("requested:fast",),
            reason="test",
        ),
        success=True,
        usage={"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000},
        latency_ms=50,
    )

    assert result["status"] == "pass"
    assert result["accepted_events"][0]["is_known_model"] is False
    assert result["accepted_events"][0]["estimated_cost_usd"] == 0.0
    assert result["totals"]["estimated_cost_usd_sum"] == 0.0
    assert result["totals"]["unknown_model_count"] == 1
    assert result["totals"]["unpriced_model_count"] == 0


def test_route_telemetry_repository_counts_known_catalog_models_without_token_prices(tmp_path):
    service = RouteTelemetryRepositoryService(tmp_path)
    route = resolve_runtime_model("gemini-3-pro-image", task="image")
    result = service.append_route_decision(
        route=route,
        task_inference=TaskInference(
            requested_task="image",
            task="image",
            source="explicit",
            confidence=1.0,
            signals=("requested:image",),
            reason="test",
        ),
        success=True,
        usage={"prompt_tokens": 1000, "completion_tokens": 1000, "total_tokens": 2000},
        latency_ms=50,
    )

    assert result["status"] == "pass"
    assert result["accepted_events"][0]["is_known_model"] is True
    assert result["accepted_events"][0]["estimated_cost_usd"] == 0.0
    assert result["totals"]["unknown_model_count"] == 0
    assert result["totals"]["unpriced_model_count"] == 1
    assert result["daily_buckets"][0]["unpriced_model_count"] == 1


def test_route_telemetry_repository_rejects_sensitive_events_without_echoing_values(tmp_path):
    secret_value = "s" + "k-" + ("C" * 24)
    client_email = "client" + "@example.com"
    raw_prompt = "UNSAFE_PROMPT_SHOULD_NOT_APPEAR"
    event = _event()
    event.update(
        {
            "api_key": secret_value,
            "client_email": client_email,
            "raw_prompt": raw_prompt,
            "metadata": {"raw_model_output": "UNSAFE_OUTPUT_SHOULD_NOT_APPEAR"},
        }
    )

    result = RouteTelemetryRepositoryService(tmp_path).append_events([event])
    rendered = str(result)

    assert result["status"] == "fail"
    assert result["summary"]["accepted_event_count"] == 0
    assert result["summary"]["rejected_event_count"] == 1
    assert result["summary"]["stored_event_count"] == 0
    assert result["rejected_events"][0]["reason_codes"] == ["forbidden_fields_present", "sensitive_values_present"]
    assert secret_value not in rendered
    assert client_email not in rendered
    assert raw_prompt not in rendered
    assert "UNSAFE_OUTPUT_SHOULD_NOT_APPEAR" not in rendered
    assert not SECRET_PATTERN.search(rendered)


def test_route_telemetry_repository_rejects_duplicate_event_ids(tmp_path):
    service = RouteTelemetryRepositoryService(tmp_path)
    first = service.append_events([_event()])
    second = service.append_events([_event()])

    assert first["summary"]["stored_event_count"] == 1
    assert second["status"] == "warn"
    assert second["summary"]["accepted_event_count"] == 0
    assert second["summary"]["stored_event_count"] == 1
    assert second["rejected_events"][0]["status"] == "duplicate"


def test_route_telemetry_repository_warns_but_persists_missing_recommended_fields(tmp_path):
    event = _event()
    event.pop("route_id")
    event.pop("requested_model")

    result = RouteTelemetryRepositoryService(tmp_path).append_events([event])

    assert result["status"] == "warn"
    assert result["summary"]["accepted_event_count"] == 1
    assert result["summary"]["stored_event_count"] == 1
    assert result["persistence_plan_status"] == "warn"


def test_route_telemetry_repository_routes_return_snapshot_and_append(tmp_path, monkeypatch):
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from services import route_telemetry_repository
    from routers.maintenance import router

    monkeypatch.setattr(route_telemetry_repository.settings, "local_storage_dir", str(tmp_path))
    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/route-telemetry-repository")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["summary"]["stored_event_count"] == 0

    post_response = client.post("/api/v1/maintenance/route-telemetry-repository", json=[_event()])
    assert post_response.status_code == 200
    payload = post_response.json()["data"]
    assert payload["summary"]["stored_event_count"] == 1
    assert payload["totals"]["request_count"] == 1
