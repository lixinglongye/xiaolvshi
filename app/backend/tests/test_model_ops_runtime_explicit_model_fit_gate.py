import json
import re

from services.model_ops_runtime_explicit_model_fit_gate import ModelOpsRuntimeExplicitModelFitGateService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_runtime_explicit_model_fit_gate_surfaces_unknown_and_explicit_exceptions():
    gate = ModelOpsRuntimeExplicitModelFitGateService().build_gate(
        {
            "observed_models": [
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.5-flash-image",
                "yibu/gemini-9.9-flash-lite",
            ]
        }
    )
    rows = {row["scenario_id"]: row for row in gate["request_rows"]}

    assert gate["status"] == "review_required"
    assert gate["summary"]["scenario_count"] >= 9
    assert gate["summary"]["unknown_gateway_passthrough_count"] == 1
    assert gate["summary"]["explicit_over_budget_allowed_count"] == 1
    assert gate["summary"]["downgraded_to_recommended_count"] >= 2
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["configuration_written"] is False
    assert rows["fast-premium-downgrade"]["runtime_fit_status"] == "enforced"
    assert rows["fast-premium-downgrade"]["resolved_model"] == "gemini-2.5-flash-lite"
    assert rows["fast-premium-explicit-allow"]["runtime_fit_status"] == "review_required"
    assert rows["fast-premium-explicit-allow"]["explicit_over_budget_allowed"] is True
    assert rows["classification-unknown-gateway"]["unknown_gateway_passthrough"] is False
    assert rows["classification-unknown-gateway"]["routed_to_recommended_model"] is True
    assert rows["classification-unknown-gateway"]["runtime_fit_status"] == "enforced"
    assert rows["classification-unknown-gateway"]["requested_model_status"] == "unknown"
    assert rows["classification-unknown-gateway"]["explicit_model_requested"] is True
    assert rows["classification-unknown-gateway"]["explicit_model_fit_status"] == "enforced"
    assert "unknown_gateway_routed_to_recommended" in rows["classification-unknown-gateway"]["reason_codes"]
    assert "unknown_gateway_routed_to_recommended" in rows["classification-unknown-gateway"]["explicit_model_fit_reason_codes"]
    assert "unknown_gateway_runtime_passthrough" not in rows["classification-unknown-gateway"]["reason_codes"]
    assert rows["classification-unknown-gateway-explicit-allow"]["unknown_gateway_passthrough"] is True
    assert rows["classification-unknown-gateway-explicit-allow"]["runtime_fit_status"] == "review_required"
    assert rows["classification-unknown-gateway-explicit-allow"]["explicit_model_fit_status"] == "allowed_review_exception"
    assert "explicit_gateway_passthrough_allowed" in rows["classification-unknown-gateway-explicit-allow"]["reason_codes"]
    assert "unknown_gateway_runtime_passthrough" in rows["classification-unknown-gateway-explicit-allow"]["reason_codes"]
    assert "unknown-gateway-passthrough-visible" in gate["warning_check_ids"]
    assert gate["privacy_boundary"]["request_body_included"] is False
    assert gate["claim_boundary"]["runtime_behavior_changed"] is True


def test_runtime_explicit_model_fit_gate_custom_safe_scenarios_can_be_ready():
    observed_matrix = {
        "task_fit_rows": [
            {"task": "fast", "gateway_fit_status": "cheap_fit", "cheapest_gateway_model": "gemini-2.5-flash-lite"},
            {"task": "review", "gateway_fit_status": "balanced_fit", "cheapest_gateway_model": "gemini-2.5-flash"},
        ]
    }
    gate = ModelOpsRuntimeExplicitModelFitGateService().build_gate(
        {
            "observed_gateway_model_fit_matrix": observed_matrix,
            "request_scenarios": [
                {"id": "fast-default", "task": "fast", "model": "auto"},
                {"id": "review-default", "task": "review", "model": "auto"},
            ],
        }
    )

    assert gate["status"] == "ready"
    assert gate["summary"]["ready_row_count"] == 2
    assert gate["summary"]["review_row_count"] == 0
    assert gate["warning_check_ids"] == []
    assert all(row["observed_fit_status"] in {"cheap_fit", "balanced_fit"} for row in gate["request_rows"])


def test_runtime_explicit_model_fit_gate_reviews_high_frequency_noncheap_explicit_allow():
    gate = ModelOpsRuntimeExplicitModelFitGateService().build_gate(
        {
            "observed_gateway_model_fit_matrix": {"task_fit_rows": []},
            "request_scenarios": [
                {
                    "id": "fast-pro-explicit",
                    "task": "fast",
                    "model": "gemini-2.5-pro",
                    "allow_over_budget_model": True,
                }
            ],
        }
    )
    row = gate["request_rows"][0]

    assert gate["status"] == "review_required"
    assert row["runtime_fit_status"] == "review_required"
    assert "high_frequency_not_cheap_first_aligned" in row["reason_codes"]
    assert "high-frequency-cheap-first-enforced" in gate["warning_check_ids"]


def test_runtime_explicit_model_fit_gate_rejects_raw_payload_fields_without_echoing_values():
    secret = "s" + "k-" + ("R" * 24)
    gate = ModelOpsRuntimeExplicitModelFitGateService().build_gate(
        {
            "request_scenarios": [{"id": "fast", "task": "fast", "model": "gemini-2.5-flash-lite"}],
            "headers": {"authorization": f"Bearer {secret}"},
            "messages": [{"role": "user", "content": "client@example.com raw legal text"}],
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["status"] == "blocked"
    assert gate["summary"]["forbidden_payload_field_count"] >= 2
    assert "sanitized-runtime-scenarios-only" in gate["blocking_check_ids"]
    assert gate["privacy_boundary"]["raw_payload_echoed"] is False
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert "raw legal text" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_runtime_explicit_model_fit_gate_route_and_models_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/runtime-explicit-model-fit-gate")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["status"] == "review_required"
    assert route_payload["data"]["summary"]["forbidden_payload_field_count"] == 0
    assert route_payload["data"]["summary"]["gateway_called"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/runtime-explicit-model-fit-gate",
        json={"request_scenarios": [{"task": "fast", "model": "gemini-2.5-pro", "allow_over_budget_model": True}]},
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "review_required"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["runtime_explicit_model_fit_gate"]["summary"]["configuration_written"] is False
    assert "runtime_explicit_model_fit_gate" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
