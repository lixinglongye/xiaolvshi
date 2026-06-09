import json
import re

from services.model_ops_request_execution_observation_gate import (
    ModelOpsRequestExecutionObservationGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_request_execution_observation_gate_accepts_default_metadata_rows():
    gate = ModelOpsRequestExecutionObservationGateService().build_gate()
    rows = {row["request_id"]: row for row in gate["observation_rows"]}

    assert gate["id"] == "modelops-request-execution-observation-gate"
    assert gate["status"] == "ready"
    assert gate["summary"]["observation_count"] == 3
    assert gate["summary"]["ready_observation_count"] == 3
    assert gate["summary"]["matched_preflight_count"] == 3
    assert gate["summary"]["high_frequency_observation_count"] == 3
    assert gate["summary"]["cheap_first_observed_count"] == 3
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["privacy_boundary"]["raw_model_output_included"] is False
    assert gate["claim_boundary"]["request_sent_by_gate"] is False
    assert gate["source_preflight"]["id"] == "modelops-request-execution-preflight"

    assert rows["fast-default"]["preflight_match"] is True
    assert rows["fast-default"]["observed_model"] == "gemini-2.5-flash-lite"
    assert rows["embedding-default"]["observed_output_tokens"] == 0
    assert gate["blocking_check_ids"] == []
    assert gate["warning_check_ids"] == []


def test_request_execution_observation_gate_blocks_cost_over_preflight_limit():
    gate = ModelOpsRequestExecutionObservationGateService().build_gate(
        {
            "preflight": {
                "requests": [
                    {
                        "id": "fast-cost",
                        "task": "fast",
                        "model": "auto",
                        "estimated_input_tokens": 1200,
                        "estimated_output_tokens": 256,
                        "max_cost_usd": 0.01,
                    }
                ]
            },
            "observations": [
                {
                    "request_id": "fast-cost",
                    "task": "fast",
                    "resolved_model": "gemini-2.5-flash-lite",
                    "status": "success",
                    "observed_input_tokens": 1200,
                    "observed_output_tokens": 256,
                    "observed_cost_usd": 0.02,
                    "latency_ms": 900,
                }
            ],
        }
    )
    row = gate["observation_rows"][0]

    assert gate["status"] == "blocked"
    assert row["observation_status"] == "blocked"
    assert "observed_cost_over_preflight_limit" in row["reason_codes"]
    assert "observed-cost-within-preflight-limit" in gate["blocking_check_ids"]
    assert row["release_action"] == "block_observation_until_cost_metadata_is_safe"


def test_request_execution_observation_gate_blocks_high_frequency_non_cheap_model():
    gate = ModelOpsRequestExecutionObservationGateService().build_gate(
        {
            "preflight": {
                "requests": [
                    {
                        "id": "fast-premium",
                        "task": "fast",
                        "model": "auto",
                        "estimated_input_tokens": 1200,
                    }
                ]
            },
            "observations": [
                {
                    "request_id": "fast-premium",
                    "task": "fast",
                    "resolved_model": "gemini-2.5-pro",
                    "status": "success",
                    "observed_cost_usd": 0.001,
                    "latency_ms": 1000,
                }
            ],
        }
    )
    row = gate["observation_rows"][0]

    assert gate["status"] == "blocked"
    assert "high_frequency_observed_non_cheap_model" in row["reason_codes"]
    assert "observed_model_mismatch" in row["reason_codes"]
    assert "observed-cheap-first-alignment" in gate["blocking_check_ids"]


def test_request_execution_observation_gate_warns_for_fallback_and_latency():
    gate = ModelOpsRequestExecutionObservationGateService().build_gate(
        {
            "preflight": {
                "requests": [
                    {
                        "id": "review-fallback",
                        "task": "review",
                        "model": "auto",
                        "estimated_input_tokens": 3000,
                    }
                ]
            },
            "observations": [
                {
                    "request_id": "review-fallback",
                    "task": "review",
                    "resolved_model": "gemini-2.5-flash-lite",
                    "status": "success",
                    "fallback_used": True,
                    "observed_cost_usd": 0.001,
                    "latency_ms": 45000,
                }
            ],
        }
    )
    row = gate["observation_rows"][0]

    assert gate["status"] == "review_required"
    assert row["observation_status"] == "review_required"
    assert "fallback_model_used" in row["reason_codes"]
    assert "latency_over_review_limit" in row["reason_codes"]
    assert "observation-review-exceptions-visible" in gate["warning_check_ids"]


def test_request_execution_observation_gate_rejects_raw_payload_without_echoing_values():
    secret = "s" + "k-" + ("O" * 24)
    gate = ModelOpsRequestExecutionObservationGateService().build_gate(
        {
            "observations": [
                {
                    "request_id": "fast-default",
                    "task": "fast",
                    "resolved_model": "gemini-2.5-flash-lite",
                    "status": "success",
                    "observed_cost_usd": 0.0001,
                    "latency_ms": 1000,
                }
            ],
            "headers": {"authorization": f"Bearer {secret}"},
            "gateway_response": {"body": "client@example.com raw model output"},
            "prompt": "raw legal text should not be retained",
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["status"] == "blocked"
    assert gate["summary"]["forbidden_payload_field_count"] >= 3
    assert "sanitized-observation-metadata-only" in gate["blocking_check_ids"]
    assert gate["privacy_boundary"]["raw_payload_echoed"] is False
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert "raw model output" not in serialized
    assert "raw legal text should not be retained" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_request_execution_observation_gate_route_and_models_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/request-execution-observation-gate")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == "modelops-request-execution-observation-gate"
    assert response.json()["data"]["summary"]["gateway_called"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/request-execution-observation-gate",
        json={
            "observations": [
                {
                    "request_id": "unknown-row",
                    "task": "fast",
                    "resolved_model": "gemini-2.5-flash-lite",
                    "status": "success",
                    "observed_cost_usd": 0.0001,
                    "latency_ms": 1000,
                }
            ]
        },
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["request_execution_observation_gate"]["summary"]["configuration_written"] is False
    assert "request_execution_observation_gate" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
