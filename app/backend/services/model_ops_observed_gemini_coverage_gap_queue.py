from __future__ import annotations

from typing import Any

from services.gemini_model_variant_matrix import GeminiModelVariantMatrixService
from services.model_ops_observed_gemini_model_intake_queue import (
    ModelOpsObservedGeminiModelIntakeQueueService,
)


HIGH_FREQUENCY_DEFAULT_TASKS = ("cheap", "fast", "ocr", "classification")
REVIEWED_FAMILY_IDS = ("gemini-flash-lite", "gemini-flash", "gemini-pro", "gemini-image")


class ModelOpsObservedGeminiCoverageGapQueueService:
    """Summarize observed Gemini model intake into family and task coverage gaps."""

    def __init__(
        self,
        variant_matrix_service: GeminiModelVariantMatrixService | None = None,
        intake_queue_service: ModelOpsObservedGeminiModelIntakeQueueService | None = None,
    ) -> None:
        self.variant_matrix_service = variant_matrix_service or GeminiModelVariantMatrixService()
        self.intake_queue_service = intake_queue_service or ModelOpsObservedGeminiModelIntakeQueueService()

    def build_queue(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        matrix = self.variant_matrix_service.build_matrix(data)
        intake = self.intake_queue_service.build_queue(data)
        intake_items = [item for item in _list(intake.get("queue_items")) if isinstance(item, dict)]
        family_rows = self._family_rows(matrix, intake_items)
        task_rows = self._task_rows(matrix, intake_items)
        gap_items = self._gap_items(family_rows, task_rows, intake_items)
        blocking = [item for item in gap_items if item["severity"] == "fail"]
        review = [item for item in gap_items if item["severity"] == "warn"]
        observed_count = _int(_dict(intake.get("summary")).get("observed_model_count"))
        status = "not_run" if observed_count <= 0 else ("blocked" if blocking else ("review_required" if review else "ready"))

        return {
            "status": status,
            "method": {
                "type": "model-ops-observed-gemini-coverage-gap-queue",
                "notes": [
                    "Converts sanitized observed Gemini model intake into family and high-frequency task coverage gaps.",
                    "Keeps cheap Flash-Lite candidates first for high-volume tasks and sends unknown, unpriced, preview, premium, and media variants to review.",
                    "Uses local catalog, variant matrix, and observed-model extraction metadata only; it never calls NewAPI, Gemini, OpenAI, Google, gateways, or the network.",
                ],
            },
            "summary": {
                "observed_model_count": observed_count,
                "family_row_count": len(family_rows),
                "covered_family_count": sum(1 for row in family_rows if row["coverage_status"] == "covered"),
                "family_gap_count": sum(1 for row in family_rows if row["coverage_status"] != "covered"),
                "high_frequency_task_count": len(task_rows),
                "cheap_first_task_covered_count": sum(1 for row in task_rows if row["coverage_status"] == "covered"),
                "cheap_first_task_gap_count": sum(1 for row in task_rows if row["coverage_status"] != "covered"),
                "gap_item_count": len(gap_items),
                "blocking_gap_count": len(blocking),
                "review_gap_count": len(review),
                "ready_cheap_first_candidate_count": sum(
                    1 for item in intake_items if bool(item.get("cheap_first_default_candidate"))
                ),
                "blocked_model_count": sum(1 for item in intake_items if str(item.get("intake_status")) == "blocked"),
                "review_model_count": sum(1 for item in intake_items if str(item.get("intake_status")) == "review_required"),
                "unknown_gemini_count": sum(1 for item in intake_items if "unknown-gemini-catalog-metadata" in _list(item.get("reason_codes"))),
                "unpriced_model_count": sum(1 for item in intake_items if str(item.get("pricing_status")) == "unpriced"),
                "preview_model_count": sum(1 for item in intake_items if str(item.get("model_lifecycle_status")) == "preview"),
                "media_review_count": sum(1 for item in intake_items if str(item.get("intake_action")) == "media_route_review"),
                "external_non_gemini_count": sum(1 for item in intake_items if not bool(item.get("gemini_like"))),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
            },
            "family_rows": family_rows,
            "high_frequency_task_rows": task_rows,
            "gap_items": gap_items,
            "blocking_gap_ids": [item["id"] for item in blocking],
            "review_gap_ids": [item["id"] for item in review],
            "recommended_actions": self._recommended_actions(status, blocking, review, task_rows),
            "source_summaries": {
                "gemini_variant_matrix": matrix.get("summary", {}),
                "observed_gemini_model_intake_queue": intake.get("summary", {}),
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
                "output_scope": "sanitized model ids, canonical ids, family labels, task labels, counts, statuses, and maintainer actions",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "all_gemini_models_supported_claimed": False,
                "live_gateway_execution_claimed": False,
                "pricing_accuracy_claimed": False,
                "model_quality_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_observed_gemini_coverage_gap_queue.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_gemini_model_variant_matrix.py -q",
                "python -m pytest tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _family_rows(self, matrix: dict[str, Any], intake_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for family in _list(matrix.get("family_rows")):
            if not isinstance(family, dict):
                continue
            family_id = str(family.get("family") or "gemini-other")
            if family_id not in REVIEWED_FAMILY_IDS:
                continue
            observed = [item for item in intake_items if _family_label(str(item.get("canonical_model") or item.get("raw_model") or "")) == family_id]
            ready = [item for item in observed if bool(item.get("cheap_first_default_candidate"))]
            blocked = [item for item in observed if str(item.get("intake_status")) == "blocked"]
            review = [item for item in observed if str(item.get("intake_status")) == "review_required"]
            catalog_count = _int(family.get("catalog_model_count"))
            coverage_status = "covered" if observed else ("missing_catalog_family" if catalog_count <= 0 else "missing_observed_family")
            rows.append(
                {
                    "family": family_id,
                    "coverage_status": coverage_status,
                    "catalog_model_count": catalog_count,
                    "observed_model_count": len(observed),
                    "ready_cheap_first_candidate_count": len(ready),
                    "blocked_model_count": len(blocked),
                    "review_required_model_count": len(review),
                    "high_frequency_default_allowed": bool(family.get("high_frequency_default_allowed")),
                    "default_use": str(family.get("default_use") or "review-only"),
                    "observed_models": sorted(str(item.get("raw_model") or "") for item in observed),
                    "recommended_action": self._family_action(family_id, coverage_status, ready, blocked, review),
                }
            )
        return rows

    def _task_rows(self, matrix: dict[str, Any], intake_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        catalog_candidates = [
            row
            for row in _list(matrix.get("model_rows"))
            if isinstance(row, dict) and bool(row.get("high_frequency_default_allowed"))
        ]
        rows: list[dict[str, Any]] = []
        for task in HIGH_FREQUENCY_DEFAULT_TASKS:
            candidates = [
                item
                for item in intake_items
                if bool(item.get("cheap_first_default_candidate")) and task in _list(item.get("allowed_default_tasks"))
            ]
            coverage_status = "covered" if candidates else ("catalog_only" if catalog_candidates else "missing_candidate")
            rows.append(
                {
                    "task": task,
                    "coverage_status": coverage_status,
                    "ready_candidate_count": len(candidates),
                    "catalog_candidate_count": len(catalog_candidates),
                    "candidate_models": sorted(str(item.get("raw_model") or "") for item in candidates),
                    "recommended_action": self._task_action(task, coverage_status),
                }
            )
        return rows

    def _gap_items(
        self,
        family_rows: list[dict[str, Any]],
        task_rows: list[dict[str, Any]],
        intake_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for item in intake_items:
            status = str(item.get("intake_status"))
            if status not in {"blocked", "review_required"}:
                continue
            severity = "fail" if status == "blocked" else "warn"
            raw_model = str(item.get("raw_model") or "unknown")
            items.append(
                self._gap_item(
                    gap_id=f"observed-gemini-model-{_safe_id(raw_model)}",
                    title=f"Review observed Gemini model: {raw_model}",
                    severity=severity,
                    priority=92 if severity == "fail" else 66,
                    gap_type="observed_model_intake",
                    scope=raw_model,
                    coverage_status=status,
                    model_ids=[raw_model],
                    reason_codes=_list(item.get("reason_codes")),
                    recommended_action=self._observed_model_action(item),
                )
            )
        for row in task_rows:
            if row["coverage_status"] == "covered":
                continue
            items.append(
                self._gap_item(
                    gap_id=f"cheap-first-task-{row['task']}",
                    title=f"Cover cheap-first task: {row['task']}",
                    severity="warn",
                    priority=74,
                    gap_type="high_frequency_task_coverage",
                    scope=row["task"],
                    coverage_status=row["coverage_status"],
                    model_ids=row["candidate_models"],
                    reason_codes=["cheap-first-observed-candidate-missing"],
                    recommended_action=row["recommended_action"],
                )
            )
        for row in family_rows:
            if row["coverage_status"] == "covered":
                continue
            items.append(
                self._gap_item(
                    gap_id=f"gemini-family-{row['family']}",
                    title=f"Observe Gemini family: {row['family']}",
                    severity="warn",
                    priority=58,
                    gap_type="gemini_family_coverage",
                    scope=row["family"],
                    coverage_status=row["coverage_status"],
                    model_ids=row["observed_models"],
                    reason_codes=["gemini-family-observation-missing"],
                    recommended_action=row["recommended_action"],
                )
            )
        return sorted(items, key=lambda item: (-item["priority"], item["id"]))

    def _gap_item(
        self,
        *,
        gap_id: str,
        title: str,
        severity: str,
        priority: int,
        gap_type: str,
        scope: str,
        coverage_status: str,
        model_ids: list[str],
        reason_codes: list[str],
        recommended_action: str,
    ) -> dict[str, Any]:
        return {
            "id": f"observed-gemini-coverage-{gap_id}",
            "title": title,
            "severity": severity,
            "priority": priority,
            "gap_type": gap_type,
            "scope": scope,
            "coverage_status": coverage_status,
            "model_ids": model_ids,
            "reason_codes": reason_codes,
            "recommended_action": recommended_action,
            "owner": "model_ops",
            "release_gate_links": [
                "modelops-observed-gemini-coverage-gap-queue",
                "modelops-observed-gemini-model-intake-queue",
                "gemini-model-variant-matrix",
                "model-ops-readiness",
            ],
            "evidence_paths": [
                "app/backend/services/model_ops_observed_gemini_coverage_gap_queue.py",
                "app/backend/services/model_ops_observed_gemini_model_intake_queue.py",
                "app/backend/services/gemini_model_variant_matrix.py",
            ],
            "validation_commands": [
                "python -m pytest tests/test_model_ops_observed_gemini_coverage_gap_queue.py -q",
            ],
        }

    def _family_action(
        self,
        family_id: str,
        coverage_status: str,
        ready: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
    ) -> str:
        if coverage_status != "covered":
            return f"Add sanitized observed model-list evidence for {family_id} before claiming broad Gemini variant coverage."
        if blocked:
            return f"Catalog or price blocked {family_id} models before they enter default-candidate review."
        if review:
            return f"Review lifecycle, media, or premium boundaries for observed {family_id} models."
        if ready:
            return f"{family_id} has an observed cheap-first candidate for high-volume routing review."
        return f"{family_id} is observed but remains explicit-only until task fit and pricing are reviewed."

    def _task_action(self, task: str, coverage_status: str) -> str:
        if coverage_status == "covered":
            return f"Keep observed Flash-Lite style candidate available for {task}."
        if coverage_status == "catalog_only":
            return f"Observe a gateway-supported Flash-Lite style model before claiming {task} cheap-first coverage."
        return f"Add a priced stable Flash-Lite style catalog candidate before promoting {task} defaults."

    def _observed_model_action(self, item: dict[str, Any]) -> str:
        reason_codes = {str(code) for code in _list(item.get("reason_codes"))}
        raw_model = str(item.get("raw_model") or "observed Gemini model")
        if "unknown-gemini-catalog-metadata" in reason_codes:
            return f"Block {raw_model} from defaults until catalog, pricing, lifecycle, and family metadata exist."
        if "price-metadata-missing" in reason_codes:
            return f"Block {raw_model} from defaults until pricing metadata is complete."
        if any(code.startswith("lifecycle-") for code in reason_codes):
            return f"Review preview lifecycle risk for {raw_model} before any default-promotion proposal."
        if str(item.get("intake_action")) == "media_route_review":
            return f"Review media-only routing for {raw_model}; do not use it to close text cheap-first coverage."
        if "not-cheap-first-default" in reason_codes:
            return f"Review premium or non-cheap Gemini routing for {raw_model} before default promotion."
        if "non-gemini-model-ignored" in reason_codes:
            return f"Keep {raw_model} out of Gemini default candidates."
        return str(item.get("release_action") or "Review observed Gemini model before default promotion.")

    def _recommended_actions(
        self,
        status: str,
        blocking: list[dict[str, Any]],
        review: list[dict[str, Any]],
        task_rows: list[dict[str, Any]],
    ) -> list[str]:
        if status == "not_run":
            return ["Submit sanitized observed Gemini model ids before claiming gateway family or cheap-first task coverage."]
        if blocking:
            return [
                "Block default promotion for unknown, unpriced, or malformed observed Gemini-like models until catalog metadata is refreshed.",
                "Rerun observed-model intake and this coverage gap queue after catalog pricing and lifecycle review.",
            ]
        task_gaps = [row for row in task_rows if row["coverage_status"] != "covered"]
        if task_gaps:
            return [
                "Keep Flash-Lite style models first for high-volume tasks, but collect observed gateway evidence for uncovered tasks.",
                "Do not use premium or preview models to close cheap-first task coverage without maintainer approval.",
            ]
        if review:
            return ["Review premium, preview, media, or family coverage gaps before claiming broad Gemini variant support."]
        return ["Observed Gemini family and cheap-first task coverage is ready for maintainer release review."]


def _family_label(model_id: str) -> str:
    value = model_id.lower()
    if "flash-lite" in value:
        return "gemini-flash-lite"
    if "flash" in value and "image" not in value:
        return "gemini-flash"
    if "pro" in value and "image" not in value:
        return "gemini-pro"
    if "image" in value:
        return "gemini-image"
    return "gemini-other"


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
