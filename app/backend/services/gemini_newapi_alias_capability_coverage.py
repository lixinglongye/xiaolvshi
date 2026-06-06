from __future__ import annotations

import re
from typing import Any

from services import model_catalog
from services.gemini_newapi_model_alias_matrix import DEFAULT_PREFIXES, REJECTED_MODEL_ID_PREFIX
from services.gemini_newapi_observed_model_extraction import extract_observed_model_ids
from services.model_catalog import ModelProfile
from services.model_default_candidate_selector import TASK_POLICIES, normalize_task


EXTRA_PREFIXES = (
    "yibu:",
    "yibuapi/",
    "yibuapi/google/",
    "newapi/",
    "newapi/google/",
    "openai/gemini/",
    "publishers/google/models/",
)
ACTION_SUFFIXES = ("", "@latest", "@stable", ":generateContent", ":streamGenerateContent")


class GeminiNewapiAliasCapabilityCoverageService:
    """Explain Gemini/NewAPI alias shape capability coverage without gateway calls."""

    def build_coverage(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        include_catalog_aliases = data.get("include_catalog_aliases", True) is not False
        observed_model_extraction = extract_observed_model_ids(data, max_candidates=80, max_model_ids=80)
        rows = self._catalog_rows() if include_catalog_aliases else []
        rows.extend(self._observed_rows(observed_model_extraction))
        known_rows = [row for row in rows if row["coverage_status"] == "covered"]
        external_rows = [row for row in rows if row["coverage_status"] == "external"]
        review_rows = [row for row in rows if row["coverage_status"] == "review_required"] + external_rows
        blocked_rows = [row for row in rows if row["coverage_status"] == "blocked"]
        capability_totals = self._capability_totals(known_rows)
        task_totals = self._task_totals(known_rows)

        return {
            "id": "gemini-newapi-alias-capability-coverage",
            "title": "Gemini/NewAPI alias capability coverage",
            "status": "blocked" if blocked_rows else ("review_required" if review_rows else "ready"),
            "method": {
                "type": "metadata-only-gemini-newapi-alias-capability-coverage",
                "notes": [
                    "Expands local Gemini catalog models through common OpenAI-compatible gateway alias shapes.",
                    "Checks whether each alias shape still resolves to catalog capability metadata after prefix, suffix, and action normalization.",
                    "Classifies cheap-first default eligibility by task capability, lifecycle, and cost metadata only.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, yibuapi, gateways, or the network.",
                ],
            },
            "summary": {
                "coverage_row_count": len(rows),
                "catalog_model_count": len(model_catalog.GEMINI_MODEL_CATALOG),
                "alias_shape_count": len({row["alias_shape"] for row in rows}),
                "known_coverage_count": len(known_rows),
                "review_required_count": len(review_rows),
                "external_model_count": len(external_rows),
                "blocked_count": len(blocked_rows),
                "cheap_first_high_frequency_alias_count": sum(1 for row in known_rows if row["high_frequency_default_allowed"]),
                "balanced_after_precheck_alias_count": sum(1 for row in known_rows if row["balanced_after_precheck_allowed"]),
                "premium_or_media_review_alias_count": sum(1 for row in rows if row["premium_or_media_review_required"]),
                "text_json_capable_alias_count": capability_totals["text_json"],
                "vision_ocr_capable_alias_count": capability_totals["vision_ocr"],
                "grounding_capable_alias_count": capability_totals["grounding"],
                "agentic_capable_alias_count": capability_totals["agentic"],
                "image_capable_alias_count": capability_totals["image"],
                "covered_task_count": len([task for task, count in task_totals.items() if count]),
                "high_frequency_task_count": len([task for task in task_totals if TASK_POLICIES[task].high_frequency]),
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
                "observed_model_extractor_version": observed_model_extraction["summary"]["extractor_version"],
                "raw_payload_echoed": False,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
            },
            "coverage_rows": rows,
            "capability_totals": capability_totals,
            "task_alias_coverage": [
                {
                    "task": task,
                    "alias_count": count,
                    "high_frequency": TASK_POLICIES[task].high_frequency,
                    "route_mode": TASK_POLICIES[task].route_mode,
                    "status": "covered" if count else "gap",
                }
                for task, count in task_totals.items()
            ],
            "accepted_alias_shapes": self._accepted_alias_examples(),
            "coverage_policy": {
                "cheap_first_rule": "Stable token-priced Flash-Lite aliases with required task capabilities can be high-frequency cheap-first defaults.",
                "balanced_rule": "Stable low/medium Flash aliases can support review/document routes after cheap precheck.",
                "premium_rule": "Pro, preview, image, media, unknown, unpriced, and external aliases require explicit maintainer review.",
                "observed_unknown_rule": "Observed Gemini-like aliases that do not resolve to catalog metadata remain explicit-only until price, lifecycle, capability, and gateway evidence pass.",
            },
            "source_summaries": {
                "observed_model_extraction": observed_model_extraction["summary"],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "output_scope": "sanitized model aliases, canonical catalog ids, capabilities, task labels, status labels, and no-write/no-call flags only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_yibu_account_validation_claimed": False,
                "automatic_default_change_claimed": False,
                "pricing_accuracy_claimed": False,
                "production_quality_claimed": False,
                "public_benchmark_score_claimed": False,
            },
            "recommended_actions": self._recommended_actions(review_rows, blocked_rows),
            "validation_commands": [
                "python -m pytest tests/test_gemini_newapi_alias_capability_coverage.py tests/test_model_catalog.py -q",
                "python -m pytest tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_model_selector.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _catalog_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        prefixes = (*DEFAULT_PREFIXES, *EXTRA_PREFIXES)
        for profile in model_catalog.GEMINI_MODEL_CATALOG:
            for prefix in prefixes:
                for suffix in ACTION_SUFFIXES:
                    alias = f"{prefix}{profile.id}{suffix}"
                    rows.append(self._row(alias, source="catalog", profile=profile))
        return rows

    def _observed_rows(self, extraction: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        observed_models = extraction.get("observed_models", [])
        if not isinstance(observed_models, list):
            observed_models = []
        for safe_alias in observed_models[:80]:
            canonical = model_catalog.canonical_model_id(safe_alias)
            profile = model_catalog.model_profile(canonical) if canonical else None
            rows.append(self._row(safe_alias, source="observed", profile=profile))
        summary = extraction.get("summary", {})
        rejected_sensitive = int(summary.get("rejected_sensitive_count") or 0)
        rejected_invalid = int(summary.get("rejected_invalid_count") or 0)
        for index in range(1, rejected_sensitive + 1):
            rows.append(self._blocked_row(index, reason="sensitive"))
        for index in range(1, rejected_invalid + 1):
            rows.append(self._blocked_row(index, reason="invalid"))
        return rows

    def _row(self, alias: str, *, source: str, profile: ModelProfile | None) -> dict[str, Any]:
        canonical = model_catalog.canonical_model_id(alias)
        gemini_like = self._is_gemini_like(alias)
        status = "covered" if profile and canonical else ("review_required" if gemini_like else "external")
        task_coverage = self._task_coverage(profile)
        high_frequency_default_allowed = bool(
            profile
            and profile.status == "stable"
            and profile.cost_tier in {"lowest", "low"}
            and "flash-lite" in profile.id
            and any(TASK_POLICIES[task].high_frequency for task in task_coverage)
        )
        balanced_after_precheck_allowed = bool(
            profile
            and profile.status == "stable"
            and profile.cost_tier in {"lowest", "low", "medium"}
            and "text" in profile.capabilities
            and "json" in profile.capabilities
            and "image" not in profile.capabilities
        )
        premium_or_media_review = bool(
            not profile
            or profile.status != "stable"
            or profile.cost_tier == "premium"
            or "image" in (profile.capabilities if profile else ())
        )
        return {
            "id": f"gemini-alias-capability-{_slug(alias)}",
            "source": source,
            "alias_model": alias,
            "canonical_model": canonical,
            "alias_shape": self._alias_shape(alias),
            "coverage_status": status,
            "known_catalog_model": bool(profile and canonical),
            "model_family": profile.family if profile else ("gemini" if gemini_like else "external"),
            "cost_tier": profile.cost_tier if profile else "unknown",
            "latency_tier": profile.latency_tier if profile else "unknown",
            "lifecycle_status": profile.status if profile else "unknown",
            "capabilities": list(profile.capabilities) if profile else [],
            "covered_tasks": task_coverage,
            "covered_high_frequency_tasks": [task for task in task_coverage if TASK_POLICIES[task].high_frequency],
            "high_frequency_default_allowed": high_frequency_default_allowed,
            "balanced_after_precheck_allowed": balanced_after_precheck_allowed,
            "premium_or_media_review_required": premium_or_media_review,
            "default_allowed_without_review": high_frequency_default_allowed,
            "reason_codes": self._reason_codes(profile, status, high_frequency_default_allowed, premium_or_media_review),
            "recommended_action": self._recommended_action(status, high_frequency_default_allowed, premium_or_media_review),
        }

    def _blocked_row(self, index: int, *, reason: str = "sensitive") -> dict[str, Any]:
        sensitive = reason == "sensitive"
        alias_model = (
            f"{REJECTED_MODEL_ID_PREFIX}-{index}" if sensitive else f"redacted-invalid-model-id-{index}"
        )
        return {
            "id": f"gemini-alias-capability-{alias_model}",
            "source": "observed",
            "alias_model": alias_model,
            "canonical_model": None,
            "alias_shape": "rejected_sensitive" if sensitive else "rejected_invalid",
            "coverage_status": "blocked",
            "known_catalog_model": False,
            "model_family": "unknown",
            "cost_tier": "unknown",
            "latency_tier": "unknown",
            "lifecycle_status": "unknown",
            "capabilities": [],
            "covered_tasks": [],
            "covered_high_frequency_tasks": [],
            "high_frequency_default_allowed": False,
            "balanced_after_precheck_allowed": False,
            "premium_or_media_review_required": True,
            "default_allowed_without_review": False,
            "reason_codes": ["sensitive-alias-rejected" if sensitive else "invalid-alias-rejected"],
            "recommended_action": (
                "Remove sensitive observed model values and resubmit sanitized gateway model ids only."
                if sensitive
                else "Remove malformed observed model values and resubmit supported model id metadata only."
            ),
        }

    def _task_coverage(self, profile: ModelProfile | None) -> list[str]:
        if not profile:
            return []
        tasks: list[str] = []
        for task, policy in TASK_POLICIES.items():
            if all(capability in profile.capabilities for capability in policy.required_capabilities):
                tasks.append(normalize_task(task))
        return _dedupe(tasks)

    def _capability_totals(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "text_json": sum(1 for row in rows if {"text", "json"}.issubset(set(row["capabilities"]))),
            "vision_ocr": sum(1 for row in rows if {"vision", "ocr"}.issubset(set(row["capabilities"]))),
            "grounding": sum(1 for row in rows if "grounding" in row["capabilities"]),
            "agentic": sum(1 for row in rows if "agentic" in row["capabilities"]),
            "image": sum(1 for row in rows if "image" in row["capabilities"]),
        }

    def _task_totals(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        totals = {task: 0 for task in TASK_POLICIES}
        for row in rows:
            for task in row["covered_tasks"]:
                totals[task] = totals.get(task, 0) + 1
        return totals

    def _accepted_alias_examples(self) -> list[str]:
        model_id = "gemini-2.5-flash-lite"
        return [
            model_id,
            f"models/{model_id}",
            f"google/{model_id}",
            f"google:{model_id}",
            f"yibu/{model_id}",
            f"yibu:{model_id}",
            f"yibuapi/google/{model_id}",
            f"newapi/google/{model_id}",
            f"openrouter/google/{model_id}",
            f"publishers/google/models/{model_id}:generateContent",
        ]

    def _alias_shape(self, alias: str) -> str:
        value = alias.lower()
        if value.startswith("publishers/google/models/"):
            return "google_publishers_models"
        if value.startswith("newapi/google/"):
            return "newapi_google_slash_prefix"
        if value.startswith("newapi/"):
            return "newapi_slash_prefix"
        if value.startswith("yibuapi/google/"):
            return "yibuapi_google_slash_prefix"
        if value.startswith("yibuapi/"):
            return "yibuapi_slash_prefix"
        if value.startswith("yibu:"):
            return "yibu_colon_prefix"
        if value.endswith(":generatecontent") or value.endswith(":streamgeneratecontent"):
            return "action_suffix"
        if value.endswith("@latest") or value.endswith("@stable"):
            return "lifecycle_suffix"
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

    def _reason_codes(
        self,
        profile: ModelProfile | None,
        status: str,
        high_frequency_default_allowed: bool,
        premium_or_media_review: bool,
    ) -> list[str]:
        if status == "blocked":
            return ["blocked-sensitive-input"]
        if not profile:
            return ["catalog-review-required" if status == "review_required" else "non-gemini-external-model"]
        codes = [f"cost-tier:{profile.cost_tier}", f"lifecycle:{profile.status}"]
        if high_frequency_default_allowed:
            codes.append("cheap-first-high-frequency-covered")
        if premium_or_media_review:
            codes.append("explicit-review-before-default")
        if "grounding" in profile.capabilities:
            codes.append("grounding-capable")
        if "agentic" in profile.capabilities:
            codes.append("agentic-capable")
        return codes

    def _recommended_action(
        self,
        status: str,
        high_frequency_default_allowed: bool,
        premium_or_media_review: bool,
    ) -> str:
        if status == "blocked":
            return "Discard sensitive observed value and rerun with sanitized model metadata."
        if status == "review_required":
            return "Keep explicit-only until catalog, price, lifecycle, capability, and gateway evidence is added."
        if status == "external":
            return "Ignore for Gemini defaults unless a non-Gemini provider policy is added."
        if high_frequency_default_allowed:
            return "Candidate can remain in the cheap-first default ladder when gateway compatibility evidence is current."
        if premium_or_media_review:
            return "Keep explicit-only or operator-approved because this alias is premium, preview, or media-specific."
        return "Use after cheap precheck where task capability and quality gates require it."

    def _recommended_actions(
        self,
        review_rows: list[dict[str, Any]],
        blocked_rows: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Keep stable Flash-Lite aliases first for high-volume routing, classification, OCR, and cheap prechecks.",
            "Use the task coverage table before enabling unknown Gemini aliases from yibuapi or other OpenAI-compatible gateways.",
            "Keep this coverage packet metadata-only; do not paste API keys, prompts, legal documents, or gateway responses.",
        ]
        if review_rows:
            actions.append("Add catalog metadata and gateway compatibility evidence for review-required Gemini-like aliases.")
        if blocked_rows:
            actions.append("Remove sensitive observed model values before alias capability review.")
        return actions

    def _is_gemini_like(self, alias: str) -> bool:
        value = (alias or "").strip().lower()
        if "not-gemini" in value or "non-gemini" in value:
            return False
        return "gemini-" in value


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:96] or "unknown"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
