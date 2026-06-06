from __future__ import annotations

import re
from typing import Any

from services.gemini_newapi_observed_model_extraction import extract_observed_model_ids
from services.model_catalog import GEMINI_MODEL_CATALOG, canonical_model_id, model_profile


DEFAULT_PREFIXES = ("", "models/", "google/", "google:", "yibu/", "gemini/", "openrouter/google/")
REJECTED_MODEL_ID_PREFIX = "redacted-sensitive-model-id"
REJECTED_INVALID_MODEL_ID_PREFIX = "redacted-invalid-model-id"


class GeminiNewapiModelAliasMatrixService:
    """Build metadata-only evidence for Gemini model alias support."""

    def build_matrix(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        observed_aliases = self._observed_aliases(data)
        aliases = self._aliases(data, observed_aliases)
        rows = [self._row(alias, source="observed" if alias in observed_aliases else "catalog") for alias in aliases]
        known_rows = [row for row in rows if row["alias_status"] == "catalog_known"]
        review_rows = [row for row in rows if row["alias_status"] == "catalog_review"]
        external_rows = [row for row in rows if row["alias_status"] == "external_model"]
        rejected_rows = [row for row in rows if row["alias_status"] in {"rejected_sensitive", "rejected_invalid"}]
        high_frequency_rows = [row for row in rows if row["high_frequency_default_allowed"]]
        cheap_first_rows = [row for row in rows if row["cheap_first_candidate"]]
        premium_rows = [row for row in rows if row["premium_exception"]]

        return {
            "id": "gemini-newapi-model-alias-matrix",
            "title": "Gemini/NewAPI model alias matrix",
            "status": self._status(review_rows, external_rows, rejected_rows),
            "summary": {
                "alias_row_count": len(rows),
                "catalog_model_count": len(GEMINI_MODEL_CATALOG),
                "observed_model_count": len(observed_aliases),
                "known_alias_count": len(known_rows),
                "catalog_review_count": len(review_rows),
                "external_model_count": len(external_rows),
                "rejected_sensitive_count": sum(1 for row in rejected_rows if row["alias_status"] == "rejected_sensitive"),
                "rejected_invalid_count": sum(1 for row in rejected_rows if row["alias_status"] == "rejected_invalid"),
                "rejected_model_count": len(rejected_rows),
                "cheap_first_candidate_count": len(cheap_first_rows),
                "high_frequency_default_allowed_count": len(high_frequency_rows),
                "premium_exception_count": len(premium_rows),
                "canonical_catalog_count": len({row["canonical_model"] for row in known_rows if row["canonical_model"]}),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
                "credentials_included": False,
            },
            "alias_rows": rows,
            "accepted_alias_shapes": [
                "gemini-2.5-flash-lite",
                "models/gemini-2.5-flash-lite",
                "google/gemini-2.5-flash-lite",
                "google:gemini-2.5-flash-lite",
                "yibu/gemini-2.5-flash-lite",
                "gemini/gemini-2.5-flash-lite",
                "openrouter/google/gemini-2.5-flash-lite",
            ],
            "default_policy": {
                "high_frequency_default_rule": "Only stable Flash-Lite catalog aliases are high-frequency default candidates.",
                "balanced_route_rule": "Stable Flash or Flash-Lite aliases can support review routes after cheap precheck.",
                "premium_exception_rule": "Pro, preview, image, unknown, and external ids require explicit maintainer review before default use.",
                "unknown_gemini_like_policy": "Allow explicit-only experiments after catalog, price, lifecycle, and gateway review.",
                "configuration_write_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "credential_material_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "network_called": False,
                "gateway_called": False,
                "configuration_written": False,
                "output_scope": "sanitized model ids, canonical ids, alias shapes, status labels, cost tiers, reason codes, and default eligibility flags only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_yibu_account_validation_claimed": False,
                "automatic_default_change_claimed": False,
                "price_freshness_claimed": False,
                "production_quality_claimed": False,
            },
            "recommended_actions": self._recommended_actions(review_rows, external_rows, rejected_rows),
            "validation_commands": [
                "python -m pytest tests/test_gemini_newapi_model_alias_matrix.py tests/test_model_catalog.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _aliases(self, data: dict[str, Any], observed_aliases: list[str]) -> list[str]:
        aliases: list[str] = []
        if data.get("include_catalog_aliases", True) is not False:
            for profile in GEMINI_MODEL_CATALOG:
                for prefix in DEFAULT_PREFIXES:
                    aliases.append(f"{prefix}{profile.id}")
        aliases.extend(observed_aliases)
        return _dedupe([alias for alias in aliases if alias])

    def _observed_aliases(self, data: dict[str, Any]) -> list[str]:
        extraction = extract_observed_model_ids(data, max_model_ids=80)
        aliases = list(extraction["observed_models"])
        rejected_sensitive_count = int(extraction["summary"]["rejected_sensitive_count"])
        rejected_invalid_count = int(extraction["summary"].get("rejected_invalid_count") or 0)
        for index in range(1, rejected_sensitive_count + 1):
            aliases.append(f"{REJECTED_MODEL_ID_PREFIX}-{index}")
        for index in range(1, rejected_invalid_count + 1):
            aliases.append(f"{REJECTED_INVALID_MODEL_ID_PREFIX}-{index}")
        return aliases

    def _row(self, raw_model: str, *, source: str) -> dict[str, Any]:
        if (
            not raw_model
            or raw_model.startswith(REJECTED_MODEL_ID_PREFIX)
            or raw_model.startswith(REJECTED_INVALID_MODEL_ID_PREFIX)
        ):
            return self._rejected_row(raw_model)
        canonical = canonical_model_id(raw_model)
        profile = model_profile(raw_model) if canonical else None
        gemini_like = self._is_gemini_like(raw_model)
        alias_shape = self._alias_shape(raw_model)
        if profile:
            alias_status = "catalog_known"
            default_class = self._default_class(profile.id, profile.cost_tier, profile.status, profile.capabilities)
        elif gemini_like:
            alias_status = "catalog_review"
            default_class = "explicit_only_catalog_review"
        else:
            alias_status = "external_model"
            default_class = "ignore_for_gemini_defaults"
        reason_codes = self._reason_codes(alias_status, profile, alias_shape, default_class)
        return {
            "id": f"gemini-alias-{alias_shape}-{_slug(raw_model)}",
            "source": source,
            "alias_model": raw_model,
            "sanitized_model_id": raw_model,
            "canonical_model": canonical,
            "alias_shape": alias_shape,
            "alias_status": alias_status,
            "default_class": default_class,
            "known_catalog_model": bool(profile),
            "model_family": profile.family if profile else ("gemini" if gemini_like else "external"),
            "cost_tier": profile.cost_tier if profile else None,
            "lifecycle_status": profile.status if profile else "unknown",
            "cheap_first_candidate": default_class in {"high_frequency_default_candidate", "balanced_after_precheck_candidate"},
            "high_frequency_default_allowed": default_class == "high_frequency_default_candidate",
            "balanced_after_precheck_allowed": default_class in {
                "high_frequency_default_candidate",
                "balanced_after_precheck_candidate",
            },
            "premium_exception": default_class in {
                "premium_exception_review",
                "media_exception_review",
                "explicit_only_catalog_review",
            },
            "default_allowed_without_review": default_class == "high_frequency_default_candidate",
            "reason_codes": reason_codes,
            "recommended_action": self._recommended_action(default_class, alias_status),
            "configuration_write_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
        }

    def _rejected_row(self, raw_model: str | None = None) -> dict[str, Any]:
        safe_model_id = raw_model if raw_model else REJECTED_MODEL_ID_PREFIX
        invalid_input = safe_model_id.startswith(REJECTED_INVALID_MODEL_ID_PREFIX)
        return {
            "id": f"gemini-alias-{safe_model_id}",
            "source": "observed",
            "alias_model": safe_model_id,
            "sanitized_model_id": safe_model_id,
            "canonical_model": None,
            "alias_shape": "rejected_invalid" if invalid_input else "rejected_sensitive",
            "alias_status": "rejected_invalid" if invalid_input else "rejected_sensitive",
            "default_class": "blocked_invalid_input" if invalid_input else "blocked_sensitive_input",
            "known_catalog_model": False,
            "model_family": "unknown",
            "cost_tier": None,
            "lifecycle_status": "unknown",
            "cheap_first_candidate": False,
            "high_frequency_default_allowed": False,
            "balanced_after_precheck_allowed": False,
            "premium_exception": True,
            "default_allowed_without_review": False,
            "reason_codes": ["invalid-model-id-rejected" if invalid_input else "sensitive-model-id-rejected"],
            "recommended_action": (
                "Drop malformed model-id metadata and rerun with supported model id fields only."
                if invalid_input
                else "Drop sensitive model-id input and rerun with sanitized gateway /models metadata."
            ),
            "configuration_write_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
        }

    def _is_gemini_like(self, model_id: str) -> bool:
        value = (model_id or "").strip().lower()
        candidates = {value, value.rsplit("/", 1)[-1], value.rsplit(":", 1)[-1]}
        return any(candidate.startswith("gemini-") or "gemini-" in candidate for candidate in candidates)

    def _alias_shape(self, model_id: str) -> str:
        value = model_id.lower()
        if value.startswith("models/"):
            return "models_prefix"
        if value.startswith("google/"):
            return "google_slash_prefix"
        if value.startswith("google:"):
            return "google_colon_prefix"
        if value.startswith("yibu/"):
            return "yibu_slash_prefix"
        if value.startswith("gemini/"):
            return "gemini_slash_prefix"
        if "/google/" in value:
            return "nested_google_slash_prefix"
        if "/" in value:
            return "gateway_slash_prefix"
        if ":" in value:
            return "gateway_colon_prefix"
        return "canonical"

    def _default_class(
        self,
        model_id: str,
        cost_tier: str,
        status: str,
        capabilities: tuple[str, ...],
    ) -> str:
        if "image" in capabilities:
            return "media_exception_review"
        if status != "stable":
            return "premium_exception_review"
        if "flash-lite" in model_id and cost_tier in {"lowest", "low"}:
            return "high_frequency_default_candidate"
        if "flash" in model_id and cost_tier in {"lowest", "low", "medium"}:
            return "balanced_after_precheck_candidate"
        return "premium_exception_review"

    def _reason_codes(
        self,
        alias_status: str,
        profile: Any,
        alias_shape: str,
        default_class: str,
    ) -> list[str]:
        codes: list[str] = [f"alias-shape:{alias_shape}"]
        if alias_status != "catalog_known":
            codes.append(alias_status.replace("_", "-"))
        if profile:
            codes.append(f"cost-tier:{profile.cost_tier}")
            codes.append(f"lifecycle:{profile.status}")
        if default_class == "high_frequency_default_candidate":
            codes.append("flash-lite-cheap-first")
        elif default_class == "balanced_after_precheck_candidate":
            codes.append("balanced-after-cheap-precheck")
        elif default_class == "media_exception_review":
            codes.append("media-exception-review")
        elif default_class == "premium_exception_review":
            codes.append("premium-or-preview-review")
        elif default_class == "explicit_only_catalog_review":
            codes.append("explicit-only-until-catalog-review")
        else:
            codes.append("not-gemini-default-candidate")
        return codes

    def _recommended_action(self, default_class: str, alias_status: str) -> str:
        if default_class == "high_frequency_default_candidate":
            return "Allow as cheap-first high-frequency default if gateway compatibility evidence is current."
        if default_class == "balanced_after_precheck_candidate":
            return "Use after cheap precheck or as balanced review default with maintainer evidence."
        if default_class == "explicit_only_catalog_review":
            return "Keep explicit-only until catalog, price, lifecycle, and gateway compatibility evidence is added."
        if alias_status == "external_model":
            return "Ignore for Gemini defaults unless maintainers intentionally add a non-Gemini provider policy."
        return "Require maintainer review before default use."

    def _recommended_actions(
        self,
        review_rows: list[dict[str, Any]],
        external_rows: list[dict[str, Any]],
        rejected_rows: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Use stable Flash-Lite aliases as the first high-volume default candidates.",
            "Keep Pro, preview, media, unknown Gemini-like, and external ids explicit-only until maintainer review.",
            "Archive this alias matrix beside model selector and coverage-gate evidence before changing defaults.",
        ]
        if review_rows:
            actions.append("Add catalog pricing, lifecycle, and gateway compatibility metadata for unknown Gemini-like aliases.")
        if external_rows:
            actions.append("Separate non-Gemini gateway ids from Gemini default recommendations.")
        if rejected_rows:
            actions.append("Remove sensitive or malformed values from observed gateway metadata before review.")
        return actions

    def _status(
        self,
        review_rows: list[dict[str, Any]],
        external_rows: list[dict[str, Any]],
        rejected_rows: list[dict[str, Any]],
    ) -> str:
        if rejected_rows:
            return "needs_sanitization"
        if review_rows or external_rows:
            return "needs_catalog_review"
        return "ready"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "unknown"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
