from __future__ import annotations

import re
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_catalog import canonical_model_id, model_profile


SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization)",
    re.IGNORECASE,
)
FORBIDDEN_PAYLOAD_FIELD_PATTERN = re.compile(
    r"(authorization|api[_-]?key|app_ai_key|headers|messages|prompt|raw_output|"
    r"raw_response|response_text|output|outputs|image_url|image_urls|b64_json|base64)",
    re.IGNORECASE,
)
GEMINI_MODEL_ID_PATTERN = re.compile(r"(^|[:/_-])gemini([:/_-]|-\d|\d|\b)")
OFFICIAL_SOURCE_URLS = (
    "https://ai.google.dev/gemini-api/docs/models",
    "https://ai.google.dev/gemini-api/docs/pricing",
)


class ModelCatalogCandidatePatchPlanService:
    """Build review-only catalog patch candidates from sanitized observed model ids."""

    def build_plan(self, payload: Any = None, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        forbidden_payload_field_count = self._forbidden_payload_field_count(data)
        extraction = self._extract_model_ids(data, signals or {})
        rows = [self._review_row(model_id) for model_id in extraction["model_ids"]]
        candidate_patches = [row for row in rows if row["row_type"] == "candidate_patch"]
        existing_catalog_diffs = [row for row in rows if row["row_type"] == "existing_catalog_review"]
        external_ignores = [row for row in rows if row["row_type"] == "external_ignore"]
        cheap_first_candidates = [
            row for row in candidate_patches if row["cheap_first_candidate_status"] == "blocked_until_price_lifecycle_and_probe_pass"
        ]
        premium_candidates = [
            row for row in candidate_patches if row["cheap_first_candidate_status"] == "premium_or_preview_explicit_only"
        ]
        status = self._status(
            candidate_patches,
            external_ignores,
            extraction["rejected_sensitive_count"],
            forbidden_payload_field_count,
            rows,
        )
        checks = self._checks(
            rows,
            candidate_patches,
            external_ignores,
            extraction["rejected_sensitive_count"],
            forbidden_payload_field_count,
        )
        blocking_checks = [check for check in checks if check["status"] == "fail"]
        warning_checks = [check for check in checks if check["status"] == "warn"]

        return {
            "id": "model-catalog-candidate-patch-plan",
            "title": "Model catalog candidate patch plan",
            "status": status,
            "method": {
                "type": "model-catalog-candidate-patch-plan",
                "notes": [
                    "Turns sanitized observed Gemini-like model ids into manual catalog patch candidates.",
                    "Generates review stubs and required metadata checks only; it never edits model_catalog.py.",
                    "Uses local metadata and supplied sanitized model ids only; it never calls gateways or the network.",
                ],
                "source_urls": list(OFFICIAL_SOURCE_URLS),
            },
            "summary": {
                "observed_model_count": len(rows),
                "candidate_patch_count": len(candidate_patches),
                "add_count": len(candidate_patches),
                "update_count": len(existing_catalog_diffs),
                "review_required_count": len(candidate_patches) + len(external_ignores),
                "blocked_count": extraction["rejected_sensitive_count"] + forbidden_payload_field_count,
                "pricing_watch_count": len(candidate_patches),
                "existing_catalog_review_count": len(existing_catalog_diffs),
                "external_ignore_count": len(external_ignores),
                "cheap_first_candidate_count": len(cheap_first_candidates),
                "premium_or_preview_candidate_count": len(premium_candidates),
                "rejected_sensitive_count": extraction["rejected_sensitive_count"],
                "forbidden_payload_field_count": forbidden_payload_field_count,
                "candidate_patch_written": False,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
            },
            "candidate_patch_rows": candidate_patches,
            "candidate_patches": candidate_patches,
            "existing_catalog_diffs": existing_catalog_diffs,
            "external_model_ignores": external_ignores,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking_checks],
            "warning_check_ids": [check["id"] for check in warning_checks],
            "manual_source_review": {
                "required": bool(candidate_patches),
                "source_urls": list(OFFICIAL_SOURCE_URLS),
                "required_checks": [
                    "official_model_list_review",
                    "pricing_source_review",
                    "lifecycle_status_review",
                    "capability_review",
                    "gateway_probe_review",
                    "cheap_first_policy_review",
                ],
            },
            "recommended_actions": self._recommended_actions(
                candidate_patches,
                external_ignores,
                extraction["rejected_sensitive_count"],
                forbidden_payload_field_count,
                rows,
            ),
            "privacy_boundary": {
                "metadata_only": True,
                "candidate_patch_written": False,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "sanitized model ids, proposed catalog ids, required metadata checks, status labels, and maintainer action labels only",
            },
            "claim_boundary": {
                "automatic_catalog_edit_claimed": False,
                "automatic_default_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "pricing_accuracy_claimed": False,
                "model_quality_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_catalog_candidate_patch_plan.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_model_gateway_probe_evaluation.py -q",
                "python -m pytest tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _review_row(self, model_id: str) -> dict[str, Any]:
        canonical = canonical_model_id(model_id)
        profile = model_profile(model_id)
        gemini_like = self._is_gemini_like(model_id)
        if profile:
            return self._existing_catalog_row(model_id, canonical or profile.id, profile)
        if gemini_like:
            return self._candidate_patch_row(model_id)
        return {
            "id": f"catalog-candidate-ignore-{_safe_id(model_id)}",
            "row_type": "external_ignore",
            "observed_model": model_id,
            "model_id": model_id,
            "proposed_catalog_id": None,
            "catalog_action": "ignore_non_gemini_model",
            "patch_action": "ignore_non_gemini_model",
            "default_promotion_state": "not_applicable",
            "release_action": "exclude_from_gemini_default_candidates",
            "recommended_action": "Keep this non-Gemini id outside Gemini catalog and default-routing review.",
            "candidate_patch_written": False,
            "gateway_call_allowed": False,
        }

    def _existing_catalog_row(self, observed_model: str, canonical_model: str, profile: Any) -> dict[str, Any]:
        pricing_status = self._pricing_status(profile)
        cheap_first_allowed = (
            "flash-lite" in profile.id
            and profile.status == "stable"
            and COST_TIER_RANK.get(profile.cost_tier, 99) <= COST_TIER_RANK.get("low", 99)
            and pricing_status == "token_priced"
        )
        return {
            "id": f"catalog-existing-{_safe_id(observed_model)}",
            "row_type": "existing_catalog_review",
            "observed_model": observed_model,
            "model_id": observed_model,
            "canonical_model": canonical_model,
            "known_catalog_model": True,
            "catalog_action": "no_catalog_patch_required",
            "patch_action": "no_catalog_patch_required",
            "cost_tier": profile.cost_tier,
            "latency_tier": profile.latency_tier,
            "source_url": profile.pricing_source_url,
            "lifecycle_status": profile.status,
            "catalog_status": profile.status,
            "pricing_status": pricing_status,
            "cheap_first_default_allowed": cheap_first_allowed,
            "default_allowed_for_high_frequency": cheap_first_allowed,
            "manual_review_required": profile.status != "stable" or not cheap_first_allowed,
            "requires_operator_review": profile.status != "stable" or not cheap_first_allowed,
            "release_action": "no_catalog_patch_required",
            "recommended_action": self._existing_recommendation(profile, cheap_first_allowed),
            "candidate_patch_written": False,
            "gateway_call_allowed": False,
        }

    def _candidate_patch_row(self, observed_model: str) -> dict[str, Any]:
        proposed_catalog_id = self._candidate_catalog_id(observed_model)
        profile_stub = self._profile_stub(proposed_catalog_id)
        cheap_first_status = self._cheap_first_candidate_status(proposed_catalog_id)
        return {
            "id": f"catalog-candidate-{_safe_id(proposed_catalog_id)}",
            "row_type": "candidate_patch",
            "observed_model": observed_model,
            "model_id": proposed_catalog_id,
            "proposed_catalog_id": proposed_catalog_id,
            "known_catalog_model": False,
            "catalog_action": "manual_model_profile_candidate",
            "patch_action": "add_manual_model_profile_candidate",
            "proposed_profile_stub": profile_stub,
            "catalog_status": "missing",
            "cost_tier": "unknown",
            "latency_tier": "unknown",
            "source_url": OFFICIAL_SOURCE_URLS[0],
            "pricing_status": "unknown",
            "default_allowed_for_high_frequency": False,
            "requires_operator_review": True,
            "required_metadata_checks": [
                "official_model_list_review",
                "pricing_source_review",
                "lifecycle_status_review",
                "capability_review",
                "gateway_probe_review",
                "cheap_first_policy_review",
            ],
            "cheap_first_candidate_status": cheap_first_status,
            "default_promotion_state": "blocked_until_candidate_review_passes",
            "release_action": "require_catalog_patch_review_before_default_change",
            "candidate_patch_written": False,
            "gateway_call_allowed": False,
            "reason": self._candidate_recommendation(proposed_catalog_id, cheap_first_status),
            "recommended_action": self._candidate_recommendation(proposed_catalog_id, cheap_first_status),
        }

    def _profile_stub(self, proposed_catalog_id: str) -> dict[str, Any]:
        capabilities = ["text", "json"]
        if "image" in proposed_catalog_id:
            capabilities = ["image"]
        elif "vision" in proposed_catalog_id:
            capabilities.append("vision")
        if "ground" in proposed_catalog_id:
            capabilities.append("grounding")
        return {
            "id": proposed_catalog_id,
            "provider": "google",
            "family": "gemini",
            "cost_tier": "unknown",
            "latency_tier": "unknown",
            "capabilities": _dedupe(capabilities),
            "best_for": ["review_required"],
            "status": "review_required",
            "input_usd_per_million_tokens": None,
            "output_usd_per_million_tokens": None,
            "output_usd_per_image": None,
            "pricing_source_url": OFFICIAL_SOURCE_URLS[1],
            "notes": "Candidate only; maintainers must verify model list, pricing, lifecycle, capabilities, and gateway probe evidence before editing model_catalog.py.",
        }

    def _candidate_catalog_id(self, observed_model: str) -> str:
        value = observed_model.lower().strip()
        value = value.rsplit("/", 1)[-1]
        value = value.rsplit(":", 1)[-1]
        return re.sub(r"[^a-z0-9_.-]+", "-", value).strip("-") or "unknown-gemini-model"

    def _cheap_first_candidate_status(self, proposed_catalog_id: str) -> str:
        if "pro" in proposed_catalog_id or "preview" in proposed_catalog_id or "image" in proposed_catalog_id:
            return "premium_or_preview_explicit_only"
        if "flash-lite" in proposed_catalog_id:
            return "blocked_until_price_lifecycle_and_probe_pass"
        if "flash" in proposed_catalog_id:
            return "balanced_route_review_only"
        return "explicit_only_until_catalog_review"

    def _existing_recommendation(self, profile: Any, cheap_first_allowed: bool) -> str:
        if cheap_first_allowed:
            return "No catalog patch is required; keep this stable Flash-Lite model eligible for cheap-first defaults."
        if profile.status != "stable":
            return "No catalog patch is required, but keep this model explicit-only until lifecycle review passes."
        if "image" in profile.capabilities:
            return "No catalog patch is required; keep media routes separated from high-frequency text defaults."
        return "No catalog patch is required; use after cheap-first precheck or explicit maintainer review."

    def _candidate_recommendation(self, proposed_catalog_id: str, cheap_first_status: str) -> str:
        if cheap_first_status == "blocked_until_price_lifecycle_and_probe_pass":
            return (
                f"Prepare {proposed_catalog_id} for maintainer review only after official pricing, lifecycle, "
                "capabilities, and gateway probe evidence are attached."
            )
        if cheap_first_status == "balanced_route_review_only":
            return f"Review {proposed_catalog_id} as a balanced route candidate, not a high-frequency default."
        if cheap_first_status == "premium_or_preview_explicit_only":
            return f"Keep {proposed_catalog_id} explicit-only unless premium/preview review approves a narrow exception."
        return f"Keep {proposed_catalog_id} explicit-only until catalog metadata is complete."

    def _pricing_status(self, profile: Any) -> str:
        if profile.output_usd_per_image is not None:
            return "image_priced"
        if profile.input_usd_per_million_tokens is not None and profile.output_usd_per_million_tokens is not None:
            return "token_priced"
        if profile.input_usd_per_million_tokens is not None or profile.output_usd_per_million_tokens is not None:
            return "partial_token_priced"
        return "missing"

    def _extract_model_ids(self, data: dict[str, Any], signals: dict[str, Any]) -> dict[str, Any]:
        values = [
            *self._extract_from_payload(data),
            *self._extract_from_signals(signals),
        ]
        seen: set[str] = set()
        model_ids: list[str] = []
        rejected_sensitive_count = 0
        for value in values[:120]:
            safe = self._safe_model_id(value)
            if not safe:
                rejected_sensitive_count += 1
                continue
            if safe in seen:
                continue
            seen.add(safe)
            model_ids.append(safe)
        return {
            "model_ids": model_ids[:80],
            "rejected_sensitive_count": rejected_sensitive_count,
        }

    def _extract_from_payload(self, data: dict[str, Any]) -> list[Any]:
        values: list[Any] = []
        for key in ("model_ids", "observed_models"):
            rows = data.get(key)
            if isinstance(rows, list):
                values.extend(rows)
        response = data.get("models_response")
        if isinstance(response, list):
            values.extend(response)
        elif isinstance(response, dict):
            for key in ("data", "models", "items"):
                rows = response.get(key)
                if isinstance(rows, list):
                    values.extend(rows)
        for key in ("gateway_probe_evaluation", "observed_gemini_model_intake_queue"):
            values.extend(self._extract_from_signal(data.get(key)))
        return values

    def _extract_from_signals(self, signals: dict[str, Any]) -> list[Any]:
        values: list[Any] = []
        for key in ("gateway_probe_evaluation", "observed_gemini_model_intake_queue"):
            values.extend(self._extract_from_signal(signals.get(key)))
        return values

    def _extract_from_signal(self, value: Any) -> list[Any]:
        if not isinstance(value, dict):
            return []
        values: list[Any] = []
        rows = value.get("model_rows")
        if isinstance(rows, list):
            values.extend(row.get("model") for row in rows if isinstance(row, dict))
        queue_items = value.get("queue_items")
        if isinstance(queue_items, list):
            values.extend(row.get("raw_model") or row.get("observed_model") for row in queue_items if isinstance(row, dict))
        return values

    def _safe_model_id(self, value: Any) -> str | None:
        if isinstance(value, dict):
            for key in ("id", "model", "name"):
                if isinstance(value.get(key), str):
                    value = value[key]
                    break
            else:
                return None
        if not isinstance(value, str):
            return None
        raw = value.strip().lower()[:180]
        if not raw or SENSITIVE_VALUE_PATTERN.search(raw):
            return None
        return re.sub(r"[^a-z0-9_.:/-]+", "-", raw).strip("-") or None

    def _forbidden_payload_field_count(self, value: Any) -> int:
        return min(20, len(self._forbidden_payload_hits(value)))

    def _forbidden_payload_hits(self, value: Any) -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if FORBIDDEN_PAYLOAD_FIELD_PATTERN.search(str(key)):
                    hits.append("redacted_forbidden_field")
                    continue
                hits.extend(self._forbidden_payload_hits(child))
                if len(hits) >= 20:
                    return hits[:20]
        elif isinstance(value, list):
            for child in value[:40]:
                hits.extend(self._forbidden_payload_hits(child))
                if len(hits) >= 20:
                    return hits[:20]
        elif isinstance(value, str) and SENSITIVE_VALUE_PATTERN.search(value[:4096]):
            hits.append("redacted_sensitive_value")
        return hits[:20]

    def _is_gemini_like(self, model_id: str) -> bool:
        lowered = model_id.lower()
        if "not-gemini" in lowered or "non-gemini" in lowered:
            return False
        return bool(GEMINI_MODEL_ID_PATTERN.search(lowered))

    def _status(
        self,
        candidate_patches: list[dict[str, Any]],
        external_ignores: list[dict[str, Any]],
        rejected_sensitive_count: int,
        forbidden_payload_field_count: int,
        rows: list[dict[str, Any]],
    ) -> str:
        if rejected_sensitive_count or forbidden_payload_field_count:
            return "blocked"
        if candidate_patches:
            return "review_required"
        if external_ignores:
            return "review_required"
        if rows:
            return "ready"
        return "not_run"

    def _recommended_actions(
        self,
        candidate_patches: list[dict[str, Any]],
        external_ignores: list[dict[str, Any]],
        rejected_sensitive_count: int,
        forbidden_payload_field_count: int,
        rows: list[dict[str, Any]],
    ) -> list[str]:
        if rejected_sensitive_count or forbidden_payload_field_count:
            return [
                "Discard sensitive or raw probe payload values and resubmit sanitized model ids only.",
                "Do not use this plan to edit the catalog until sanitization passes.",
            ]
        if candidate_patches:
            return [
                "Open manual catalog review for candidate Gemini ids before editing model_catalog.py.",
                "Attach official model list, pricing, lifecycle, capability, and gateway probe evidence.",
                "Keep unknown Gemini-like ids explicit-only until the candidate review passes.",
            ]
        if external_ignores and not rows:
            return ["Submit sanitized Gemini-like model ids before catalog review."]
        if external_ignores:
            return ["Ignore non-Gemini ids for Gemini catalog defaults and keep known catalog rows unchanged."]
        if rows:
            return ["No catalog patch candidates are needed for the supplied known Gemini catalog ids."]
        return ["Submit sanitized gateway /models metadata or observed Gemini model ids before planning catalog patches."]

    def _checks(
        self,
        rows: list[dict[str, Any]],
        candidate_patches: list[dict[str, Any]],
        external_ignores: list[dict[str, Any]],
        rejected_sensitive_count: int,
        forbidden_payload_field_count: int,
    ) -> list[dict[str, str]]:
        return [
            {
                "id": "sanitized-model-metadata-only",
                "status": "fail" if rejected_sensitive_count or forbidden_payload_field_count else "pass",
                "reason": "Sensitive or raw probe payload values were rejected."
                if rejected_sensitive_count or forbidden_payload_field_count
                else "Payload is limited to sanitized model metadata.",
            },
            {
                "id": "observed-models-present",
                "status": "pass" if rows else "warn",
                "reason": f"Reviewed {len(rows)} sanitized model ids." if rows else "Submit sanitized observed model ids.",
            },
            {
                "id": "candidate-patch-review",
                "status": "warn" if candidate_patches else "pass",
                "reason": f"{len(candidate_patches)} unknown Gemini-like ids require manual catalog candidate review."
                if candidate_patches
                else "No unknown Gemini-like catalog candidates were found.",
            },
            {
                "id": "external-models-ignored",
                "status": "warn" if external_ignores else "pass",
                "reason": f"{len(external_ignores)} non-Gemini ids are excluded from Gemini catalog defaults."
                if external_ignores
                else "No non-Gemini ids were supplied.",
            },
            {
                "id": "no-automatic-catalog-edit",
                "status": "pass",
                "reason": "The plan does not write model_catalog.py, .env, templates, or runtime configuration.",
            },
        ]


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:96] or "unknown"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
