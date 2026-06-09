import pytest

from services import model_gateway_health_plan, model_gateway_probe_runbook_gate
from services.model_gateway_probe_evaluation import (
    ModelGatewayProbeEvaluationService,
    model_gateway_probe_evaluation_registry,
)
from services.model_gateway_probe_runbook_gate import ModelGatewayProbeRunbookGateService


@pytest.fixture(autouse=True)
def clear_probe_registry():
    model_gateway_probe_evaluation_registry.clear()
    yield
    model_gateway_probe_evaluation_registry.clear()


def _passing_probe():
    return ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {
                "data": [
                    {"id": "gemini-2.5-flash-lite"},
                    {"id": "gemini-2.5-flash"},
                    {"id": "gemini-3.1-flash-lite"},
                    {"id": "gemini-2.5-flash-image"},
                ]
            },
            "chat_probe_results": {
                "gemini-2.5-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 900},
                "gemini-2.5-flash": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 1200},
                "gemini-3.1-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 1000},
            },
            "image_probe_results": {
                "gemini-2.5-flash-image": {"status": "pass", "http_status": 200, "image_count": 1, "latency_ms": 2400}
            },
        }
    )


def test_probe_runbook_gate_passes_after_sanitized_probe_evidence(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured-locally")

    gate = ModelGatewayProbeRunbookGateService().build_gate({"gateway_probe_evaluation": _passing_probe()})

    assert gate["status"] == "pass"
    assert gate["summary"]["ready_step_count"] == gate["summary"]["step_count"]
    assert gate["summary"]["cheap_probe_pass_count"] >= 1
    assert gate["summary"]["image_probe_pass_count"] == 1
    assert gate["summary"]["configuration_written"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["default_model_changed"] is False
    assert gate["privacy_boundary"]["credentials_included"] is False
    assert gate["privacy_boundary"]["raw_probe_payload_included"] is False
    assert gate["claim_boundary"]["actual_key_validated"] is False
    assert all(step["status"] == "ready" for step in gate["runbook_steps"])
    assert "configured-locally" not in str(gate)


def test_probe_runbook_gate_warns_until_list_models_and_cheap_probe_are_submitted(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured-locally")

    gate = ModelGatewayProbeRunbookGateService().build_gate()

    assert gate["status"] == "warn"
    assert "runbook-review-steps-visible" in gate["warning_check_ids"]
    step_status = {step["id"]: step["status"] for step in gate["runbook_steps"]}
    assert step_status["normalize-runtime-channel"] == "ready"
    assert step_status["verify-secret-boundary"] == "ready"
    assert step_status["list-models-first"] == "review_required"
    assert step_status["cheap-json-probe"] == "review_required"
    assert step_status["legal-fixture-smoke"] == "review_required"
    assert gate["summary"]["next_step_id"] == "list-models-first"


def test_probe_runbook_gate_blocks_rejected_probe_payload_without_echoing_secret(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured-locally")
    secret_value = "s" + "k-" + ("A" * 24)
    rejected_probe = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {"data": [{"id": "gemini-2.5-flash-lite"}]},
            "chat_probe_results": {
                "gemini-2.5-flash-lite": {
                    "status": "pass",
                    "http_status": 200,
                    "json_ok": True,
                    "trace_id": secret_value,
                }
            },
        }
    )

    gate = ModelGatewayProbeRunbookGateService().build_gate({"gateway_probe_evaluation": rejected_probe})

    assert gate["status"] == "fail"
    assert "runbook-no-sensitive-probe-fields" in gate["blocking_check_ids"]
    step_status = {step["id"]: step["status"] for step in gate["runbook_steps"]}
    assert step_status["cheap-json-probe"] == "blocked"
    assert step_status["legal-fixture-smoke"] == "blocked"
    assert gate["summary"]["forbidden_payload_field_count"] == 1
    assert secret_value not in str(gate)


def test_probe_runbook_gate_blocks_insecure_remote_gateway(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "http://example.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured-locally")

    gate = ModelGatewayProbeRunbookGateService().build_gate({"gateway_probe_evaluation": _passing_probe()})

    assert gate["status"] == "fail"
    assert "runbook-no-blocked-steps" in gate["blocking_check_ids"]
    step_status = {step["id"]: step["status"] for step in gate["runbook_steps"]}
    assert step_status["verify-secret-boundary"] == "blocked"
    assert step_status["list-models-first"] == "blocked"


def test_probe_runbook_gate_route_and_model_ops_payload_include_gate(monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured-locally")
    model_gateway_probe_evaluation_registry.record(_passing_probe())

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gateway-probe-runbook-gate")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "pass"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["gateway_probe_runbook_gate"]["status"] == "pass"
    readiness_check = next(
        check for check in payload["model_ops_readiness"]["checks"] if check["id"] == "gateway-probe-runbook-gate"
    )
    assert readiness_check["status"] == "pass"
