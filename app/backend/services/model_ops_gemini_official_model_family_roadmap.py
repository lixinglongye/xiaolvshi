from __future__ import annotations

from typing import Any

from services.model_catalog import catalog_for_api, canonical_model_id, task_default_model


OFFICIAL_SOURCE_ROWS: tuple[dict[str, str], ...] = (
    {
        "id": "gemini-api-models",
        "title": "Gemini API model list",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "tracked_signal": "Official Gemini model families, lifecycle labels, supported modalities, and API names.",
    },
    {
        "id": "gemini-api-pricing",
        "title": "Gemini API pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing",
        "tracked_signal": "Token, image, audio, and model-family pricing that keeps cheap-first defaults honest.",
    },
    {
        "id": "gemini-openai-compatible",
        "title": "Gemini OpenAI compatibility",
        "url": "https://ai.google.dev/gemini-api/docs/openai",
        "tracked_signal": "OpenAI-compatible request shapes including chat, streaming, vision, tools, and structured outputs.",
    },
)

OFFICIAL_FAMILY_TARGETS: tuple[dict[str, Any], ...] = (
    {
        "family_id": "gemini-2.5-text",
        "display_name": "Gemini 2.5 text and multimodal",
        "official_scope": "Flash-Lite, Flash, and Pro text/vision models for high-volume routing, OCR, review, and long-context analysis.",
        "required_capabilities": ("text", "vision", "json", "long-context"),
        "catalog_model_ids": ("gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"),
        "preferred_cheap_first_model": "gemini-2.5-flash-lite",
        "fallback_model": "gemini-2.5-flash",
        "premium_exception_model": "gemini-2.5-pro",
        "route_policy": "cheap_first_for_high_frequency_then_balanced_or_premium_review",
        "default_claim": "covered_for_text_and_vision_defaults",
    },
    {
        "family_id": "gemini-3-text",
        "display_name": "Gemini 3 text, agentic, and grounding",
        "official_scope": "Gemini 3 style Flash/Flash-Lite/Pro models for agentic workflows, coding, grounding, and sustained reasoning.",
        "required_capabilities": ("text", "vision", "json", "agentic", "grounding"),
        "catalog_model_ids": (
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-3-flash-preview",
            "gemini-3.1-pro",
            "gemini-3.1-pro-preview",
        ),
        "preferred_cheap_first_model": "gemini-3.1-flash-lite",
        "fallback_model": "gemini-3-flash-preview",
        "premium_exception_model": "gemini-3.1-pro",
        "route_policy": "cheap_first_agentic_grounded_with_preview_and_pro_review",
        "default_claim": "covered_with_review_boundaries",
    },
    {
        "family_id": "gemini-image",
        "display_name": "Gemini image generation and editing",
        "official_scope": "Image generation and editing models that use media-specific pricing and explicit media routes.",
        "required_capabilities": ("image", "image-edit"),
        "catalog_model_ids": ("gemini-2.5-flash-image", "gemini-3.1-flash-image", "gemini-3-pro-image"),
        "preferred_cheap_first_model": "gemini-2.5-flash-image",
        "fallback_model": "gemini-3.1-flash-image",
        "premium_exception_model": "gemini-3-pro-image",
        "route_policy": "explicit_media_route_only",
        "default_claim": "covered_for_explicit_media_routes",
    },
    {
        "family_id": "gemini-live-audio",
        "display_name": "Gemini Live and native audio",
        "official_scope": "Real-time Live API and audio-capable Gemini models for multimodal conversation.",
        "required_capabilities": ("audio", "live"),
        "catalog_model_ids": (),
        "preferred_cheap_first_model": None,
        "fallback_model": None,
        "premium_exception_model": None,
        "route_policy": "future_explicit_live_route_only",
        "default_claim": "gap_queue_only",
    },
    {
        "family_id": "gemini-embedding",
        "display_name": "Gemini embeddings",
        "official_scope": "Embedding models for retrieval, source matching, and legal RAG index expansion.",
        "required_capabilities": ("embedding",),
        "catalog_model_ids": (),
        "preferred_cheap_first_model": None,
        "fallback_model": None,
        "premium_exception_model": None,
        "route_policy": "future_rag_index_route_only",
        "default_claim": "gap_queue_only",
    },
    {
        "family_id": "gemini-tts",
        "display_name": "Gemini text-to-speech",
        "official_scope": "Speech output and TTS model family support for explicit audio generation routes.",
        "required_capabilities": ("tts", "audio"),
        "catalog_model_ids": (),
        "preferred_cheap_first_model": None,
        "fallback_model": None,
        "premium_exception_model": None,
        "route_policy": "future_explicit_audio_route_only",
        "default_claim": "gap_queue_only",
    },
)

HIGH_FREQUENCY_TASKS = ("cheap", "fast", "classification", "ocr", "agentic", "grounded-research")


class ModelOpsGeminiOfficialModelFamilyRoadmapService:
    """Build metadata-only roadmap evidence for official Gemini family coverage."""

    def build_roadmap(self) -> dict[str, Any]:
        catalog_rows = catalog_for_api()
        family_rows = [self._family_row(target, catalog_rows) for target in OFFICIAL_FAMILY_TARGETS]
        roadmap_items = self._roadmap_items(family_rows)
        cheap_first_rows = self._cheap_first_rows(catalog_rows)
        checks = self._checks(family_rows, cheap_first_rows)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-gemini-official-model-family-roadmap-evidence",
            "title": "ModelOps Gemini official model family roadmap evidence",
            "status": status,
            "method": {
                "type": "metadata-only-gemini-official-family-roadmap",
                "notes": [
                    "Maps official Gemini model families to local catalog coverage, cheap-first candidates, and review-only gaps.",
                    "Keeps cheap Flash-Lite text defaults separate from explicit media, live audio, embedding, and speech roadmap items.",
                    "Does not call Gemini, Google, NewAPI, OpenAI, gateways, app AI endpoints, or the network.",
                ],
                "source_urls": [row["url"] for row in OFFICIAL_SOURCE_ROWS],
            },
            "summary": {
                "official_family_count": len(family_rows),
                "covered_family_count": sum(1 for row in family_rows if row["coverage_status"] == "covered"),
                "review_family_count": sum(1 for row in family_rows if row["coverage_status"] == "review_required"),
                "gap_family_count": sum(1 for row in family_rows if row["coverage_status"] == "gap"),
                "catalog_model_count": len(catalog_rows),
                "cheap_first_candidate_count": sum(1 for row in cheap_first_rows if row["cheap_first_allowed"]),
                "explicit_only_family_count": sum(1 for row in family_rows if "explicit" in row["route_policy"]),
                "roadmap_item_count": len(roadmap_items),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
            },
            "official_source_rows": [dict(row) for row in OFFICIAL_SOURCE_ROWS],
            "family_rows": family_rows,
            "roadmap_items": roadmap_items,
            "cheap_first_evidence_rows": cheap_first_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(family_rows, warnings),
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "headers_included": False,
                "prompts_included": False,
                "request_bodies_included": False,
                "response_bodies_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "official source ids and URLs, local catalog model ids, family labels, capabilities, route policies, checks, and maintainer actions only",
            },
            "claim_boundary": {
                "all_gemini_models_supported_claimed": False,
                "official_source_refresh_completed": False,
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "production_quality_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claim": "The repository exposes metadata-only roadmap evidence for official Gemini family coverage and cheap-first review gaps.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_official_model_family_roadmap.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _family_row(self, target: dict[str, Any], catalog_rows: list[dict[str, Any]]) -> dict[str, Any]:
        required = tuple(str(item) for item in target["required_capabilities"])
        catalog_model_ids = {str(item) for item in target.get("catalog_model_ids") or ()}
        matched = [row for row in catalog_rows if str(row.get("id") or "") in catalog_model_ids]
        preferred = self._catalog_match(catalog_rows, target.get("preferred_cheap_first_model"))
        fallback = self._catalog_match(catalog_rows, target.get("fallback_model"))
        premium = self._catalog_match(catalog_rows, target.get("premium_exception_model"))
        missing_capabilities = [
            capability
            for capability in required
            if not any(capability in set(str(item) for item in row.get("capabilities") or []) for row in matched)
        ]
        if not matched or not preferred:
            coverage_status = "gap"
        elif missing_capabilities or any(str(row.get("status")) in {"preview", "review"} for row in matched):
            coverage_status = "review_required"
        else:
            coverage_status = "covered"
        return {
            "family_id": str(target["family_id"]),
            "display_name": str(target["display_name"]),
            "official_scope": str(target["official_scope"]),
            "required_capabilities": list(required),
            "coverage_status": coverage_status,
            "catalog_model_count": len(matched),
            "catalog_models": [str(row.get("id")) for row in matched],
            "missing_capabilities": missing_capabilities,
            "preferred_cheap_first_model": target.get("preferred_cheap_first_model"),
            "preferred_model_catalog_status": str(preferred.get("status") or "missing") if preferred else "missing",
            "preferred_model_cost_tier": str(preferred.get("cost_tier") or "unknown") if preferred else "missing",
            "fallback_model": target.get("fallback_model"),
            "fallback_model_catalog_status": str(fallback.get("status") or "missing") if fallback else "missing",
            "premium_exception_model": target.get("premium_exception_model"),
            "premium_model_catalog_status": str(premium.get("status") or "missing") if premium else "missing",
            "route_policy": str(target["route_policy"]),
            "default_claim": str(target["default_claim"]),
            "high_frequency_default_allowed": bool(preferred)
            and "flash-lite" in str(target.get("preferred_cheap_first_model") or "")
            and str(preferred.get("status") or "") == "stable"
            and str(preferred.get("cost_tier") or "") in {"lowest", "low"},
            "recommended_action": self._family_action(str(target["family_id"]), coverage_status, missing_capabilities),
        }

    def _catalog_match(self, catalog_rows: list[dict[str, Any]], model_id: Any) -> dict[str, Any] | None:
        canonical = canonical_model_id(str(model_id or ""))
        if not canonical:
            return None
        return next((row for row in catalog_rows if row.get("id") == canonical), None)

    def _roadmap_items(self, family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in family_rows:
            if row["coverage_status"] == "covered":
                action_type = "monitor"
                priority = "P3"
                owner = "model_ops"
            elif row["coverage_status"] == "review_required":
                action_type = "review"
                priority = "P2"
                owner = "model_ops"
            else:
                action_type = "catalog_gap"
                priority = "P1"
                owner = "model_ops"
            items.append(
                {
                    "id": f"gemini-official-family-{row['family_id']}",
                    "family_id": row["family_id"],
                    "priority": priority,
                    "action_type": action_type,
                    "owner": owner,
                    "status": row["coverage_status"],
                    "route_policy": row["route_policy"],
                    "next_action": row["recommended_action"],
                    "claim_boundary": "metadata-only roadmap; no live support or quality claim",
                }
            )
        return items

    def _cheap_first_rows(self, catalog_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for task in HIGH_FREQUENCY_TASKS:
            default_model = task_default_model(task)
            canonical = canonical_model_id(default_model)
            catalog = next((row for row in catalog_rows if row.get("id") == canonical), None)
            cheap_first_allowed = bool(catalog) and "flash-lite" in str(canonical) and str(catalog.get("status")) == "stable"
            rows.append(
                {
                    "task": task,
                    "default_model": default_model,
                    "canonical_model": canonical,
                    "catalog_status": str(catalog.get("status") or "missing") if catalog else "missing",
                    "cost_tier": str(catalog.get("cost_tier") or "unknown") if catalog else "unknown",
                    "cheap_first_allowed": cheap_first_allowed,
                    "review_required": not cheap_first_allowed,
                    "recommended_action": "Keep the current stable Flash-Lite default for this high-frequency route."
                    if cheap_first_allowed
                    else "Review this high-frequency route before claiming cheap-first Gemini coverage.",
                }
            )
        return rows

    def _checks(self, family_rows: list[dict[str, Any]], cheap_first_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        gap_families = [row["family_id"] for row in family_rows if row["coverage_status"] == "gap"]
        review_families = [row["family_id"] for row in family_rows if row["coverage_status"] == "review_required"]
        cheap_first_gaps = [row["task"] for row in cheap_first_rows if not row["cheap_first_allowed"]]
        return [
            {
                "id": "official-family-roadmap-attached",
                "status": "pass" if len(family_rows) >= 6 else "fail",
                "reason": "Official Gemini model families are mapped into local roadmap rows."
                if len(family_rows) >= 6
                else "Official Gemini family roadmap rows are incomplete.",
            },
            {
                "id": "cheap-first-high-frequency-defaults",
                "status": "pass" if not cheap_first_gaps else "fail",
                "reason": "High-frequency Gemini tasks resolve to stable Flash-Lite defaults."
                if not cheap_first_gaps
                else "High-frequency Gemini tasks are missing stable Flash-Lite defaults: " + ", ".join(cheap_first_gaps) + ".",
            },
            {
                "id": "official-family-gap-queue",
                "status": "warn" if gap_families else "pass",
                "reason": "All tracked official Gemini families have local catalog coverage."
                if not gap_families
                else "Some official Gemini families remain roadmap gaps and must not be claimed as supported: "
                + ", ".join(gap_families)
                + ".",
            },
            {
                "id": "preview-and-review-family-boundary",
                "status": "warn" if review_families else "pass",
                "reason": "Tracked Gemini families are stable or explicitly gap-queued."
                if not review_families
                else "Preview, review-only, or partially covered Gemini families require maintainer review: "
                + ", ".join(review_families)
                + ".",
            },
            {
                "id": "no-live-or-default-change-claim",
                "status": "pass",
                "reason": "The roadmap evidence does not claim live gateway execution, pricing accuracy, production quality, or automatic default changes.",
            },
        ]

    def _family_action(self, family_id: str, coverage_status: str, missing_capabilities: list[str]) -> str:
        if coverage_status == "covered":
            return f"Keep {family_id} on its current cheap-first or explicit route policy and refresh official sources before default changes."
        if coverage_status == "review_required":
            missing = ", ".join(missing_capabilities) if missing_capabilities else "preview/review-only catalog boundaries"
            return f"Review {family_id} before promotion; unresolved scope: {missing}."
        return f"Add catalog rows, pricing posture, request-policy notes, and explicit route boundaries before claiming {family_id} support."

    def _recommended_actions(self, family_rows: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
        if not warnings:
            return ["All tracked Gemini family roadmap rows are ready; refresh official sources before changing defaults."]
        actions = [
            row["recommended_action"]
            for row in family_rows
            if row["coverage_status"] in {"gap", "review_required"}
        ]
        actions.append("Keep high-frequency text defaults on stable Flash-Lite models until roadmap gaps are reviewed.")
        return actions[:8]
