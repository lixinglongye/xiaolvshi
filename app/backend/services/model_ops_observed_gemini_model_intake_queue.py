from __future__ import annotations

import re
from typing import Any

from services.gemini_model_variant_matrix import GeminiModelVariantMatrixService
from services.model_budget import COST_TIER_RANK
from services.model_catalog import model_profile


HIGH_FREQUENCY_DEFAULT_TASKS = ("cheap", "fast", "ocr", "classification")
GEMINI_MODEL_ID_PATTERN = re.compile(r"(^|[:/_-])gemini([:/_-]|-\d|\d|\b)")


class ModelOpsObservedGeminiModelIntakeQueueService:
    """Review observed Gemini-like model ids before they become defaults."""

    def __init__(self, variant_matrix_service: GeminiModelVariantMatrixService | None = None) -> None:
        self.variant_matrix_service = variant_matrix_service or GeminiModelVariantMatrixService()

    def build_queue(self, payload: Any = None) -> dict[str, Any]:
        matrix = self.variant_matrix_service.build_matrix(payload)
        observed_rows = matrix.get("observed_model_reviews", [])
        queue_items = [self._queue_item(row) for row in observed_rows if isinstance(row, dict)]
        blocked = [item for item in queue_items if item["intake_status"] == "blocked"]
        review = [item for item in queue_items if item["intake_status"] == "review_required"]
        ready = [item for item in queue_items if item["intake_status"] == "ready"]
        source_summary = matrix["source_summaries"]["observed_model_extraction"]
        rejected_model_count = int(source_summary.get("rejected_model_count") or 0)
        rejected_sensitive_count = int(source_summary.get("rejected_sensitive_count") or 0)
        rejected_invalid_count = int(source_summary.get("rejected_invalid_count") or 0)
        cheap_first_ready = [item for item in queue_items if item["cheap_first_default_candidate"]]
        unknown_gemini = [item for item in queue_items if item["intake_action"] == "catalog_metadata_review"]
        external = [item for item in queue_items if item["intake_action"] == "ignore_non_gemini"]
        safety_checks = self._promotion_safety_checks(
            blocked=blocked,
            review=review,
            ready=ready,
            cheap_first_ready=cheap_first_ready,
            rejected_model_count=rejected_model_count,
            rejected_sensitive_count=rejected_sensitive_count,
            rejected_invalid_count=rejected_invalid_count,
        )
        blocking_checks = [check for check in safety_checks if check["status"] == "fail"]
        warning_checks = [check for check in safety_checks if check["status"] == "warn"]
        intake_runbook_steps = self._intake_runbook_steps(
            status=(
                "blocked"
                if blocked or rejected_model_count
                else ("review_required" if review else ("ready" if queue_items else "not_run"))
            ),
            blocked=blocked,
            review=review,
            cheap_first_ready=cheap_first_ready,
            rejected_model_count=rejected_model_count,
        )

        return {
            "status": (
                "blocked"
                if blocked or rejected_model_count
                else ("review_required" if review else ("ready" if queue_items else "not_run"))
            ),
            "method": {
                "type": "model-ops-observed-gemini-model-intake-queue",
                "notes": [
                    "Converts sanitized observed gateway model ids into a default-promotion intake queue.",
                    "Known stable Flash-Lite/low-cost models can become cheap-first candidates; unknown, preview, premium, or unpriced variants require review.",
                    "Uses local catalog and variant matrix metadata only; it never calls NewAPI, Gemini, OpenAI, Google, gateways, or the network.",
                ],
            },
            "summary": {
                "observed_model_count": len(queue_items),
                "ready_count": len(ready),
                "review_required_count": len(review),
                "blocked_count": len(blocked) + rejected_model_count,
                "cheap_first_candidate_count": len(cheap_first_ready),
                "unknown_gemini_count": len(unknown_gemini),
                "external_non_gemini_count": len(external),
                "source_catalog_review_count": matrix["summary"]["catalog_review_count"],
                "source_accepted_observed_model_count": matrix["summary"]["accepted_observed_model_count"],
                "source_dropped_observed_model_count": matrix["summary"]["dropped_observed_model_count"],
                "source_rejected_sensitive_observed_model_count": rejected_sensitive_count,
                "source_rejected_invalid_observed_model_count": rejected_invalid_count,
                "source_rejected_observed_model_count": rejected_model_count,
                "promotion_safety_check_count": len(safety_checks),
                "promotion_safety_blocking_count": len(blocking_checks),
                "promotion_safety_warning_count": len(warning_checks),
                "intake_runbook_step_count": len(intake_runbook_steps),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
            },
            "queue_items": queue_items,
            "ready_model_ids": [item["raw_model"] for item in ready],
            "review_model_ids": [item["raw_model"] for item in review],
            "blocked_model_ids": [item["raw_model"] for item in blocked],
            "cheap_first_candidate_summary": {
                "candidate_model_ids": [item["raw_model"] for item in cheap_first_ready],
                "candidate_count": len(cheap_first_ready),
                "default_task_scope": list(HIGH_FREQUENCY_DEFAULT_TASKS),
                "review_required_model_ids": [item["raw_model"] for item in review],
                "blocked_model_ids": [item["raw_model"] for item in blocked],
                "external_model_ids": [item["raw_model"] for item in external],
                "safe_to_enter_default_change_queue": bool(cheap_first_ready) and not blocked and not rejected_model_count,
            },
            "promotion_safety_checks": safety_checks,
            "blocking_check_ids": [check["id"] for check in blocking_checks],
            "warning_check_ids": [check["id"] for check in warning_checks],
            "intake_runbook_steps": intake_runbook_steps,
            "recommended_actions": self._recommended_actions(
                blocked,
                review,
                ready,
                cheap_first_ready,
                rejected_model_count,
            ),
            "source_summaries": {
                "variant_matrix": matrix["summary"],
                "observed_model_extraction": matrix["source_summaries"]["observed_model_extraction"],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "output_scope": "sanitized model ids, canonical ids, cost tier, lifecycle status, queue status, and release action metadata",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "pricing_accuracy_claimed": False,
                "model_quality_claimed": False,
                "public_benchmark_scores_included": False,
                "ready_candidates_are_auto_promoted": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_gemini_model_variant_matrix.py -q",
                "python -m pytest tests/test_model_gateway_probe_evaluation.py tests/test_model_ops_readiness.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _queue_item(self, row: dict[str, Any]) -> dict[str, Any]:
        raw_model = str(row.get("raw_model") or "")
        canonical_model = row.get("canonical_model")
        profile = model_profile(str(canonical_model or raw_model))
        intake_action = self._intake_action(row, profile)
        reason_codes = self._reason_codes(row, profile, intake_action)
        intake_status = self._intake_status(reason_codes)
        cheap_first_candidate = intake_status == "ready" and bool(row.get("default_allowed_for_high_frequency"))
        return {
            "id": f"observed-gemini-intake-{_safe_id(raw_model)}",
            "raw_model": raw_model,
            "canonical_model": canonical_model,
            "catalog_status": row.get("status") or "unknown",
            "intake_status": intake_status,
            "intake_action": intake_action,
            "release_action": self._release_action(intake_status, intake_action),
            "known_catalog_model": profile is not None,
            "gemini_like": _is_gemini_like(raw_model),
            "cost_tier": row.get("cost_tier") or (profile.cost_tier if profile else "unknown"),
            "model_lifecycle_status": profile.status if profile else "unknown",
            "default_allowed_for_high_frequency": bool(row.get("default_allowed_for_high_frequency")),
            "cheap_first_default_candidate": cheap_first_candidate,
            "allowed_default_tasks": list(HIGH_FREQUENCY_DEFAULT_TASKS) if cheap_first_candidate else [],
            "capabilities": list(profile.capabilities) if profile else [],
            "pricing_status": self._pricing_status(profile),
            "reason_codes": reason_codes,
            "warnings": [str(item) for item in row.get("warnings", []) if item],
        }

    def _promotion_safety_checks(
        self,
        *,
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        ready: list[dict[str, Any]],
        cheap_first_ready: list[dict[str, Any]],
        rejected_model_count: int,
        rejected_sensitive_count: int,
        rejected_invalid_count: int,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "sanitized-model-id-intake",
                "status": "fail" if rejected_model_count else "pass",
                "reason": (
                    "Rejected sensitive or malformed model metadata is present; do not promote defaults."
                    if rejected_model_count
                    else "Observed model ids passed the shared metadata-only sanitizer."
                ),
                "evidence": [
                    f"rejected_sensitive:{rejected_sensitive_count}",
                    f"rejected_invalid:{rejected_invalid_count}",
                ],
            },
            {
                "id": "unknown-gemini-default-block",
                "status": "fail" if blocked else "pass",
                "reason": (
                    "Unknown or unpriced Gemini-like models remain explicit-only until catalog metadata exists."
                    if blocked
                    else "No unknown Gemini-like model is eligible for default promotion."
                ),
                "evidence": [item["id"] for item in blocked],
            },
            {
                "id": "review-only-model-boundary",
                "status": "warn" if review else "pass",
                "reason": (
                    "Preview, premium, media, balanced, or non-Gemini rows require maintainer review before default work."
                    if review
                    else "No review-only observed model is queued for default promotion."
                ),
                "evidence": [item["id"] for item in review],
            },
            {
                "id": "cheap-first-candidate-boundary",
                "status": "pass" if cheap_first_ready or not ready else "warn",
                "reason": (
                    "Ready candidates are limited to stable low-cost Gemini models for high-frequency task scope."
                    if cheap_first_ready
                    else (
                        "Ready rows exist but none are cheap-first default candidates."
                        if ready
                        else "No ready observed Gemini candidates were submitted."
                    )
                ),
                "evidence": [item["id"] for item in cheap_first_ready],
            },
        ]

    def _intake_runbook_steps(
        self,
        *,
        status: str,
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        cheap_first_ready: list[dict[str, Any]],
        rejected_model_count: int,
    ) -> list[dict[str, Any]]:
        steps = [
            {
                "id": "submit-sanitized-model-list",
                "step_order": 1,
                "owner": "maintainer",
                "step_status": "blocked" if rejected_model_count else "ready",
                "action": "Paste only sanitized /v1/models ids or model-list JSON into the observed Gemini intake evaluator.",
                "depends_on": [],
                "release_gate_links": ["gemini-variant-matrix", "observed-gemini-model-intake-queue"],
                "validation_commands": [
                    "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py -q",
                ],
            },
            {
                "id": "catalog-metadata-review",
                "step_order": 2,
                "owner": "model-ops",
                "step_status": "blocked" if blocked else ("review_required" if review else "ready"),
                "action": (
                    "Add or refresh source-backed catalog metadata before any unknown, preview, premium, or media model is used as a default."
                    if blocked or review
                    else "Catalog metadata is sufficient for the submitted observed Gemini defaults."
                ),
                "depends_on": ["submit-sanitized-model-list"],
                "release_gate_links": ["catalog-source-audit", "catalog-candidate-patch-plan"],
                "validation_commands": [
                    "python -m pytest tests/test_model_catalog_source_audit.py tests/test_model_catalog_candidate_patch_plan.py -q",
                ],
            },
            {
                "id": "selector-replay-before-default-change",
                "step_order": 3,
                "owner": "model-ops",
                "step_status": "blocked" if blocked or rejected_model_count else ("ready" if cheap_first_ready else "review_required"),
                "action": (
                    "Run selector replay and impact replay before moving cheap-first candidates into default-change review."
                    if cheap_first_ready
                    else "Keep observed models in review until at least one stable low-cost Gemini candidate exists."
                ),
                "depends_on": ["catalog-metadata-review"],
                "release_gate_links": ["gemini-newapi-selector-replay", "catalog-candidate-impact-replay"],
                "validation_commands": [
                    "python -m pytest tests/test_gemini_newapi_selector_replay.py tests/test_model_catalog_candidate_impact_replay.py -q",
                ],
            },
            {
                "id": "default-change-and-canary-review",
                "step_order": 4,
                "owner": "maintainer",
                "step_status": "blocked" if status == "blocked" else ("ready" if cheap_first_ready and not review else "review_required"),
                "action": (
                    "Only after replay passes, use the default-change queue, canary plan, approval packet, rollback drill, and change manifest."
                    if cheap_first_ready
                    else "Do not edit defaults; rerun intake after catalog and selector evidence is ready."
                ),
                "depends_on": ["selector-replay-before-default-change"],
                "release_gate_links": [
                    "default-change-queue",
                    "cheap-first-canary-plan",
                    "cheap-first-maintainer-execution-checklist",
                ],
                "validation_commands": [
                    "python -m pytest tests/test_model_ops_default_change_queue.py tests/test_model_ops_cheap_first_maintainer_execution_checklist.py -q",
                ],
            },
        ]
        return steps

    def _intake_action(self, row: dict[str, Any], profile: Any) -> str:
        raw_model = str(row.get("raw_model") or "")
        if not _is_gemini_like(raw_model):
            return "ignore_non_gemini"
        if profile is None:
            return "catalog_metadata_review"
        if profile.status != "stable":
            return "lifecycle_review"
        if profile.output_usd_per_image is not None and "image" in profile.capabilities:
            return "media_route_review"
        if COST_TIER_RANK.get(profile.cost_tier, 99) <= COST_TIER_RANK.get("low", 99):
            return "cheap_first_candidate_review"
        if COST_TIER_RANK.get(profile.cost_tier, 99) <= COST_TIER_RANK.get("medium", 99):
            return "balanced_retry_review"
        return "premium_exception_review"

    def _reason_codes(self, row: dict[str, Any], profile: Any, intake_action: str) -> list[str]:
        codes: list[str] = []
        raw_model = str(row.get("raw_model") or "")
        if intake_action == "ignore_non_gemini":
            codes.append("non-gemini-model-ignored")
        if _is_gemini_like(raw_model) and profile is None:
            codes.append("unknown-gemini-catalog-metadata")
        if profile and profile.status != "stable":
            codes.append(f"lifecycle-{profile.status}")
        if profile and self._pricing_status(profile) == "unpriced":
            codes.append("price-metadata-missing")
        if profile and COST_TIER_RANK.get(profile.cost_tier, 99) > COST_TIER_RANK.get("low", 99):
            codes.append("not-cheap-first-default")
        if row.get("warnings"):
            codes.append("variant-matrix-warning")
        if bool(row.get("default_allowed_for_high_frequency")):
            codes.append("cheap-first-default-candidate")
        return _dedupe(codes) or ["intake-ready"]

    def _intake_status(self, reason_codes: list[str]) -> str:
        if "unknown-gemini-catalog-metadata" in reason_codes:
            return "blocked"
        if "price-metadata-missing" in reason_codes and "cheap-first-default-candidate" in reason_codes:
            return "blocked"
        review_only = {
            "lifecycle-preview",
            "lifecycle-review",
            "price-metadata-missing",
            "not-cheap-first-default",
            "variant-matrix-warning",
            "non-gemini-model-ignored",
        }
        if any(code in review_only for code in reason_codes):
            return "review_required"
        return "ready"

    def _release_action(self, intake_status: str, intake_action: str) -> str:
        if intake_status == "ready":
            return "eligible_for_default_change_review"
        if intake_status == "blocked":
            return "block_default_promotion_until_catalog_metadata_exists"
        if intake_action == "ignore_non_gemini":
            return "exclude_from_gemini_default_candidates"
        return "require_maintainer_review_before_default_promotion"

    def _pricing_status(self, profile: Any) -> str:
        if profile is None:
            return "unknown"
        if profile.output_usd_per_image is not None:
            return "image_priced"
        if profile.input_usd_per_million_tokens is not None or profile.output_usd_per_million_tokens is not None:
            return "token_priced"
        return "unpriced"

    def _recommended_actions(
        self,
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        ready: list[dict[str, Any]],
        cheap_first_ready: list[dict[str, Any]],
        rejected_model_count: int = 0,
    ) -> list[str]:
        if rejected_model_count:
            return [
                "Do not promote observed model ids until sensitive or malformed model metadata is removed from the intake payload.",
                "Rerun the shared observed-model extractor and intake queue with sanitized gateway /models metadata only.",
            ]
        if blocked:
            return [
                "Do not promote unknown or unpriced Gemini-like gateway ids into defaults until catalog pricing and lifecycle metadata are added.",
                "Keep blocked models explicit-only and rerun gateway probe/variant matrix review after metadata refresh.",
            ]
        if review:
            return [
                "Review preview, premium, image, medium-cost, or non-Gemini rows before default-change proposals.",
                "Use ready cheap-first candidates only after validation commands pass and maintainer approval is recorded.",
            ]
        if cheap_first_ready:
            return [
                "Ready cheap-first candidates can move to Gemini default change review before any .env/template edit.",
                "Keep Flash-Lite style models first for high-volume tasks unless quality evidence requires escalation.",
            ]
        if ready:
            return ["Observed models are ready for default-change review; rerun after any gateway or catalog change."]
        return ["Submit sanitized observed Gemini model ids before changing default models."]


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")[:96] or "unknown"


def _is_gemini_like(value: str) -> bool:
    lowered = value.lower()
    if "not-gemini" in lowered or "non-gemini" in lowered:
        return False
    return bool(GEMINI_MODEL_ID_PATTERN.search(lowered))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
