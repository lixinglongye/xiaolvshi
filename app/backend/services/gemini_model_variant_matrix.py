from __future__ import annotations

from typing import Any

from services.gemini_newapi_cheap_first_policy import GeminiNewapiCheapFirstPolicyService
from services.gemini_newapi_model_selector import GeminiNewapiModelSelectorService
from services.gemini_newapi_observed_model_extraction import (
    extract_observed_model_ids,
)
from services.model_default_candidate_selector import ModelDefaultCandidateSelectorService
from services.model_catalog import GEMINI_MODEL_CATALOG, catalog_for_api


class GeminiModelVariantMatrixService:
    """Build a metadata-only Gemini variant matrix for cheap-first routing review."""

    def __init__(
        self,
        policy_service: GeminiNewapiCheapFirstPolicyService | None = None,
        selector_service: GeminiNewapiModelSelectorService | None = None,
        default_candidate_selector: ModelDefaultCandidateSelectorService | None = None,
    ) -> None:
        self.policy_service = policy_service or GeminiNewapiCheapFirstPolicyService()
        self.selector_service = selector_service or GeminiNewapiModelSelectorService()
        self.default_candidate_selector = default_candidate_selector or ModelDefaultCandidateSelectorService()

    def build_matrix(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        observed_model_extraction = self._observed_model_extraction(data)
        observed_models = observed_model_extraction["observed_models"]
        policy = self.policy_service.build_policy(observed_models=observed_models)
        selector = self.selector_service.build_selector({"observed_models": observed_models})
        catalog_items = catalog_for_api()
        model_rows = [self._model_row(item) for item in catalog_items]
        family_rows = self._family_rows(policy, model_rows)
        high_frequency_allowed = [row for row in model_rows if row["high_frequency_default_allowed"]]
        explicit_only_rows = [
            row
            for row in model_rows
            if row["route_role"] in {"balanced_retry", "premium_exception", "media_explicit"}
        ]
        preview_rows = [row for row in model_rows if row["catalog_status"] == "preview"]
        unpriced_rows = [row for row in model_rows if row["pricing_status"] == "unpriced"]
        observed_reviews = selector["observed_model_reviews"]
        catalog_review_rows = [row for row in observed_reviews if row["status"] == "catalog_review"]
        status = "review_required" if catalog_review_rows or unpriced_rows else "ready"

        return {
            "status": status,
            "method": {
                "type": "gemini-newapi-variant-routing-matrix",
                "notes": [
                    "Joins the local Gemini catalog, cheap-first policy, selector normalization, and configured role metadata.",
                    "Supports gateway-prefixed Gemini model ids while keeping unknown Gemini-like variants explicit-only until catalog review.",
                    "Does not call Gemini, NewAPI, OpenAI, the gateway, or any model.",
                ],
            },
            "summary": {
                "catalog_model_count": len(model_rows),
                "family_count": len(family_rows),
                "high_frequency_default_allowed_count": len(high_frequency_allowed),
                "explicit_only_model_count": len(explicit_only_rows),
                "preview_model_count": len(preview_rows),
                "unpriced_model_count": len(unpriced_rows),
                "observed_model_count": len(observed_reviews),
                "catalog_review_count": len(catalog_review_rows),
                "observed_model_candidate_count": observed_model_extraction["summary"]["candidate_count"],
                "accepted_observed_model_count": observed_model_extraction["summary"]["accepted_model_count"],
                "dropped_observed_model_count": observed_model_extraction["summary"]["dropped_model_count"],
                "rejected_sensitive_observed_model_count": observed_model_extraction["summary"][
                    "rejected_sensitive_count"
                ],
                "rejected_invalid_observed_model_count": observed_model_extraction["summary"].get(
                    "rejected_invalid_count", 0
                ),
                "rejected_observed_model_count": observed_model_extraction["summary"].get("rejected_model_count", 0),
                "observed_model_source_count": len(observed_model_extraction["summary"]["source_fields"]),
                "cheap_first_default_model": self.default_candidate_selector.recommended_model_for_task("fast"),
                "raw_payload_echoed": False,
            },
            "source_summaries": {
                "observed_model_extraction": observed_model_extraction["summary"],
            },
            "family_rows": family_rows,
            "model_rows": model_rows,
            "observed_model_reviews": observed_reviews,
            "prefix_compatibility": policy["newapi_openai_compatible_prefix_compatibility"],
            "unknown_model_policy": policy["unknown_gemini_like_model_handling"],
            "blocking_check_ids": [],
            "warning_check_ids": self._warning_ids(catalog_review_rows, unpriced_rows),
            "recommended_actions": self._recommended_actions(catalog_review_rows, unpriced_rows),
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "gateway_called": False,
                "output_scope": "metadata-only Gemini model ids, source-field names, families, cost tiers, route roles, prefix examples, and review statuses",
            },
            "validation_commands": [
                "python -m pytest tests/test_gemini_model_variant_matrix.py -q",
                "python -m pytest tests/test_model_catalog.py tests/test_gemini_newapi_cheap_first_policy.py tests/test_gemini_newapi_model_selector.py -q",
                "npm run typecheck",
            ],
        }

    def _model_row(self, item: dict[str, Any]) -> dict[str, Any]:
        model_id = str(item["id"])
        capabilities = [str(value) for value in item.get("capabilities", [])]
        route_role = self._route_role(item, capabilities)
        high_frequency_allowed = route_role == "cheap_first_default"
        return {
            "model_id": model_id,
            "family": self._family_label(model_id),
            "catalog_status": str(item.get("status") or "unknown"),
            "cost_tier": str(item.get("cost_tier") or "unknown"),
            "latency_tier": str(item.get("latency_tier") or "unknown"),
            "route_role": route_role,
            "high_frequency_default_allowed": high_frequency_allowed,
            "balanced_retry_allowed": route_role == "balanced_retry",
            "premium_exception_required": route_role == "premium_exception",
            "media_route_only": route_role == "media_explicit",
            "pricing_status": self._pricing_status(item),
            "configured_roles": list(item.get("configured_roles") or []),
            "capabilities": capabilities,
            "supported_request_shapes": [
                model_id,
                f"models/{model_id}",
                f"google/{model_id}",
                f"google:{model_id}",
            ],
            "review_note": self._review_note(route_role, item),
        }

    def _family_rows(self, policy: dict[str, Any], model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        counts_by_family = {
            family: sum(1 for row in model_rows if row["family"] == family)
            for family in sorted({row["family"] for row in model_rows})
        }
        for family in policy["supported_gemini_model_families"]:
            family_id = str(family["family"])
            rows.append(
                {
                    "family": family_id,
                    "catalog_model_count": counts_by_family.get(family_id, 0),
                    "cost_posture": family["cost_posture"],
                    "default_use": family["default_use"],
                    "high_frequency_default_allowed": family["high_frequency_default_allowed"],
                    "catalog_patterns": family["catalog_patterns"],
                    "catalog_models": family["catalog_models"],
                }
            )
        return rows

    def _observed_model_extraction(self, value: Any) -> dict[str, Any]:
        return extract_observed_model_ids(value)

    def _family_label(self, model_id: str) -> str:
        if model_id.startswith("veo-") or "video" in model_id:
            return "veo-video"
        if "tts" in model_id:
            return "gemini-tts"
        if "live" in model_id or "native-audio" in model_id:
            return "gemini-live-audio"
        if "embedding" in model_id:
            return "gemini-embedding"
        if "flash-lite" in model_id:
            return "gemini-flash-lite"
        if "flash" in model_id and "image" not in model_id:
            return "gemini-flash"
        if "pro" in model_id and "image" not in model_id:
            return "gemini-pro"
        if "image" in model_id:
            return "gemini-image"
        return "gemini-other"

    def _route_role(self, item: dict[str, Any], capabilities: list[str]) -> str:
        model_id = str(item["id"])
        status = str(item.get("status") or "")
        cost_tier = str(item.get("cost_tier") or "")
        media_capabilities = {
            "image",
            "video-generation",
            "audio-generation",
            "tts",
            "live",
            "transcription",
        }
        if "flash-lite" in model_id and cost_tier in {"lowest", "low"} and status == "stable":
            return "cheap_first_default"
        if media_capabilities.intersection(capabilities):
            return "media_explicit"
        if "flash" in model_id and status == "stable" and cost_tier in {"low", "medium"}:
            return "balanced_retry"
        if cost_tier == "premium" or status == "preview" or "pro" in model_id:
            return "premium_exception"
        return "explicit_only"

    def _pricing_status(self, item: dict[str, Any]) -> str:
        pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
        if pricing.get("output_usd_per_image") is not None:
            return "image_priced"
        if pricing.get("input_usd_per_million_tokens") is not None or pricing.get("output_usd_per_million_tokens") is not None:
            return "token_priced"
        return "unpriced"

    def _review_note(self, route_role: str, item: dict[str, Any]) -> str:
        if route_role == "cheap_first_default":
            return "Allowed as a high-volume default when the gateway supports this catalog id or accepted prefixes."
        if route_role == "balanced_retry":
            return "Use after cheap precheck or deterministic quality failure; do not make it the first high-volume default."
        if route_role == "premium_exception":
            return "Requires explicit operator or release-gate exception before use."
        if route_role == "media_explicit":
            return "Use only for explicit image/media routes."
        if str(item.get("status") or "") == "preview":
            return "Preview model requires catalog and stability review before default use."
        return "Explicit-only until cost, stability, and task fit are reviewed."

    def _warning_ids(self, catalog_review_rows: list[dict[str, Any]], unpriced_rows: list[dict[str, Any]]) -> list[str]:
        ids: list[str] = []
        if catalog_review_rows:
            ids.append("observed-gemini-like-catalog-review")
        if unpriced_rows:
            ids.append("catalog-unpriced-models")
        return ids

    def _recommended_actions(self, catalog_review_rows: list[dict[str, Any]], unpriced_rows: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Keep Flash-Lite as the first high-frequency default and escalate only after deterministic quality checks fail.",
            "Allow gateway-prefixed Gemini ids, but require catalog review before unknown Gemini-like variants become defaults.",
        ]
        if catalog_review_rows:
            actions.append("Review observed Gemini-like model ids before promoting them into APP_AI_* defaults.")
        if unpriced_rows:
            actions.append("Fill pricing metadata before using unpriced Gemini variants in cost forecasts or default recommendations.")
        return actions
