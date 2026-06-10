import json
import re

from services.modelops_legal_benchmark_default_promotion_observation_gate import (
    ModelOpsLegalBenchmarkDefaultPromotionObservationGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def _execution_handoff(
    *,
    status: str = "ready",
    execution_status: str = "ready_for_external_execution",
    post_change_observation_status: str = "not_observed",
    route_telemetry_status: str = "not_attached",
    legal_benchmark_smoke_status: str = "not_attached",
    rollback_window_status: str = "not_opened",
    incident_status: str = "not_attached",
    blocking_ids: list[str] | None = None,
    model_id: str = "gemini-2.5-flash-lite",
) -> dict:
    blocking_ids = blocking_ids or []
    return {
        "id": "modelops-legal-benchmark-default-promotion-execution-handoff",
        "title": "ModelOps legal benchmark default-promotion execution handoff",
        "status": status,
        "summary": {
            "source_count": 1,
            "handoff_row_count": 1,
            "ready_for_external_execution_count": 1 if execution_status == "ready_for_external_execution" else 0,
            "awaiting_external_signoff_count": 0,
            "blocked_count": 1 if blocking_ids or status == "blocked" else 0,
            "not_run_count": 0,
            "configuration_written": False,
            "env_file_written": False,
            "approval_record_written": False,
            "signoff_record_written": False,
            "rollback_executed": False,
            "gateway_called": False,
            "network_called": False,
            "raw_payload_echoed": False,
            "raw_model_output_returned": False,
        },
        "handoff_rows": [
            {
                "id": "legal-benchmark-default-promotion-execution-handoff-1",
                "source_signoff_item_id": "legal-benchmark-default-promotion-signoff-1",
                "requirement_id": "legal-fixture-promotion-contract-review",
                "fixture_id": "contract-risk-review-basic",
                "task": "legal_review",
                "proposed_default_model": model_id,
                "model_cost_tier": "lowest",
                "execution_status": execution_status,
                "post_change_observation_status": post_change_observation_status,
                "route_telemetry_status": route_telemetry_status,
                "legal_benchmark_smoke_status": legal_benchmark_smoke_status,
                "rollback_window_status": rollback_window_status,
                "incident_status": incident_status,
                "reason_codes": ["external-execution-ready"],
            }
        ],
        "blocking_check_ids": blocking_ids,
        "warning_check_ids": [],
    }


def test_default_promotion_observation_gate_ready_when_external_observation_is_attached():
    gate = ModelOpsLegalBenchmarkDefaultPromotionObservationGateService().build_gate(
        {
            "legal_benchmark_default_promotion_execution_handoff": _execution_handoff(
                post_change_observation_status="observed",
                route_telemetry_status="ready",
                legal_benchmark_smoke_status="pass",
                rollback_window_status="clear",
                incident_status="none",
            )
        }
    )
    row = gate["observation_rows"][0]
    rollback_row = gate["rollback_window_rows"][0]
    checks = {check["id"]: check for check in gate["checks"]}

    assert gate["id"] == "modelops-legal-benchmark-default-promotion-observation-gate"
    assert gate["status"] == "ready"
    assert gate["decision"]["observation_gate_ready"] is True
    assert gate["decision"]["default_change_allowed_by_observation_gate"] is False
    assert gate["decision"]["rollback_execution_allowed"] is False
    assert gate["summary"]["observation_ready_count"] == 1
    assert gate["summary"]["rollback_window_clear_count"] == 1
    assert gate["summary"]["configuration_written"] is False
    assert gate["summary"]["rollback_executed"] is False
    assert gate["summary"]["traffic_shifted"] is False
    assert row["observation_gate_status"] == "observation_ready"
    assert row["default_change_allowed_by_observation_gate"] is False
    assert "confirm-legal-benchmark-smoke-pass" in row["observation_checks"]
    assert rollback_row["rollback_window_status"] == "clear"
    assert rollback_row["rollback_executed"] is False
    assert checks["default-promotion-execution-handoff-attached-not-blocked"]["status"] == "pass"
    assert checks["post-change-observation-attached"]["status"] == "pass"
    assert checks["rollback-window-clear"]["status"] == "pass"


def test_default_promotion_observation_gate_blocks_when_execution_handoff_blocks():
    gate = ModelOpsLegalBenchmarkDefaultPromotionObservationGateService().build_gate(
        {
            "legal_benchmark_default_promotion_execution_handoff": _execution_handoff(
                status="blocked",
                execution_status="blocked",
                blocking_ids=["default-promotion-signoff-packet-attached-not-blocked"],
            )
        }
    )

    assert gate["status"] == "blocked"
    assert "default-promotion-execution-handoff-attached-not-blocked" in gate["blocking_check_ids"]
    assert gate["observation_rows"][0]["observation_gate_status"] == "blocked"
    assert gate["decision"]["release_action"] == "block_or_rollback_external_default_promotion"


def test_default_promotion_observation_gate_requires_rollback_window_clear():
    gate = ModelOpsLegalBenchmarkDefaultPromotionObservationGateService().build_gate(
        {
            "legal_benchmark_default_promotion_execution_handoff": _execution_handoff(
                post_change_observation_status="observed",
                route_telemetry_status="ready",
                legal_benchmark_smoke_status="pass",
                rollback_window_status="not_clear",
                incident_status="none",
            )
        }
    )
    checks = {check["id"]: check for check in gate["checks"]}

    assert gate["status"] == "review_required"
    assert gate["summary"]["review_required_count"] == 1
    assert gate["summary"]["rollback_window_clear_count"] == 0
    assert gate["observation_rows"][0]["observation_gate_status"] == "review_required"
    assert "rollback-window-not-clear" in gate["observation_rows"][0]["reason_codes"]
    assert checks["rollback-window-clear"]["status"] == "warn"
    assert gate["summary"]["traffic_shifted"] is False


def test_default_promotion_observation_gate_redacts_sensitive_values():
    payload = {
        "legal_benchmark_default_promotion_execution_handoff": _execution_handoff(model_id="sk-" + ("e" * 24)),
        "api_key": "sk-" + ("f" * 24),
        "raw_output": "RAW_PRIVATE_OBSERVATION_SHOULD_NOT_LEAK",
        "prompt": "PRIVATE_OBSERVATION_PROMPT_SHOULD_NOT_LEAK",
    }

    gate = ModelOpsLegalBenchmarkDefaultPromotionObservationGateService().build_gate(payload)
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["summary"]["raw_input_field_count"] >= 3
    assert gate["summary"]["network_called"] is False
    assert gate["claim_boundary"]["live_gateway_execution_claimed"] is False
    assert "redacted-sensitive-value" in serialized
    assert "RAW_PRIVATE_OBSERVATION_SHOULD_NOT_LEAK" not in serialized
    assert "PRIVATE_OBSERVATION_PROMPT_SHOULD_NOT_LEAK" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_default_promotion_observation_gate_aihub_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-benchmark-default-promotion-observation-gate")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()["data"]
    assert direct_payload["id"] == "modelops-legal-benchmark-default-promotion-observation-gate"
    assert direct_payload["summary"]["network_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/legal-benchmark-default-promotion-observation-gate",
        json={
            "legal_benchmark_default_promotion_execution_handoff": _execution_handoff(
                status="blocked",
                execution_status="blocked",
                blocking_ids=["synthetic-execution-block"],
            )
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["legal_benchmark_default_promotion_observation_gate"]["id"]
        == "modelops-legal-benchmark-default-promotion-observation-gate"
    )
    assert any(
        check["source_key"] == "legal_benchmark_default_promotion_observation_gate"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
