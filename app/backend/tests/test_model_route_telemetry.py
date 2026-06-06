from services.model_route_telemetry import ModelRouteTelemetryRegistry, model_route_telemetry_registry
from services.model_runtime_router import resolve_runtime_model
from services.model_task_inference import infer_gentxt_task
from schemas.aihub import ChatMessage


def test_route_telemetry_records_auto_inference_and_downgrades():
    registry = ModelRouteTelemetryRegistry()
    task_inference = infer_gentxt_task(
        "auto",
        [ChatMessage(role="user", content="Review this contract for liability risk.")],
    )
    route = resolve_runtime_model("gemini-2.5-pro", task=task_inference.task)

    registry.record(route=route, task_inference=task_inference, success=True)
    snapshot = registry.snapshot()

    assert snapshot["status"] == "ready"
    assert snapshot["summary"]["request_count"] == 1
    assert snapshot["summary"]["auto_inferred_ratio"] == 1.0
    assert snapshot["summary"]["downgrade_ratio"] == 1.0
    assert snapshot["summary"]["operator_review_request_count"] == 1
    assert snapshot["by_task"]["review"]["models"] == {"gemini-2.5-flash": 1}
    assert "sk-" not in str(snapshot)


def test_route_telemetry_records_explicit_task_without_downgrade():
    registry = ModelRouteTelemetryRegistry()
    task_inference = infer_gentxt_task(
        "classification",
        [ChatMessage(role="user", content="Classify this file.")],
    )
    route = resolve_runtime_model(None, task=task_inference.task)

    registry.record(route=route, task_inference=task_inference, success=False, stream=True)
    snapshot = registry.snapshot()

    assert snapshot["summary"]["request_count"] == 1
    assert snapshot["summary"]["failure_rate"] == 1.0
    assert snapshot["totals"]["explicit_task"] == 1
    assert snapshot["totals"]["stream_requests"] == 1
    assert snapshot["by_inference_source"]["explicit"]["failures"] == 1


def test_model_ops_route_includes_route_telemetry():
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
    assert payload["route_telemetry"]["status"] == "ready"
    assert payload["route_telemetry"]["summary"]["request_count"] == 0
    assert payload["route_telemetry_repository"]["status"] == "ready"
    assert payload["route_telemetry_repository"]["summary"]["raw_payload_storage_allowed"] is False


def test_route_telemetry_version_changes_on_record_and_reset():
    registry = ModelRouteTelemetryRegistry()
    initial_version = registry.version
    task_inference = infer_gentxt_task(
        "fast",
        [ChatMessage(role="user", content="Summarize this note.")],
    )
    route = resolve_runtime_model(None, task=task_inference.task)

    registry.record(route=route, task_inference=task_inference, success=True)
    recorded_version = registry.version
    registry.reset()

    assert recorded_version == initial_version + 1
    assert registry.version == recorded_version + 1
    assert registry.snapshot()["version"] == registry.version
