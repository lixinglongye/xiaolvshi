import json
import re

from services.model_ops_observed_gemini_model_intake_queue import (
    ModelOpsObservedGeminiModelIntakeQueueService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_observed_gemini_model_intake_queue_ranks_ready_blocked_and_review_models():
    queue = ModelOpsObservedGeminiModelIntakeQueueService().build_queue(
        {
            "models_response": {
                "data": [
                    {"id": "models/gemini-2.5-flash-lite"},
                    {"id": "google/gemini-3.5-flash"},
                    {"id": "yibu/gemini-3.1-flash-image"},
                    {"id": "newapi/gemini-4.0-flash-lite-preview"},
                    {"id": "gemini-3.1-pro-preview"},
                    {"id": "provider/not-gemini"},
                ]
            }
        }
    )
    rows = {row["raw_model"]: row for row in queue["queue_items"]}

    assert queue["status"] == "blocked"
    assert queue["summary"]["observed_model_count"] == 6
    assert queue["summary"]["cheap_first_candidate_count"] == 1
    assert queue["summary"]["unknown_gemini_count"] == 1
    assert rows["models/gemini-2.5-flash-lite"]["intake_status"] == "ready"
    assert rows["models/gemini-2.5-flash-lite"]["cheap_first_default_candidate"] is True
    assert rows["models/gemini-2.5-flash-lite"]["allowed_default_tasks"] == [
        "cheap",
        "fast",
        "ocr",
        "classification",
    ]
    assert rows["google/gemini-3.5-flash"]["intake_status"] == "review_required"
    assert "not-cheap-first-default" in rows["google/gemini-3.5-flash"]["reason_codes"]
    assert rows["yibu/gemini-3.1-flash-image"]["intake_action"] == "media_route_review"
    assert rows["yibu/gemini-3.1-flash-image"]["intake_status"] == "review_required"
    assert rows["newapi/gemini-4.0-flash-lite-preview"]["intake_status"] == "blocked"
    assert "unknown-gemini-catalog-metadata" in rows["newapi/gemini-4.0-flash-lite-preview"]["reason_codes"]
    assert rows["gemini-3.1-pro-preview"]["intake_status"] == "review_required"
    assert "lifecycle-preview" in rows["gemini-3.1-pro-preview"]["reason_codes"]
    assert rows["provider/not-gemini"]["release_action"] == "exclude_from_gemini_default_candidates"


def test_observed_gemini_model_intake_queue_metadata_only_boundaries():
    queue = ModelOpsObservedGeminiModelIntakeQueueService().build_queue(
        {"model_ids": ["gemini-2.5-flash-lite", "gemini-2.5-flash"]}
    )
    serialized = json.dumps(queue, ensure_ascii=False)

    assert queue["summary"]["configuration_written"] is False
    assert queue["summary"]["gateway_called"] is False
    assert queue["summary"]["network_called"] is False
    assert queue["summary"]["raw_payload_echoed"] is False
    assert queue["privacy_boundary"]["credentials_included"] is False
    assert queue["privacy_boundary"]["raw_model_output_included"] is False
    assert queue["claim_boundary"]["automatic_default_change_claimed"] is False
    assert queue["claim_boundary"]["pricing_accuracy_claimed"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_observed_gemini_model_intake_queue_route_and_models_payload_include_queue():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/observed-gemini-model-intake-queue")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["configuration_written"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/observed-gemini-model-intake-queue",
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
    assert "observed_gemini_model_intake_queue" in payload
    assert payload["observed_gemini_model_intake_queue"]["summary"]["configuration_written"] is False
    assert any(
        check["source_key"] == "observed_gemini_model_intake_queue"
        for check in payload["model_ops_readiness"]["checks"]
    )
