import json
import re

from services.model_ops_aihub_media_speech_default_catalog_gate import (
    ModelOpsAIHubMediaSpeechDefaultCatalogGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|authorization|password|secret|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_media_speech_default_catalog_gate_tracks_current_defaults_and_future_gaps():
    gate = ModelOpsAIHubMediaSpeechDefaultCatalogGateService().build_gate()
    rows = {row["task"]: row for row in gate["default_rows"]}
    checks = {check["id"]: check for check in gate["checks"]}

    assert gate["id"] == "modelops-aihub-media-speech-default-catalog-gate"
    assert gate["status"] == "review_required"
    assert gate["summary"]["target_count"] == 6
    assert gate["summary"]["default_task_count"] == 4
    assert gate["summary"]["explicit_route_count"] == 4
    assert gate["summary"]["catalog_known_default_count"] == 1
    assert gate["summary"]["missing_catalog_default_count"] == 3
    assert gate["summary"]["review_required_default_count"] == 3
    assert gate["summary"]["future_family_gap_count"] == 2
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["configuration_written"] is False
    assert gate["blocking_check_ids"] == []
    assert "media-speech-default-inventory" not in gate["warning_check_ids"]
    assert "explicit-route-budget-boundary" not in gate["warning_check_ids"]
    assert "local-catalog-media-speech-defaults" in gate["warning_check_ids"]
    assert "official-family-gap-queue-attached" in gate["warning_check_ids"]
    assert checks["media-speech-default-inventory"]["status"] == "pass"
    assert checks["explicit-route-budget-boundary"]["status"] == "pass"
    assert checks["metadata-only-boundary"]["status"] == "pass"

    assert rows["image"]["default_model"] == "gemini-2.5-flash-image"
    assert rows["image"]["default_catalog_status"] == "stable"
    assert rows["image"]["default_release_action"] == "ready"
    assert rows["image"]["budget_mode"] == "explicit-media"
    assert rows["image"]["endpoint_ids"] == ["aihub-genimg"]

    assert rows["video"]["default_model"] == "wan2.6-t2v"
    assert rows["video"]["default_catalog_status"] == "missing"
    assert rows["video"]["default_release_action"] == "catalog_review_required"
    assert rows["video"]["budget_mode"] == "explicit-video-media"
    assert rows["video"]["endpoint_ids"] == ["aihub-genvideo"]
    assert "model_not_in_local_catalog" in rows["video"]["endpoint_gap_codes"]

    assert rows["audio"]["default_model"] == "qwen3-tts-flash"
    assert rows["audio"]["default_catalog_status"] == "missing"
    assert rows["audio"]["budget_mode"] == "explicit-speech-media"
    assert rows["audio"]["endpoint_ids"] == ["aihub-genaudio"]

    assert rows["transcription"]["default_model"] == "scribe_v2"
    assert rows["transcription"]["default_catalog_status"] == "missing"
    assert rows["transcription"]["budget_mode"] == "explicit-transcription"
    assert rows["transcription"]["endpoint_ids"] == ["aihub-transcribe"]

    assert rows["live-audio"]["default_model"] is None
    assert rows["live-audio"]["default_release_action"] == "future_route_gap"
    assert rows["live-audio"]["budget_mode"] == "future-route"
    assert rows["embedding"]["default_model"] is None
    assert rows["embedding"]["default_release_action"] == "future_route_gap"
    assert rows["embedding"]["budget_mode"] == "future-route"
    assert {item["task"] for item in gate["review_items"]} == set(rows)


def test_media_speech_default_catalog_gate_boundaries_are_metadata_only():
    gate = ModelOpsAIHubMediaSpeechDefaultCatalogGateService().build_gate(
        {
            "raw_prompt": "sk-THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED_123456789",
            "client_email": "client@example.com",
            "audio_transcript": "do not echo",
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["gateway_called"] is False
    assert gate["privacy_boundary"]["network_called"] is False
    assert gate["privacy_boundary"]["configuration_written"] is False
    assert gate["privacy_boundary"]["model_called"] is False
    assert gate["privacy_boundary"]["raw_legal_text_included"] is False
    assert gate["claim_boundary"]["all_media_speech_models_supported_claimed"] is False
    assert gate["claim_boundary"]["default_change_claimed"] is False
    assert gate["claim_boundary"]["live_audio_route_claimed"] is False
    assert "THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED" not in serialized
    assert "client@example.com" not in serialized
    assert "do not echo" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_media_speech_default_catalog_gate_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/aihub-media-speech-default-catalog-gate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-aihub-media-speech-default-catalog-gate"
    assert payload["data"]["summary"]["default_task_count"] == 4
    assert payload["data"]["summary"]["missing_catalog_default_count"] == 3
    assert payload["data"]["summary"]["gateway_called"] is False

    posted = client.post(
        "/api/v1/aihub/models/aihub-media-speech-default-catalog-gate",
        json={"raw_prompt": "do not echo", "model": "sk-THIS_SHOULD_NOT_BE_ECHOED_123456789"},
    )
    assert posted.status_code == 200
    assert posted.json()["data"]["summary"]["future_family_gap_count"] == 2
    assert "THIS_SHOULD_NOT_BE_ECHOED" not in json.dumps(posted.json(), ensure_ascii=False)

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["aihub_media_speech_default_catalog_gate"]["id"]
        == "modelops-aihub-media-speech-default-catalog-gate"
    )
    assert models_payload["aihub_media_speech_default_catalog_gate"]["summary"]["default_task_count"] == 4
    assert any(
        check["source_key"] == "aihub_media_speech_default_catalog_gate"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
