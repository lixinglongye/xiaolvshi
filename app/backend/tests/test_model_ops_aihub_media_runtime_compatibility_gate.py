import json
import re

from services.model_ops_aihub_media_runtime_compatibility_gate import (
    ModelOpsAIHubMediaRuntimeCompatibilityGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|authorization|password|secret|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_media_runtime_compatibility_gate_tracks_openai_shapes_and_native_boundaries():
    gate = ModelOpsAIHubMediaRuntimeCompatibilityGateService().build_gate()
    rows = {row["task"]: row for row in gate["runtime_shape_rows"]}
    checks = {check["id"]: check for check in gate["checks"]}

    assert gate["id"] == "modelops-aihub-media-runtime-compatibility-gate"
    assert gate["status"] == "review_required"
    assert gate["summary"]["runtime_shape_count"] == 4
    assert gate["summary"]["implemented_endpoint_shape_count"] == 3
    assert gate["summary"]["openai_compatible_shape_count"] == 3
    assert gate["summary"]["gateway_shape_review_required_count"] == 1
    assert gate["summary"]["adapter_review_required_count"] == 2
    assert gate["summary"]["future_route_required_count"] == 1
    assert gate["summary"]["review_required_shape_count"] == 4
    assert gate["summary"]["candidate_model_count"] == 10
    assert gate["summary"]["candidate_catalog_known_count"] == 10
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["configuration_written"] is False
    assert gate["blocking_check_ids"] == []
    assert "openai-compatible-shape-boundary" in gate["warning_check_ids"]
    assert "native-adapter-review-boundary" in gate["warning_check_ids"]
    assert "live-session-route-boundary" in gate["warning_check_ids"]
    assert checks["current-runtime-shape-inventory"]["status"] == "pass"
    assert checks["metadata-only-runtime-boundary"]["status"] == "pass"

    assert rows["video"]["endpoint_id"] == "aihub-genvideo"
    assert rows["video"]["current_endpoint_shape"] == "openai_client_videos_create_retrieve"
    assert rows["video"]["current_runtime_methods"] == ["client.videos.create", "client.videos.retrieve"]
    assert rows["video"]["native_family"] == "veo-video"
    assert rows["video"]["native_runtime_shape"] == "gemini_veo_video_generation_endpoint"
    assert rows["video"]["compatibility_status"] == "gateway_shape_review_required"
    assert rows["video"]["default_model"] == "wan2.6-t2v"
    assert rows["video"]["default_catalog_status"] == "missing"

    assert rows["audio"]["endpoint_id"] == "aihub-genaudio"
    assert rows["audio"]["current_endpoint_shape"] == "openai_client_audio_speech_create"
    assert rows["audio"]["current_runtime_methods"] == ["client.audio.speech.create"]
    assert rows["audio"]["native_family"] == "gemini-tts"
    assert rows["audio"]["native_runtime_shape"] == "gemini_generate_content_audio_response_modality"
    assert rows["audio"]["compatibility_status"] == "adapter_review_required"
    assert rows["audio"]["default_model"] == "qwen3-tts-flash"

    assert rows["transcription"]["endpoint_id"] == "aihub-transcribe"
    assert rows["transcription"]["current_endpoint_shape"] == "openai_client_audio_transcriptions_create"
    assert rows["transcription"]["current_runtime_methods"] == ["client.audio.transcriptions.create"]
    assert rows["transcription"]["native_family"] == "gemini-audio-understanding"
    assert rows["transcription"]["native_runtime_shape"] == "gemini_generate_content_audio_input"
    assert rows["transcription"]["compatibility_status"] == "adapter_review_required"
    assert rows["transcription"]["default_model"] == "scribe_v2"

    assert rows["live-audio"]["endpoint_id"] is None
    assert rows["live-audio"]["current_endpoint_shape"] == "not_implemented_live_session_route"
    assert rows["live-audio"]["native_runtime_shape"] == "gemini_live_session_websocket"
    assert rows["live-audio"]["compatibility_status"] == "future_route_required"
    assert rows["live-audio"]["default_model"] is None
    assert {item["task"] for item in gate["review_items"]} == set(rows)


def test_media_runtime_compatibility_gate_boundaries_are_metadata_only():
    gate = ModelOpsAIHubMediaRuntimeCompatibilityGateService().build_gate(
        {
            "raw_prompt": "sk-THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED_123456789",
            "client_email": "client@example.com",
            "audio_transcript": "do not echo",
            "headers": {"authorization": "bearer secret"},
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["gateway_called"] is False
    assert gate["privacy_boundary"]["network_called"] is False
    assert gate["privacy_boundary"]["configuration_written"] is False
    assert gate["privacy_boundary"]["raw_media_included"] is False
    assert gate["claim_boundary"]["native_gemini_media_support_claimed"] is False
    assert gate["claim_boundary"]["veo_gateway_execution_claimed"] is False
    assert gate["claim_boundary"]["gemini_tts_adapter_claimed"] is False
    assert gate["claim_boundary"]["live_audio_route_claimed"] is False
    assert "THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED" not in serialized
    assert "client@example.com" not in serialized
    assert "do not echo" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_media_runtime_compatibility_gate_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/aihub-media-runtime-compatibility-gate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-aihub-media-runtime-compatibility-gate"
    assert payload["data"]["summary"]["openai_compatible_shape_count"] == 3
    assert payload["data"]["summary"]["gateway_called"] is False

    posted = client.post(
        "/api/v1/aihub/models/aihub-media-runtime-compatibility-gate",
        json={"raw_prompt": "do not echo", "model": "sk-THIS_SHOULD_NOT_BE_ECHOED_123456789"},
    )
    assert posted.status_code == 200
    assert posted.json()["data"]["summary"]["future_route_required_count"] == 1
    assert "THIS_SHOULD_NOT_BE_ECHOED" not in json.dumps(posted.json(), ensure_ascii=False)

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["aihub_media_runtime_compatibility_gate"]["id"]
        == "modelops-aihub-media-runtime-compatibility-gate"
    )
    assert models_payload["aihub_media_runtime_compatibility_gate"]["summary"]["adapter_review_required_count"] == 2
    assert any(
        check["source_key"] == "aihub_media_runtime_compatibility_gate"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
