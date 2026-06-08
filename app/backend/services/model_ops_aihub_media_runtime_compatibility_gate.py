from __future__ import annotations

from typing import Any

from services.model_budget import model_budget_decision
from services.model_catalog import canonical_model_id, model_profile, task_default_model


OFFICIAL_RUNTIME_SOURCE_ROWS: tuple[dict[str, str], ...] = (
    {
        "id": "gemini-openai-compatibility",
        "title": "Gemini OpenAI compatibility",
        "url": "https://ai.google.dev/gemini-api/docs/openai",
        "tracked_signal": "OpenAI-compatible Gemini request boundary for text/image-style gateway calls.",
    },
    {
        "id": "gemini-veo-video-runtime",
        "title": "Veo video generation in Gemini API",
        "url": "https://ai.google.dev/gemini-api/docs/video",
        "tracked_signal": "Native Veo generation endpoint shape, polling behavior, and preview video model boundary.",
    },
    {
        "id": "gemini-speech-generation-runtime",
        "title": "Gemini speech generation",
        "url": "https://ai.google.dev/gemini-api/docs/speech-generation",
        "tracked_signal": "Native Gemini TTS request shape, response modality, voice config, and preview lifecycle.",
    },
    {
        "id": "gemini-audio-understanding-runtime",
        "title": "Gemini audio understanding",
        "url": "https://ai.google.dev/gemini-api/docs/audio",
        "tracked_signal": "Native audio understanding and speech-to-text shape for non-real-time audio inputs.",
    },
    {
        "id": "gemini-live-api-runtime",
        "title": "Gemini Live API",
        "url": "https://ai.google.dev/gemini-api/docs/live-guide",
        "tracked_signal": "Native Live API session/WebSocket boundary for real-time multimodal audio.",
    },
)


RUNTIME_ENDPOINT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "aihub-genvideo-runtime-shape",
        "task": "video",
        "endpoint_id": "aihub-genvideo",
        "service_method": "AIHubService.genvideo",
        "current_endpoint_shape": "openai_client_videos_create_retrieve",
        "current_runtime_methods": ("client.videos.create", "client.videos.retrieve"),
        "current_request_fields": ("model", "prompt", "size", "seconds", "input_reference"),
        "current_response_contract": "poll_task_then_extract_cdn_url",
        "native_family": "veo-video",
        "native_runtime_shape": "gemini_veo_video_generation_endpoint",
        "review_candidate_models": (
            "veo-3.1-lite-generate-preview",
            "veo-3.1-fast-generate-preview",
            "veo-3.1-generate-preview",
        ),
        "compatibility_status": "gateway_shape_review_required",
        "runtime_boundary": "Existing code is verified only for gateways that emulate client.videos.create/retrieve.",
        "release_action": "Keep Veo defaults review-only until gateway video shape and polling behavior are tested.",
    },
    {
        "id": "aihub-genaudio-runtime-shape",
        "task": "audio",
        "endpoint_id": "aihub-genaudio",
        "service_method": "AIHubService.genaudio",
        "current_endpoint_shape": "openai_client_audio_speech_create",
        "current_runtime_methods": ("client.audio.speech.create",),
        "current_request_fields": ("model", "input", "voice", "response_format"),
        "current_response_contract": "extract_cdn_url_from_speech_response",
        "native_family": "gemini-tts",
        "native_runtime_shape": "gemini_generate_content_audio_response_modality",
        "review_candidate_models": (
            "gemini-2.5-flash-preview-tts",
            "gemini-3.1-flash-tts-preview",
            "gemini-2.5-pro-preview-tts",
        ),
        "compatibility_status": "adapter_review_required",
        "runtime_boundary": "Existing code is verified only for OpenAI-compatible audio.speech gateways.",
        "release_action": "Keep Gemini TTS review-only until a native audio modality adapter or gateway speech adapter is validated.",
    },
    {
        "id": "aihub-transcribe-runtime-shape",
        "task": "transcription",
        "endpoint_id": "aihub-transcribe",
        "service_method": "AIHubService.transcribe",
        "current_endpoint_shape": "openai_client_audio_transcriptions_create",
        "current_runtime_methods": ("client.audio.transcriptions.create",),
        "current_request_fields": ("file", "model", "response_format"),
        "current_response_contract": "extract_text_from_transcription_response",
        "native_family": "gemini-audio-understanding",
        "native_runtime_shape": "gemini_generate_content_audio_input",
        "review_candidate_models": ("gemini-2.5-flash", "gemini-2.5-pro"),
        "compatibility_status": "adapter_review_required",
        "runtime_boundary": "Existing code is verified only for OpenAI-compatible transcription gateways.",
        "release_action": "Keep Gemini audio-understanding transcription review-only until audio-input request shape and output extraction are implemented.",
    },
    {
        "id": "aihub-live-audio-runtime-shape",
        "task": "live-audio",
        "endpoint_id": None,
        "service_method": None,
        "current_endpoint_shape": "not_implemented_live_session_route",
        "current_runtime_methods": (),
        "current_request_fields": (),
        "current_response_contract": "no_current_aihub_live_route",
        "native_family": "gemini-live-audio",
        "native_runtime_shape": "gemini_live_session_websocket",
        "review_candidate_models": (
            "gemini-3.1-flash-live-preview",
            "gemini-2.5-flash-native-audio-preview-12-2025",
        ),
        "compatibility_status": "future_route_required",
        "runtime_boundary": "No AIHub Live session route exists, so existing audio endpoints must not claim Live support.",
        "release_action": "Create a dedicated Live session route, catalog policy, and adapter tests before claiming support.",
    },
)


class ModelOpsAIHubMediaRuntimeCompatibilityGateService:
    """Build metadata-only compatibility evidence for AIHub media runtime shapes."""

    def build_gate(self, _payload: Any = None) -> dict[str, Any]:
        rows = [self._row(spec) for spec in RUNTIME_ENDPOINT_SPECS]
        checks = self._checks(rows)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-aihub-media-runtime-compatibility-gate",
            "title": "ModelOps AIHub media runtime compatibility gate",
            "status": status,
            "method": {
                "type": "metadata-only-media-runtime-compatibility-gate",
                "notes": [
                    "Inventories AIHub video, audio, transcription, and future Live runtime endpoint shapes.",
                    "Separates current OpenAI-compatible client methods from native Gemini/Veo/TTS/Live route requirements.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
                "source_urls": [row["url"] for row in OFFICIAL_RUNTIME_SOURCE_ROWS],
            },
            "summary": {
                "runtime_shape_count": len(rows),
                "implemented_endpoint_shape_count": sum(1 for row in rows if row["endpoint_id"]),
                "openai_compatible_shape_count": sum(
                    1 for row in rows if str(row["current_endpoint_shape"]).startswith("openai_client")
                ),
                "gateway_shape_review_required_count": sum(
                    1 for row in rows if row["compatibility_status"] == "gateway_shape_review_required"
                ),
                "adapter_review_required_count": sum(
                    1 for row in rows if row["compatibility_status"] == "adapter_review_required"
                ),
                "future_route_required_count": sum(
                    1 for row in rows if row["compatibility_status"] == "future_route_required"
                ),
                "review_required_shape_count": sum(
                    1 for row in rows if row["compatibility_status"] != "ready"
                ),
                "candidate_model_count": sum(len(row["review_candidate_models"]) for row in rows),
                "candidate_catalog_known_count": sum(row["candidate_catalog_known_count"] for row in rows),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "model_called": False,
                "default_changed": False,
                "raw_payload_echoed": False,
            },
            "official_source_rows": [dict(row) for row in OFFICIAL_RUNTIME_SOURCE_ROWS],
            "runtime_shape_rows": rows,
            "review_items": self._review_items(rows),
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "recommended_actions": self._recommended_actions(rows),
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "model_called": False,
                "traffic_shifted": False,
                "default_changed": False,
                "credentials_included": False,
                "headers_included": False,
                "prompts_included": False,
                "request_bodies_included": False,
                "response_bodies_included": False,
                "raw_payload_echoed": False,
                "raw_model_output_included": False,
                "raw_legal_text_included": False,
                "raw_media_included": False,
                "audio_transcripts_included": False,
                "emails_included": False,
                "output_scope": "endpoint ids, task labels, method names, model ids, catalog status, compatibility statuses, checks, and review actions only",
            },
            "claim_boundary": {
                "native_gemini_media_support_claimed": False,
                "veo_gateway_execution_claimed": False,
                "gemini_tts_adapter_claimed": False,
                "gemini_transcription_adapter_claimed": False,
                "live_audio_route_claimed": False,
                "default_change_claimed": False,
                "allowed_claim": "The repository exposes metadata-only media runtime compatibility evidence; current endpoints remain OpenAI-compatible-shape review items for Gemini/Veo/TTS/Live promotion.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_aihub_media_runtime_compatibility_gate.py tests/test_model_ops_aihub_media_speech_default_catalog_gate.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _row(self, spec: dict[str, Any]) -> dict[str, Any]:
        task = str(spec["task"])
        default_model = task_default_model(task) if spec.get("endpoint_id") else None
        profile = model_profile(default_model or "")
        budget = model_budget_decision(default_model, task=task) if default_model else None
        candidate_models = tuple(str(item) for item in spec["review_candidate_models"])
        candidate_catalog_models = [model for model in candidate_models if model_profile(model)]
        return {
            "id": str(spec["id"]),
            "task": task,
            "endpoint_id": spec.get("endpoint_id"),
            "service_method": spec.get("service_method"),
            "current_endpoint_shape": str(spec["current_endpoint_shape"]),
            "current_runtime_methods": [str(item) for item in spec["current_runtime_methods"]],
            "current_request_fields": [str(item) for item in spec["current_request_fields"]],
            "current_response_contract": str(spec["current_response_contract"]),
            "default_model": default_model,
            "canonical_model": canonical_model_id(default_model),
            "default_catalog_status": profile.status if profile else ("missing" if default_model else "not_applicable"),
            "default_cost_tier": profile.cost_tier if profile else ("unknown" if default_model else "not_applicable"),
            "budget_mode": budget.budget_mode if budget else "future-route",
            "requires_operator_review": True if budget is None else budget.requires_operator_review or profile is None,
            "native_family": str(spec["native_family"]),
            "native_runtime_shape": str(spec["native_runtime_shape"]),
            "review_candidate_models": list(candidate_models),
            "candidate_catalog_known_count": len(candidate_catalog_models),
            "candidate_catalog_models": candidate_catalog_models,
            "compatibility_status": str(spec["compatibility_status"]),
            "runtime_boundary": str(spec["runtime_boundary"]),
            "release_action": str(spec["release_action"]),
        }

    def _review_items(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        priority_by_status = {
            "future_route_required": "P1",
            "adapter_review_required": "P1",
            "gateway_shape_review_required": "P2",
            "ready": "P3",
        }
        return [
            {
                "id": f"media-runtime-{row['task']}",
                "task": row["task"],
                "priority": priority_by_status.get(str(row["compatibility_status"]), "P2"),
                "status": row["compatibility_status"],
                "endpoint_id": row["endpoint_id"],
                "native_family": row["native_family"],
                "next_action": row["release_action"],
                "release_gate_links": [
                    "modelops-aihub-media-runtime-compatibility-gate",
                    "modelops-aihub-media-speech-default-catalog-gate",
                    "modelops-aihub-endpoint-route-coverage-gate",
                ],
            }
            for row in rows
        ]

    def _checks(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        current_openai_shapes = [
            row["task"]
            for row in rows
            if str(row["current_endpoint_shape"]).startswith("openai_client")
        ]
        adapter_required = [
            row["task"]
            for row in rows
            if row["compatibility_status"] == "adapter_review_required"
        ]
        future_required = [
            row["task"]
            for row in rows
            if row["compatibility_status"] == "future_route_required"
        ]
        return [
            {
                "id": "current-runtime-shape-inventory",
                "status": "pass" if len(rows) == 4 and len(current_openai_shapes) == 3 else "fail",
                "reason": "Current video, audio, transcription, and future Live runtime shapes are inventoried.",
                "evidence": [row["id"] for row in rows],
            },
            {
                "id": "openai-compatible-shape-boundary",
                "status": "warn" if current_openai_shapes else "pass",
                "reason": "Implemented media endpoints are OpenAI-compatible client shapes and need gateway/native adapter review before Gemini/Veo promotion.",
                "evidence": current_openai_shapes,
            },
            {
                "id": "native-adapter-review-boundary",
                "status": "warn" if adapter_required else "pass",
                "reason": "Gemini TTS and audio-understanding candidates require native adapter or gateway-shape verification.",
                "evidence": adapter_required or ["no_adapter_gap"],
            },
            {
                "id": "live-session-route-boundary",
                "status": "warn" if future_required else "pass",
                "reason": "Live audio requires a dedicated session route and must not be claimed through existing TTS/transcription endpoints.",
                "evidence": future_required or ["no_future_live_gap"],
            },
            {
                "id": "metadata-only-runtime-boundary",
                "status": "pass",
                "reason": "This gate does not call providers, gateways, app AI endpoints, models, or write defaults.",
                "evidence": ["gateway_called:false", "network_called:false", "default_changed:false"],
            },
        ]

    def _recommended_actions(self, rows: list[dict[str, Any]]) -> list[str]:
        actions = [
            str(row["release_action"])
            for row in rows
            if row["compatibility_status"] != "ready"
        ]
        actions.append("Keep Gemini/Veo/TTS/Live media promotions review-only until runtime shape tests are attached.")
        return actions[:8]
