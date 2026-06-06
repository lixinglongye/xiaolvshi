import json
import re

from services.model_gateway_request_compatibility_gate import ModelGatewayRequestCompatibilityGateService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_gateway_request_compatibility_gate_covers_cheap_first_defaults():
    gate = ModelGatewayRequestCompatibilityGateService().build_gate()
    rows = {row["task"]: row for row in gate["task_rows"]}

    assert gate["status"] == "ready"
    assert gate["summary"]["task_count"] >= 7
    assert gate["summary"]["cheap_first_task_count"] == 3
    assert gate["summary"]["cheap_first_ready_count"] == 3
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["configuration_written"] is False
    assert rows["fast"]["model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["gateway_request_shape"]["max_tokens"] <= 4096
    assert rows["fast"]["gateway_request_shape"]["reasoning_effort"] in {"none", "minimal", "low"}
    assert rows["classification"]["gateway_request_shape"]["response_format_mode"] == "json"
    assert rows["classification"]["gateway_request_shape"]["temperature"] == 0.0
    assert rows["review"]["gateway_request_shape"]["reasoning_effort"] == "low"
    assert rows["pdf"]["compatibility_status"] == "ready"
    assert gate["privacy_boundary"]["request_body_included"] is False
    assert gate["claim_boundary"]["live_gateway_execution_claimed"] is False


def test_gateway_request_compatibility_gate_blocks_unsafe_high_frequency_override():
    gate = ModelGatewayRequestCompatibilityGateService().build_gate(
        {
            "tasks": [
                {
                    "task": "fast",
                    "model": "gemini-2.5-pro",
                    "temperature": 1.4,
                    "max_tokens": 12000,
                    "response_format": {"type": "json_object"},
                    "reasoning_effort": "high",
                }
            ]
        }
    )
    row = gate["task_rows"][0]

    assert gate["status"] == "blocked"
    assert row["compatibility_status"] == "blocked"
    assert "model-cost-tier-over-task-bound" in row["reason_codes"]
    assert row["gateway_request_shape"]["temperature"] == 0.2
    assert row["gateway_request_shape"]["max_tokens"] == 4096
    assert row["gateway_request_shape"]["request_body_returned"] is False
    assert "block_high_frequency_default_promotion" == row["release_action"]


def test_gateway_request_compatibility_gate_blocks_unknown_gateway_models():
    gate = ModelGatewayRequestCompatibilityGateService().build_gate(
        {"tasks": [{"task": "classification", "model": "yibu/gemini-9.9-flash-lite"}]}
    )
    row = gate["task_rows"][0]

    assert gate["status"] == "blocked"
    assert row["known_catalog_model"] is False
    assert row["gateway_prefixed_model"] is False
    assert "unknown-catalog-model" in row["reason_codes"]
    assert row["gateway_request_shape"]["messages"] == "redacted_placeholders_only"


def test_gateway_request_compatibility_gate_rejects_raw_payload_fields_without_echoing_values():
    secret = "s" + "k-" + ("Q" * 24)
    gate = ModelGatewayRequestCompatibilityGateService().build_gate(
        {
            "tasks": [{"task": "fast", "model": "gemini-2.5-flash-lite"}],
            "headers": {"authorization": f"Bearer {secret}"},
            "messages": [{"role": "user", "content": "client@example.com raw legal text"}],
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["status"] == "blocked"
    assert gate["summary"]["forbidden_payload_field_count"] >= 2
    assert "sanitized-request-shape-only" in gate["blocking_check_ids"]
    assert gate["privacy_boundary"]["raw_payload_echoed"] is False
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert "raw legal text" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gateway_request_compatibility_gate_route_and_models_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gateway-request-compatibility-gate")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["gateway_called"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/gateway-request-compatibility-gate",
        json={"tasks": [{"task": "fast", "model": "gemini-2.5-pro"}]},
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["gateway_request_compatibility_gate"]["summary"]["configuration_written"] is False
    assert "gateway_request_compatibility_gate" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
