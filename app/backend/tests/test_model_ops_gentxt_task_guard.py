from services.model_ops_gentxt_task_guard import ModelOpsGenTxtTaskGuardService


def test_gentxt_task_guard_blocks_media_tasks_without_model_calls():
    gate = ModelOpsGenTxtTaskGuardService().build_gate()

    assert gate["id"] == "modelops-gentxt-routing-guard"
    assert gate["status"] == "pass"
    assert gate["summary"]["media_task_case_count"] == 6
    assert gate["summary"]["media_task_blocked_count"] == 6
    assert gate["summary"]["text_task_case_count"] == 5
    assert gate["summary"]["text_task_allowed_count"] == 5
    assert gate["summary"]["media_alias_default_count"] == 3
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["blocking_check_ids"] == []
    assert gate["warning_check_ids"] == []
    assert "gentxt-media-route-rejection" not in gate["blocking_check_ids"]
    assert "sk-" not in str(gate)

    media_rows = {row["requested_task"]: row for row in gate["media_task_rows"]}
    assert media_rows["video"]["resolved_text_task"] == "review"
    assert media_rows["video"]["guard_status"] == "blocked_to_review_text_budget"
    assert media_rows["video"]["model_default_if_media_endpoint"] == "wan2.6-t2v"
    assert media_rows["tts"]["normalized_task"] == "audio"
    assert media_rows["tts"]["model_default_if_media_endpoint"] == "qwen3-tts-flash"
    assert media_rows["speech-to-text"]["normalized_task"] == "transcription"
    assert media_rows["speech-to-text"]["model_default_if_media_endpoint"] == "scribe_v2"

    text_rows = {row["requested_task"]: row for row in gate["text_task_rows"]}
    assert text_rows["classification"]["guard_status"] == "allowed_text_budget"
    assert text_rows["agentic"]["resolved_text_task"] == "agentic"

    alias_rows = {row["alias"]: row for row in gate["media_alias_rows"]}
    assert alias_rows["auto-video"]["default_model"] == "wan2.6-t2v"
    assert alias_rows["auto-audio"]["default_model"] == "qwen3-tts-flash"
    assert alias_rows["auto-transcription"]["default_model"] == "scribe_v2"
    assert all(row["gentxt_allowed"] is False for row in alias_rows.values())


def test_gentxt_task_guard_routes_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    route_response = client.get("/api/v1/aihub/models/gentxt-routing-guard")
    assert route_response.status_code == 200
    route_payload = route_response.json()["data"]
    assert route_payload["status"] == "pass"
    assert route_payload["summary"]["media_task_blocked_count"] == 6

    post_response = client.post("/api/v1/aihub/models/gentxt-routing-guard", json={"ignored": "metadata-only"})
    assert post_response.status_code == 200
    assert post_response.json()["data"]["summary"]["gateway_called"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["gentxt_routing_guard"]["id"] == "modelops-gentxt-routing-guard"
    assert models_payload["gentxt_routing_guard"]["summary"]["media_task_blocked_count"] == 6
    assert "gentxt_routing_guard" in {
        check["source_key"] for check in models_payload["model_ops_readiness"]["checks"]
    }
    readiness_check = next(
        check for check in models_payload["model_ops_readiness"]["checks"] if check["source_key"] == "gentxt_routing_guard"
    )
    assert readiness_check["status"] == "pass"
