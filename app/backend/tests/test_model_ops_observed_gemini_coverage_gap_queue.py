import json
import re

from services.model_gateway_compatibility import ModelGatewayCompatibilityService
from services.model_ops_observed_gemini_coverage_gap_queue import (
    ModelOpsObservedGeminiCoverageGapQueueService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_observed_gemini_coverage_gap_queue_flags_unknown_and_family_gaps():
    result = ModelOpsObservedGeminiCoverageGapQueueService().build_queue(
        {
            "models_response": {
                "data": [
                    {"id": "models/gemini-2.5-flash-lite"},
                    {"id": "yibu/gemini-3.1-flash-image"},
                    {"id": "newapi/gemini-4.0-flash-lite-preview"},
                    {"id": "gemini-3.1-pro-preview"},
                ]
            }
        }
    )

    assert result["status"] == "blocked"
    assert result["summary"]["observed_model_count"] == 4
    assert result["summary"]["ready_cheap_first_candidate_count"] == 1
    assert result["summary"]["cheap_first_task_gap_count"] == 0
    assert result["summary"]["unknown_gemini_count"] == 1
    assert result["summary"]["preview_model_count"] == 1
    assert result["summary"]["family_gap_count"] >= 1
    assert all(row["coverage_status"] == "covered" for row in result["high_frequency_task_rows"])
    gap_types = {item["gap_type"] for item in result["gap_items"]}
    assert "observed_model_intake" in gap_types
    assert "gemini_family_coverage" in gap_types
    assert any("unknown-gemini-catalog-metadata" in item["reason_codes"] for item in result["gap_items"])
    assert result["privacy_boundary"]["gateway_called"] is False
    assert result["claim_boundary"]["all_gemini_models_supported_claimed"] is False


def test_observed_gemini_coverage_gap_queue_ready_for_default_gateway_examples():
    gateway = ModelGatewayCompatibilityService().evaluate()
    observed = [
        item.get("model")
        for item in gateway.get("configured_roles", []) + gateway.get("gateway_examples", [])
        if item.get("model")
    ]

    result = ModelOpsObservedGeminiCoverageGapQueueService().build_queue({"observed_models": observed})

    assert result["status"] == "review_required"
    assert result["summary"]["observed_model_count"] >= 4
    assert result["summary"]["cheap_first_task_covered_count"] == 4
    assert result["summary"]["cheap_first_task_gap_count"] == 0
    assert result["summary"]["covered_family_count"] >= 4
    assert result["summary"]["blocking_gap_count"] == 0
    assert any(item["gap_type"] == "observed_model_intake" for item in result["gap_items"])
    assert "premium" in " ".join(item["recommended_action"] for item in result["gap_items"]).lower()


def test_observed_gemini_coverage_gap_queue_metadata_only_boundaries():
    result = ModelOpsObservedGeminiCoverageGapQueueService().build_queue(
        {"model_ids": ["gemini-2.5-flash-lite", "gemini-2.5-flash"]}
    )
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["summary"]["configuration_written"] is False
    assert result["summary"]["gateway_called"] is False
    assert result["summary"]["network_called"] is False
    assert result["summary"]["raw_payload_echoed"] is False
    assert result["privacy_boundary"]["credentials_included"] is False
    assert result["privacy_boundary"]["raw_model_output_included"] is False
    assert result["claim_boundary"]["automatic_default_change_claimed"] is False
    assert result["claim_boundary"]["pricing_accuracy_claimed"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_observed_gemini_coverage_gap_queue_routes_and_model_ops_payload_include_queue():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/observed-gemini-coverage-gap-queue")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["configuration_written"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/observed-gemini-coverage-gap-queue",
        json={
            "models_response": {
                "data": [
                    {"id": "models/gemini-2.5-flash-lite"},
                    {"id": "newapi/gemini-4.0-flash-lite-preview"},
                ]
            }
        },
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert "observed_gemini_coverage_gap_queue" in payload
    assert payload["observed_gemini_coverage_gap_queue"]["summary"]["configuration_written"] is False
    assert any(
        check["source_key"] == "observed_gemini_coverage_gap_queue"
        for check in payload["model_ops_readiness"]["checks"]
    )
