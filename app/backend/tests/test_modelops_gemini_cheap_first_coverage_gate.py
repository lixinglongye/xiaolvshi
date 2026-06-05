import json
import re

from services.modelops_gemini_cheap_first_coverage_gate import ModelOpsGeminiCheapFirstCoverageGateService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|api[_-]?key|authorization|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+"
)


def test_gemini_cheap_first_coverage_gate_builds_metadata_only_rows():
    gate = ModelOpsGeminiCheapFirstCoverageGateService().build_gate()
    rows = {row["task"]: row for row in gate["coverage_rows"]}

    assert gate["id"] == "modelops-gemini-cheap-first-coverage-gate"
    assert gate["status"] == "blocked"
    assert gate["summary"]["coverage_row_count"] == 8
    assert gate["summary"]["ready_row_count"] >= 5
    assert gate["summary"]["review_row_count"] >= 2
    assert gate["summary"]["blocked_row_count"] >= 1
    assert gate["summary"]["cheap_first_ready_count"] >= 5
    assert gate["summary"]["premium_exception_count"] == 2
    assert gate["summary"]["unknown_model_count"] == 0
    assert gate["summary"]["non_gemini_default_count"] == 0
    assert gate["summary"]["missing_reasoning_policy_count"] == 0
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["configuration_written"] is False
    assert gate["summary"]["credentials_included"] is False

    assert rows["fast"]["runtime_default_model"] == "gemini-2.5-flash-lite"
    assert rows["fast"]["cheap_first_aligned"] is True
    assert rows["fast"]["release_action"] == "keep_cheap_first_default"
    assert rows["review"]["runtime_default_model"] == "gemini-2.5-flash"
    assert rows["pdf"]["premium_exception"] is True
    assert rows["pdf"]["release_action"] == "require_operator_premium_exception"
    assert rows["image"]["model_family"] == "media"
    assert rows["agentic"]["coverage_status"] == "blocked"
    assert "cheap_first_not_aligned" in rows["agentic"]["reason_codes"]


def test_gemini_cheap_first_coverage_gate_links_existing_modelops_signals():
    gate = ModelOpsGeminiCheapFirstCoverageGateService().build_gate()

    assert gate["linked_signal_summary"]["capability_matrix_status"] == "ready"
    assert gate["linked_signal_summary"]["capability_task_count"] == 8
    assert gate["linked_signal_summary"]["configured_gateway_role_count"] >= 8
    assert gate["research_basis"]
    assert {item["id"] for item in gate["research_basis"]} == {
        "gemini-openai-compatibility",
        "gemini-models",
        "gemini-pricing",
    }

    for row in gate["coverage_rows"]:
        assert "capability-matrix" in row["linked_gate_ids"]
        assert "gemini-lifecycle-policy" in row["linked_gate_ids"]
        assert "gateway-compatibility" in row["linked_gate_ids"]
        assert "reasoning-policy" in row["linked_gate_ids"]
        assert row["privacy_boundary"]["raw_prompt_returned"] is False
        assert row["privacy_boundary"]["raw_payload_returned"] is False
        assert row["privacy_boundary"]["model_output_returned"] is False
        assert row["privacy_boundary"]["credentials_returned"] is False


def test_gemini_cheap_first_coverage_gate_boundaries_do_not_leak_sensitive_data():
    gate = ModelOpsGeminiCheapFirstCoverageGateService().build_gate()
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["model_called"] is False
    assert gate["privacy_boundary"]["gateway_called"] is False
    assert gate["privacy_boundary"]["network_called"] is False
    assert gate["privacy_boundary"]["configuration_written"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert gate["claim_boundary"]["live_gateway_execution_claimed"] is False
    assert gate["claim_boundary"]["production_quality_claimed"] is False
    assert gate["claim_boundary"]["automatic_default_change_claimed"] is False
    assert "UNSAFE_RAW_PROMPT_SHOULD_NOT_LEAK" not in serialized
    assert "raw prompt text from a user" not in serialized
    assert "raw gateway request body" not in serialized
    assert "raw model output text" not in serialized
    assert "client@example.com" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_cheap_first_coverage_gate_route_and_models_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-cheap-first-coverage-gate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["coverage_row_count"] == 8
    assert payload["data"]["summary"]["model_called"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["gemini_cheap_first_coverage_gate"]["id"] == "modelops-gemini-cheap-first-coverage-gate"
    assert any(
        check["source_key"] == "gemini_cheap_first_coverage_gate"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
