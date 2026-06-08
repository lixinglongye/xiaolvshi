from __future__ import annotations

from typing import Any

from services.model_ops_observed_gemini_coverage_gap_queue import (
    ModelOpsObservedGeminiCoverageGapQueueService,
)
from services.model_ops_observed_gemini_model_intake_queue import (
    ModelOpsObservedGeminiModelIntakeQueueService,
)


class ModelOpsObservedGeminiPremiumExceptionReviewService:
    """Build metadata-only review packets for observed premium Gemini variants."""

    def __init__(
        self,
        coverage_gap_queue_service: ModelOpsObservedGeminiCoverageGapQueueService | None = None,
        intake_queue_service: ModelOpsObservedGeminiModelIntakeQueueService | None = None,
    ) -> None:
        self.coverage_gap_queue_service = coverage_gap_queue_service or ModelOpsObservedGeminiCoverageGapQueueService()
        self.intake_queue_service = intake_queue_service or ModelOpsObservedGeminiModelIntakeQueueService()

    def build_review(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        intake = self.intake_queue_service.build_queue(data)
        coverage = self.coverage_gap_queue_service.build_queue(data)
        intake_items = [item for item in _list(intake.get("queue_items")) if isinstance(item, dict)]
        gap_ids_by_model = self._gap_ids_by_model(coverage)
        rows = [
            self._review_row(item, gap_ids_by_model.get(str(item.get("raw_model") or ""), []))
            for item in intake_items
            if self._is_premium_exception_candidate(item)
        ]
        blocked = [row for row in rows if row["review_status"] == "blocked"]
        rejected_model_count = _int(_dict(intake.get("summary")).get("source_rejected_observed_model_count"))
        status = (
            "blocked"
            if blocked or rejected_model_count
            else ("review_required" if rows else ("ready" if intake_items else "not_run"))
        )
        safety_checks = self._safety_checks(rows=rows, rejected_model_count=rejected_model_count)
        explicit_route_supported_count = sum(1 for row in rows if row["explicit_premium_route_supported"])

        return {
            "status": status,
            "method": {
                "type": "model-ops-observed-gemini-premium-exception-review",
                "notes": [
                    "Joins observed Gemini intake and coverage-gap evidence into a premium exception review packet.",
                    "Classifies observed Gemini Pro or premium variants as premium_exception_review.",
                    "Allows explicit premium routes only after maintainer review; it never changes defaults or calls gateways.",
                ],
            },
            "summary": {
                "observed_model_count": _int(_dict(intake.get("summary")).get("observed_model_count")),
                "premium_exception_review_count": len(rows),
                "premium_review_count": len(rows),
                "pro_variant_review_count": sum(1 for row in rows if row["pro_variant"]),
                "known_premium_model_count": sum(1 for row in rows if row["known_catalog_model"]),
                "blocked_review_count": len(blocked),
                "explicit_premium_route_supported_count": explicit_route_supported_count,
                "explicit_route_supported_count": explicit_route_supported_count,
                "default_blocked_count": sum(1 for row in rows if not row["high_frequency_default_allowed"]),
                "high_frequency_default_allowed_count": sum(
                    1 for row in rows if row["high_frequency_default_allowed"]
                ),
                "release_check_count": len(safety_checks),
                "blocking_check_count": sum(1 for check in safety_checks if check["status"] == "fail"),
                "automatic_configuration_change_allowed_count": sum(
                    1 for row in rows if row["automatic_configuration_change_allowed"]
                ),
                "source_rejected_observed_model_count": rejected_model_count,
                "source_rejected_sensitive_observed_model_count": _int(
                    _dict(intake.get("summary")).get("source_rejected_sensitive_observed_model_count")
                ),
                "source_rejected_invalid_observed_model_count": _int(
                    _dict(intake.get("summary")).get("source_rejected_invalid_observed_model_count")
                ),
                "configuration_written": False,
                "automatic_configuration_change_allowed": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
                "raw_model_output_included": False,
                "credentials_included": False,
            },
            "review_rows": rows,
            "premium_exception_review_model_ids": [row["raw_model"] for row in rows],
            "blocked_review_ids": [row["id"] for row in blocked],
            "safety_checks": safety_checks,
            "release_checks": safety_checks,
            "blocking_check_ids": [check["id"] for check in safety_checks if check["status"] == "fail"],
            "warning_check_ids": [check["id"] for check in safety_checks if check["status"] == "warn"],
            "recommended_actions": self._recommended_actions(
                rows=rows,
                blocked=blocked,
                rejected_model_count=rejected_model_count,
            ),
            "source_summaries": {
                "observed_gemini_model_intake_queue": intake.get("summary", {}),
                "observed_gemini_coverage_gap_queue": coverage.get("summary", {}),
            },
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "automatic_configuration_change_allowed": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "output_scope": (
                    "sanitized model ids, canonical ids, cost tiers, lifecycle labels, review states, "
                    "route boundary labels, and linked coverage-gap ids"
                ),
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "high_frequency_default_allowed_for_premium_claimed": False,
                "live_gateway_execution_claimed": False,
                "pricing_accuracy_claimed": False,
                "model_quality_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_observed_gemini_premium_exception_review.py -q",
                "python -m pytest tests/test_model_ops_observed_gemini_coverage_gap_queue.py tests/test_model_ops_observed_gemini_model_intake_queue.py -q",
            ],
        }

    def _review_row(self, item: dict[str, Any], linked_gap_ids: list[str]) -> dict[str, Any]:
        raw_model = str(item.get("raw_model") or "")
        canonical_model = str(item.get("canonical_model") or raw_model)
        reason_codes = self._reason_codes(item)
        known_catalog_model = bool(item.get("known_catalog_model"))
        blocked = str(item.get("intake_status")) == "blocked"
        allowed_route_modes = ["explicit_premium_exception"] if known_catalog_model and not blocked else []
        blocked_default_tasks = ["cheap", "fast", "ocr", "classification", "agentic", "grounded-research"]
        release_gate_links = _dedupe(
            [
                "modelops-observed-gemini-premium-exception-review",
                "modelops-observed-gemini-coverage-gap-queue",
                "modelops-observed-gemini-model-intake-queue",
                "gemini-model-variant-matrix",
                "model-ops-readiness",
                *linked_gap_ids,
            ]
        )
        return {
            "id": f"observed-gemini-premium-exception-{_safe_id(raw_model)}",
            "raw_model": raw_model,
            "canonical_model": canonical_model,
            "review_type": "premium_exception_review",
            "review_status": "blocked" if blocked else "review_required",
            "review_decision": "blocked" if blocked else "review_required",
            "release_action": (
                "block_premium_route_until_catalog_metadata_exists"
                if blocked
                else "allow_explicit_premium_route_after_maintainer_review"
            ),
            "intake_action": str(item.get("intake_action") or "premium_exception_review"),
            "intake_status": str(item.get("intake_status") or "review_required"),
            "known_catalog_model": known_catalog_model,
            "gemini_like": bool(item.get("gemini_like")),
            "pro_variant": "pro" in f"{raw_model} {canonical_model}".lower(),
            "cost_tier": str(item.get("cost_tier") or "unknown"),
            "model_lifecycle_status": str(item.get("model_lifecycle_status") or "unknown"),
            "pricing_status": str(item.get("pricing_status") or "unknown"),
            "capabilities": [str(value) for value in _list(item.get("capabilities"))],
            "review_reason_codes": reason_codes,
            "reason_codes": reason_codes,
            "explicit_premium_route_supported": known_catalog_model and not blocked,
            "allowed_route_modes": allowed_route_modes,
            "explicit_route_only": True,
            "high_frequency_default_allowed": False,
            "allowed_high_frequency_default_tasks": [],
            "blocked_default_tasks": blocked_default_tasks,
            "automatic_configuration_change_allowed": False,
            "gateway_call_required": False,
            "network_call_required": False,
            "linked_coverage_gap_ids": linked_gap_ids,
            "release_gate_links": release_gate_links,
            "required_approvals": [
                "model_ops_review",
                "cost_owner_review",
                "operator_premium_exception_approval",
            ],
            "recommended_action": (
                f"Keep {raw_model} explicit-only for premium exception routes; do not use it as a high-frequency default."
                if not blocked
                else f"Keep {raw_model} blocked until catalog metadata, pricing, and lifecycle evidence are complete."
            ),
        }

    def _reason_codes(self, item: dict[str, Any]) -> list[str]:
        raw_model = str(item.get("raw_model") or "")
        canonical_model = str(item.get("canonical_model") or raw_model)
        codes = ["premium-exception-review"]
        if "pro" in f"{raw_model} {canonical_model}".lower():
            codes.append("pro-variant")
        if str(item.get("cost_tier")) == "premium":
            codes.append("premium-cost-tier")
        if str(item.get("intake_status")) == "blocked":
            codes.append("catalog-or-pricing-block")
        codes.extend(str(code) for code in _list(item.get("reason_codes")) if code)
        return _dedupe(codes)

    def _is_premium_exception_candidate(self, item: dict[str, Any]) -> bool:
        if not bool(item.get("gemini_like")):
            return False
        model_text = f"{item.get('raw_model') or ''} {item.get('canonical_model') or ''}".lower()
        return (
            str(item.get("intake_action")) == "premium_exception_review"
            or str(item.get("cost_tier")) == "premium"
            or "pro" in model_text
        )

    def _gap_ids_by_model(self, coverage: dict[str, Any]) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        for gap in _list(coverage.get("gap_items")):
            if not isinstance(gap, dict):
                continue
            gap_id = str(gap.get("id") or "")
            for model_id in _list(gap.get("model_ids")):
                model_key = str(model_id or "")
                if not model_key:
                    continue
                mapping.setdefault(model_key, []).append(gap_id)
        return mapping

    def _safety_checks(self, *, rows: list[dict[str, Any]], rejected_model_count: int) -> list[dict[str, Any]]:
        return [
            {
                "id": "sanitized-observed-model-intake",
                "status": "fail" if rejected_model_count else "pass",
                "reason": (
                    "Rejected observed model metadata is present; rerun with sanitized model ids before approval."
                    if rejected_model_count
                    else "Observed model metadata was sanitized by the shared intake pipeline."
                ),
                "evidence": [f"rejected_model_count:{rejected_model_count}"],
            },
            {
                "id": "premium-explicit-route-boundary",
                "status": "warn" if rows else "pass",
                "reason": (
                    "Observed Pro or premium Gemini variants require explicit route approval."
                    if rows
                    else "No observed Pro or premium Gemini variants require exception review."
                ),
                "evidence": [row["id"] for row in rows],
            },
            {
                "id": "premium-high-frequency-default-block",
                "status": "pass",
                "reason": "Premium exception rows are never allowed as high-frequency defaults.",
                "evidence": [row["id"] for row in rows if not row["high_frequency_default_allowed"]],
            },
            {
                "id": "no-automatic-configuration-change",
                "status": "pass",
                "reason": "This packet cannot edit defaults, write configuration, shift traffic, or call gateways.",
                "evidence": [row["id"] for row in rows if not row["automatic_configuration_change_allowed"]],
            },
        ]

    def _recommended_actions(
        self,
        *,
        rows: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        rejected_model_count: int,
    ) -> list[str]:
        if rejected_model_count:
            return [
                "Remove sensitive or malformed observed model metadata before approving premium exceptions.",
                "Rerun the observed Gemini intake and premium exception review with sanitized gateway model ids only.",
            ]
        if blocked:
            return [
                "Block unknown or incomplete Pro/premium Gemini variants until catalog pricing and lifecycle metadata exist.",
                "Do not enable explicit premium routes for blocked rows.",
            ]
        if rows:
            return [
                "Keep observed Pro and premium Gemini variants explicit-only and operator-reviewed.",
                "Use Flash-Lite style models for high-frequency defaults unless a separate premium exception is approved.",
            ]
        return ["No observed Pro or premium Gemini variants require exception review."]


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-")[:96] or "unknown"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
