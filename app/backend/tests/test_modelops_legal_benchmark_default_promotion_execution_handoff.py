import json
import re

from services.modelops_legal_benchmark_default_promotion_execution_handoff import (
    ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def _signoff_packet(
    *,
    status: str = "review_required",
    signoff_status: str = "ready_for_signoff",
    external_signoff_status: str = "not_attached",
    rollback_plan_status: str = "not_attached",
    config_diff_status: str = "not_attached",
    observation_plan_status: str = "not_attached",
    blocking_ids: list[str] | None = None,
    model_id: str = "gemini-2.5-flash-lite",
) -> dict:
    blocking_ids = blocking_ids or []
    return {
        "id": "modelops-legal-benchmark-default-promotion-signoff-packet",
        "title": "ModelOps legal benchmark default-promotion signoff packet",
        "status": status,
        "summary": {
            "source_count": 1,
            "signoff_item_count": 1,
            "ready_for_signoff_count": 1 if signoff_status == "ready_for_signoff" else 0,
            "review_required_count": 0,
            "blocked_count": 1 if blocking_ids or status == "blocked" else 0,
            "not_run_count": 0,
            "configuration_written": False,
            "env_file_written": False,
            "approval_record_written": False,
            "signoff_record_written": False,
            "gateway_called": False,
            "network_called": False,
            "raw_payload_echoed": False,
            "raw_model_output_returned": False,
        },
        "signoff_items": [
            {
                "id": "legal-benchmark-default-promotion-signoff-1",
                "source_checklist_row_id": "legal-benchmark-default-promotion-checklist-1",
                "requirement_id": "legal-fixture-promotion-contract-review",
                "fixture_id": "contract-risk-review-basic",
                "task": "legal_review",
                "proposed_default_model": model_id,
                "model_cost_tier": "lowest",
                "signoff_status": signoff_status,
                "external_signoff_status": external_signoff_status,
                "rollback_plan_status": rollback_plan_status,
                "config_diff_status": config_diff_status,
                "observation_plan_status": observation_plan_status,
                "reason_codes": ["legal-fixture-evidence-ready"],
            }
        ],
        "blocking_check_ids": blocking_ids,
        "warning_check_ids": [],
    }


def test_default_promotion_execution_handoff_ready_when_external_evidence_is_attached():
    packet = ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService().build_handoff(
        {
            "legal_benchmark_default_promotion_signoff_packet": _signoff_packet(
                external_signoff_status="signed",
                rollback_plan_status="ready",
                config_diff_status="reviewed",
                observation_plan_status="ready",
            )
        }
    )
    row = packet["handoff_rows"][0]
    rollback_item = packet["rollback_gate_items"][0]
    checks = {check["id"]: check for check in packet["checks"]}

    assert packet["id"] == "modelops-legal-benchmark-default-promotion-execution-handoff"
    assert packet["status"] == "ready_for_external_execution"
    assert packet["decision"]["execution_handoff_ready"] is True
    assert packet["decision"]["default_change_allowed_by_execution_handoff"] is False
    assert packet["decision"]["rollback_execution_allowed"] is False
    assert packet["summary"]["ready_for_external_execution_count"] == 1
    assert packet["summary"]["rollback_ready_count"] == 1
    assert packet["summary"]["configuration_written"] is False
    assert packet["summary"]["rollback_executed"] is False
    assert packet["summary"]["traffic_shifted"] is False
    assert row["execution_status"] == "ready_for_external_execution"
    assert row["default_change_allowed_by_execution_handoff"] is False
    assert row["traffic_shift_allowed"] is False
    assert "legal-benchmark-smoke-rerun-ready" in row["rollback_checks"]
    assert rollback_item["rollback_gate_status"] == "ready"
    assert rollback_item["rollback_execution_allowed"] is False
    assert checks["default-promotion-signoff-packet-attached-not-blocked"]["status"] == "pass"
    assert checks["external-signoff-record-attached"]["status"] == "pass"
    assert checks["rollback-plan-ready"]["status"] == "pass"


def test_default_promotion_execution_handoff_blocks_when_signoff_packet_blocks():
    packet = ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService().build_handoff(
        {
            "legal_benchmark_default_promotion_signoff_packet": _signoff_packet(
                status="blocked",
                signoff_status="blocked",
                blocking_ids=["default-promotion-checklist-attached-not-blocked"],
            )
        }
    )

    assert packet["status"] == "blocked"
    assert "default-promotion-signoff-packet-attached-not-blocked" in packet["blocking_check_ids"]
    assert packet["handoff_rows"][0]["execution_status"] == "blocked"
    assert packet["rollback_gate_items"][0]["rollback_gate_status"] == "blocked"
    assert packet["decision"]["release_action"] == "block_default_promotion"


def test_default_promotion_execution_handoff_requires_rollback_evidence_before_execution_handoff():
    packet = ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService().build_handoff(
        {
            "legal_benchmark_default_promotion_signoff_packet": _signoff_packet(
                external_signoff_status="signed",
                rollback_plan_status="not_attached",
                config_diff_status="reviewed",
                observation_plan_status="ready",
            )
        }
    )
    checks = {check["id"]: check for check in packet["checks"]}

    assert packet["status"] == "review_required"
    assert packet["summary"]["awaiting_external_signoff_count"] == 1
    assert packet["summary"]["rollback_ready_count"] == 0
    assert packet["handoff_rows"][0]["execution_status"] == "awaiting_external_signoff"
    assert "rollback-plan-missing" in packet["handoff_rows"][0]["reason_codes"]
    assert packet["rollback_gate_items"][0]["rollback_gate_status"] == "review_required"
    assert checks["rollback-plan-ready"]["status"] == "warn"
    assert packet["summary"]["traffic_shifted"] is False


def test_default_promotion_execution_handoff_redacts_sensitive_values():
    payload = {
        "legal_benchmark_default_promotion_signoff_packet": _signoff_packet(model_id="sk-" + ("e" * 24)),
        "api_key": "sk-" + ("f" * 24),
        "raw_output": "RAW_PRIVATE_EXECUTION_HANDOFF_SHOULD_NOT_LEAK",
        "prompt": "PRIVATE_PROMPT_SHOULD_NOT_LEAK",
    }

    packet = ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService().build_handoff(payload)
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["summary"]["raw_input_field_count"] >= 3
    assert packet["summary"]["network_called"] is False
    assert packet["claim_boundary"]["configuration_change_claimed"] is False
    assert "redacted-sensitive-value" in serialized
    assert "RAW_PRIVATE_EXECUTION_HANDOFF_SHOULD_NOT_LEAK" not in serialized
    assert "PRIVATE_PROMPT_SHOULD_NOT_LEAK" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_default_promotion_execution_handoff_aihub_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()["data"]
    assert direct_payload["id"] == "modelops-legal-benchmark-default-promotion-execution-handoff"
    assert direct_payload["summary"]["network_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff",
        json={
            "legal_benchmark_default_promotion_signoff_packet": _signoff_packet(
                status="blocked",
                signoff_status="blocked",
                blocking_ids=["synthetic-signoff-block"],
            )
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["legal_benchmark_default_promotion_execution_handoff"]["id"]
        == "modelops-legal-benchmark-default-promotion-execution-handoff"
    )
    assert any(
        check["source_key"] == "legal_benchmark_default_promotion_execution_handoff"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
