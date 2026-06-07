from __future__ import annotations

from typing import Any

from services.model_budget import model_budget_decision
from services.model_catalog import canonical_model_id, model_profile, task_default_model
from services.model_ops_aihub_endpoint_route_coverage_gate import (
    ModelOpsAIHubEndpointRouteCoverageGateService,
)


OFFICIAL_SOURCE_ROWS: tuple[dict[str, str], ...] = (
    {
        "id": "gemini-image-models",
        "title": "Gemini model list",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "tracked_signal": "Gemini image-capable models, lifecycle, modalities, and API model names.",
    },
    {
        "id": "gemini-veo-video",
        "title": "Veo video generation in Gemini API",
        "url": "https://ai.google.dev/gemini-api/docs/video",
        "tracked_signal": "Veo 3.1 video generation route, duration/resolution limits, and preview model posture.",
    },
    {
        "id": "gemini-speech-generation",
        "title": "Gemini speech generation",
        "url": "https://ai.google.dev/gemini-api/docs/speech-generation",
        "tracked_signal": "Native Gemini TTS models, preview lifecycle, voice/language support, and text-only input boundary.",
    },
    {
        "id": "gemini-audio-understanding",
        "title": "Gemini audio understanding",
        "url": "https://ai.google.dev/gemini-api/docs/audio",
        "tracked_signal": "Audio transcription, translation, diarization, and non-real-time speech-to-text boundaries.",
    },
    {
        "id": "gemini-live-api",
        "title": "Gemini Live API",
        "url": "https://ai.google.dev/gemini-api/docs/live-guide",
        "tracked_signal": "Native audio Live API model boundaries and real-time multimodal session requirements.",
    },
    {
        "id": "gemini-embeddings",
        "title": "Gemini embeddings",
        "url": "https://ai.google.dev/gemini-api/docs/embeddings",
        "tracked_signal": "Embedding model boundaries for RAG indexes, source matching, and future legal source retrieval routes.",
    },
)

MEDIA_SPEECH_DEFAULT_TARGETS: tuple[dict[str, Any], ...] = (
    {
        "task": "image",
        "display_name": "Image generation and editing",
        "route_kind": "explicit_media_route",
        "endpoint_ids": ("aihub-genimg",),
        "official_family": "gemini-image",
        "official_candidate_models": ("gemini-2.5-flash-image", "gemini-3.1-flash-image", "gemini-3-pro-image"),
        "cheap_first_policy": "explicit_media_low_cost_when_catalog_priced",
        "required_capabilities": ("image",),
        "default_change_policy": "keep_current_stable_image_default_unless_maintainer_changes_media_policy",
    },
    {
        "task": "video",
        "display_name": "Video generation",
        "route_kind": "explicit_video_route",
        "endpoint_ids": ("aihub-genvideo",),
        "official_family": "veo-video",
        "official_candidate_models": ("veo-3.1-generate-preview",),
        "cheap_first_policy": "explicit_media_review_only_until_catalog_priced",
        "required_capabilities": ("video-generation",),
        "default_change_policy": "do_not_replace_current_video_default_until_veo_catalog_and_gateway_review_pass",
    },
    {
        "task": "audio",
        "display_name": "Speech generation and TTS",
        "route_kind": "explicit_speech_route",
        "endpoint_ids": ("aihub-genaudio",),
        "official_family": "gemini-tts",
        "official_candidate_models": ("gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"),
        "cheap_first_policy": "explicit_speech_review_only_until_preview_tts_priced",
        "required_capabilities": ("tts", "audio-generation"),
        "default_change_policy": "do_not_replace_current_audio_default_until_tts_catalog_and_voice_policy_review_pass",
    },
    {
        "task": "transcription",
        "display_name": "Audio transcription and understanding",
        "route_kind": "explicit_transcription_route",
        "endpoint_ids": ("aihub-transcribe",),
        "official_family": "gemini-audio-understanding",
        "official_candidate_models": ("gemini-2.5-flash", "gemini-2.5-pro"),
        "cheap_first_policy": "explicit_speech_to_text_review_only_until_audio_pricing_and_latency_review",
        "required_capabilities": ("audio", "transcription"),
        "default_change_policy": "do_not_replace_current_transcription_default_until_audio_understanding_or_stt_policy_review_pass",
    },
    {
        "task": "live-audio",
        "display_name": "Live native audio",
        "route_kind": "future_live_route",
        "endpoint_ids": (),
        "official_family": "gemini-live-audio",
        "official_candidate_models": ("gemini-2.5-flash-native-audio-preview-12-2025",),
        "cheap_first_policy": "future_explicit_live_review_only",
        "required_capabilities": ("live", "audio"),
        "default_change_policy": "create_live_session_route_and_catalog_rows_before_claiming_live_audio_support",
    },
    {
        "task": "embedding",
        "display_name": "Embedding and RAG indexing",
        "route_kind": "future_embedding_route",
        "endpoint_ids": (),
        "official_family": "gemini-embedding",
        "official_candidate_models": (),
        "cheap_first_policy": "future_explicit_rag_index_review_only",
        "required_capabilities": ("embedding", "rag-index"),
        "default_change_policy": "create_embedding_route_catalog_pricing_and_index_policy_before_claiming_embedding_support",
    },
)


class ModelOpsAIHubMediaSpeechDefaultCatalogGateService:
    """Build metadata-only review evidence for AIHub media and speech defaults."""

    def build_gate(self, _payload: Any = None) -> dict[str, Any]:
        endpoint_gate = ModelOpsAIHubEndpointRouteCoverageGateService().build_gate()
        endpoint_rows = {row["id"]: row for row in endpoint_gate["endpoint_rows"]}
        default_rows = [self._default_row(target, endpoint_rows) for target in MEDIA_SPEECH_DEFAULT_TARGETS]
        endpoint_bound_rows = [row for row in default_rows if row["endpoint_count"] > 0]
        review_items = self._review_items(default_rows)
        checks = self._checks(default_rows, endpoint_gate)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-aihub-media-speech-default-catalog-gate",
            "title": "ModelOps AIHub media/speech default catalog gate",
            "status": status,
            "method": {
                "type": "metadata-only-aihub-media-speech-default-catalog-gate",
                "notes": [
                    "Reviews AIHub image, video, audio, transcription, and future Live audio defaults against local catalog and official Gemini/Veo/TTS source anchors.",
                    "Keeps non-catalog media and speech defaults explicit-review only until pricing, lifecycle, gateway behavior, and route policies are documented.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
                "source_urls": [row["url"] for row in OFFICIAL_SOURCE_ROWS],
            },
            "summary": {
                "target_count": len(default_rows),
                "default_task_count": len(endpoint_bound_rows),
                "endpoint_bound_target_count": sum(1 for row in default_rows if row["endpoint_count"] > 0),
                "explicit_route_count": len(endpoint_bound_rows),
                "catalog_known_default_count": sum(
                    1 for row in endpoint_bound_rows if row["default_catalog_status"] != "missing"
                ),
                "missing_catalog_default_count": sum(
                    1 for row in endpoint_bound_rows if row["default_catalog_status"] == "missing"
                ),
                "catalog_gap_count": sum(1 for row in default_rows if row["default_catalog_status"] == "missing"),
                "official_candidate_count": sum(len(row["official_candidate_models"]) for row in default_rows),
                "candidate_catalog_known_count": sum(row["official_candidate_catalog_known_count"] for row in default_rows),
                "explicit_review_target_count": sum(1 for row in default_rows if row["default_release_action"] != "ready"),
                "review_required_default_count": sum(
                    1 for row in endpoint_bound_rows if row["default_release_action"] != "ready"
                ),
                "future_route_count": sum(1 for row in default_rows if row["route_kind"].startswith("future")),
                "future_family_gap_count": sum(1 for row in default_rows if row["route_kind"].startswith("future")),
                "endpoint_gate_status": endpoint_gate["status"],
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "default_changed": False,
                "raw_payload_echoed": False,
            },
            "official_source_rows": [dict(row) for row in OFFICIAL_SOURCE_ROWS],
            "default_rows": default_rows,
            "review_items": review_items,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "recommended_actions": self._recommended_actions(default_rows),
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
                "emails_included": False,
                "output_scope": "task labels, endpoint ids, model ids, catalog status, budget mode, official source URLs, checks, and review actions only",
            },
            "claim_boundary": {
                "all_media_speech_models_supported_claimed": False,
                "official_catalog_refresh_completed": False,
                "default_change_claimed": False,
                "live_audio_route_claimed": False,
                "pricing_accuracy_claimed": False,
                "gateway_execution_claimed": False,
                "allowed_claim": "The repository exposes metadata-only media and speech default catalog review evidence; non-catalog or future-route defaults remain review-only.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_aihub_media_speech_default_catalog_gate.py tests/test_model_ops_aihub_endpoint_route_coverage_gate.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _default_row(self, target: dict[str, Any], endpoint_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
        task = str(target["task"])
        endpoint_ids = tuple(str(item) for item in target["endpoint_ids"])
        bound_endpoints = [endpoint_rows[item] for item in endpoint_ids if item in endpoint_rows]
        default_model = task_default_model(task) if endpoint_ids else None
        budget = model_budget_decision(default_model, task=task) if default_model else None
        canonical = canonical_model_id(default_model)
        profile = model_profile(default_model or "")
        candidate_models = tuple(str(item) for item in target["official_candidate_models"])
        candidate_catalog_known = [model for model in candidate_models if model_profile(model)]
        endpoint_gap_codes = sorted(
            {
                str(code)
                for endpoint in bound_endpoints
                for code in endpoint.get("route_gap_reason_codes", [])
                if code != "endpoint_route_coverage_ready"
            }
        )
        release_action = self._release_action(target, profile, endpoint_gap_codes, candidate_catalog_known)
        return {
            "task": task,
            "display_name": str(target["display_name"]),
            "route_kind": str(target["route_kind"]),
            "endpoint_ids": list(endpoint_ids),
            "endpoint_count": len(bound_endpoints),
            "endpoint_route_statuses": [str(endpoint.get("route_status")) for endpoint in bound_endpoints],
            "default_model": default_model,
            "canonical_model": canonical,
            "default_catalog_status": profile.status if profile else "missing",
            "default_cost_tier": profile.cost_tier if profile else "unknown",
            "default_pricing_status": self._pricing_status(profile),
            "budget_mode": budget.budget_mode if budget else "future-route",
            "is_known_model": budget.is_known_model if budget else False,
            "requires_operator_review": True if budget is None else budget.requires_operator_review or profile is None,
            "official_family": str(target["official_family"]),
            "official_candidate_models": list(candidate_models),
            "official_candidate_catalog_known_count": len(candidate_catalog_known),
            "official_candidate_catalog_models": candidate_catalog_known,
            "required_capabilities": list(str(item) for item in target["required_capabilities"]),
            "cheap_first_policy": str(target["cheap_first_policy"]),
            "default_change_policy": str(target["default_change_policy"]),
            "endpoint_gap_codes": endpoint_gap_codes,
            "default_release_action": release_action,
            "recommended_action": self._row_action(target, profile, endpoint_gap_codes, candidate_catalog_known),
        }

    def _pricing_status(self, profile: Any) -> str:
        if profile is None:
            return "missing"
        if profile.output_usd_per_image is not None:
            return "priced_per_image"
        if profile.input_usd_per_million_tokens is not None or profile.output_usd_per_million_tokens is not None:
            return "priced_per_token"
        return "missing"

    def _release_action(
        self,
        target: dict[str, Any],
        profile: Any,
        endpoint_gap_codes: list[str],
        candidate_catalog_known: list[str],
    ) -> str:
        if str(target["route_kind"]).startswith("future"):
            return "future_route_gap"
        if profile is None or "model_not_in_local_catalog" in endpoint_gap_codes:
            return "catalog_review_required"
        if profile.status != "stable" or self._pricing_status(profile) == "missing":
            return "pricing_or_lifecycle_review_required"
        if not candidate_catalog_known:
            return "official_candidate_review_required"
        return "ready"

    def _row_action(
        self,
        target: dict[str, Any],
        profile: Any,
        endpoint_gap_codes: list[str],
        candidate_catalog_known: list[str],
    ) -> str:
        task = str(target["task"])
        if str(target["route_kind"]).startswith("future"):
            return f"Create an explicit {task} route, request-policy notes, catalog rows, and source-backed pricing before claiming support."
        if profile is None:
            return f"Keep {task} default explicit-review only; add catalog, pricing, lifecycle, and gateway evidence before promotion."
        if "model_not_in_local_catalog" in endpoint_gap_codes:
            return f"Resolve {task} endpoint catalog warning before using this default for cost or support claims."
        if profile.status != "stable":
            return f"Keep {task} on explicit review because the current catalog lifecycle is {profile.status}."
        if self._pricing_status(profile) == "missing":
            return f"Refresh {task} pricing metadata before cost or cheap-first claims."
        if not candidate_catalog_known:
            return f"Attach at least one official {target['official_family']} candidate row before changing {task} defaults."
        return f"Keep {task} default unchanged and continue explicit media/speech route monitoring."

    def _review_items(self, default_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        priority_by_action = {
            "future_route_gap": "P1",
            "catalog_review_required": "P1",
            "pricing_or_lifecycle_review_required": "P2",
            "official_candidate_review_required": "P2",
            "ready": "P3",
        }
        return [
            {
                "id": f"media-speech-default-{row['task']}",
                "task": row["task"],
                "priority": priority_by_action.get(str(row["default_release_action"]), "P2"),
                "status": row["default_release_action"],
                "release_action": row["default_release_action"],
                "owner": "model_ops",
                "next_action": row["recommended_action"],
                "release_gate_links": [
                    "modelops-aihub-media-speech-default-catalog-gate",
                    "modelops-aihub-endpoint-route-coverage-gate",
                    "modelops-gemini-official-model-family-roadmap-evidence",
                ],
            }
            for row in default_rows
        ]

    def _checks(self, default_rows: list[dict[str, Any]], endpoint_gate: dict[str, Any]) -> list[dict[str, Any]]:
        bound_gaps = [row["task"] for row in default_rows if row["endpoint_count"] == 0 and not row["route_kind"].startswith("future")]
        endpoint_bound_rows = [row for row in default_rows if row["endpoint_count"] > 0]
        catalog_gaps = [row["task"] for row in default_rows if row["default_release_action"] == "catalog_review_required"]
        future_gaps = [row["task"] for row in default_rows if row["default_release_action"] == "future_route_gap"]
        ready_rows = [row["task"] for row in default_rows if row["default_release_action"] == "ready"]
        non_explicit_budget_rows = [
            row["task"]
            for row in endpoint_bound_rows
            if not str(row["budget_mode"]).startswith("explicit")
        ]
        official_candidate_gaps = [
            row["task"] for row in default_rows if row["official_candidate_catalog_known_count"] == 0
        ]
        return [
            {
                "id": "media-speech-default-inventory",
                "status": "pass" if len(endpoint_bound_rows) == 4 else "fail",
                "reason": "Image, video, audio, and transcription defaults are represented.",
                "evidence": [row["task"] for row in endpoint_bound_rows],
            },
            {
                "id": "future-family-gap-inventory",
                "status": "pass" if len(future_gaps) >= 2 else "warn",
                "reason": "Future Live audio and embedding families are tracked without claiming route support.",
                "evidence": [row["task"] for row in default_rows],
            },
            {
                "id": "endpoint-binding-coverage",
                "status": "warn" if bound_gaps else "pass",
                "reason": "Current media and speech defaults with AIHub endpoints are linked to endpoint route coverage evidence.",
                "evidence": bound_gaps or [row["task"] for row in default_rows if row["endpoint_count"] > 0],
            },
            {
                "id": "explicit-route-budget-boundary",
                "status": "warn" if non_explicit_budget_rows else "pass",
                "reason": "Current AIHub media and speech defaults stay on explicit media/speech budget modes.",
                "evidence": non_explicit_budget_rows or [row["task"] for row in endpoint_bound_rows],
            },
            {
                "id": "local-catalog-media-speech-defaults",
                "status": "warn" if catalog_gaps else "pass",
                "reason": "Non-catalog media and speech defaults remain explicit-review only until cataloged.",
                "evidence": catalog_gaps or ready_rows,
            },
            {
                "id": "official-family-gap-queue-attached",
                "status": "warn" if future_gaps else "pass",
                "reason": "Future Gemini Live audio and embedding support is queued without claiming AIHub routes exist.",
                "evidence": future_gaps or ["no_future_route_gap"],
            },
            {
                "id": "official-candidate-catalog-coverage",
                "status": "warn" if official_candidate_gaps else "pass",
                "reason": "Official Gemini/Veo/TTS candidate models should be cataloged before default changes.",
                "evidence": official_candidate_gaps or [row["task"] for row in default_rows],
            },
            {
                "id": "endpoint-route-gate-linked",
                "status": "warn" if endpoint_gate.get("status") == "blocked" else "pass",
                "reason": "The media/speech default review is linked to the AIHub endpoint route coverage gate.",
                "evidence": [str(endpoint_gate.get("id")), str(endpoint_gate.get("status"))],
            },
            {
                "id": "metadata-only-boundary",
                "status": "pass",
                "reason": "This gate does not call providers, gateways, app AI endpoints, models, or write defaults.",
                "evidence": ["gateway_called:false", "network_called:false", "default_changed:false"],
            },
        ]

    def _recommended_actions(self, default_rows: list[dict[str, Any]]) -> list[str]:
        actions = [
            row["recommended_action"]
            for row in default_rows
            if row["default_release_action"] != "ready"
        ]
        actions.append("Keep media and speech route defaults explicit-review only until source-backed catalog evidence is attached.")
        return actions[:8]
