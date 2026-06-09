from __future__ import annotations

from typing import Any

from services.model_catalog import catalog_for_api, task_default_model
from services.model_catalog_source_audit import ModelCatalogSourceAuditService


REVIEW_TASKS = ("cheap", "fast", "classification", "ocr", "review", "agentic", "grounded-research")
TEXT_MODEL_IDS = ("gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro")
SOURCE_IDS = ("google-gemini-pricing", "google-gemini-models")


class ModelOpsGeminiOfficialCheapFirstSourceReviewService:
    """Build metadata-only official-source evidence for Gemini cheap-first defaults."""

    def __init__(self, source_audit_service: ModelCatalogSourceAuditService | None = None) -> None:
        self.source_audit_service = source_audit_service or ModelCatalogSourceAuditService()

    def build_review(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        source_audit = self._source_audit(signals)
        catalog = catalog_for_api()
        catalog_by_id = {str(row.get("id") or ""): row for row in catalog}
        source_reviews = [
            row
            for row in source_audit.get("source_review_records", [])
            if isinstance(row, dict) and row.get("id") in SOURCE_IDS
        ]
        price_rows = [self._price_row(model_id, catalog_by_id) for model_id in TEXT_MODEL_IDS]
        baseline = next((row for row in price_rows if row["model_id"] == "gemini-2.5-flash-lite"), None)
        comparison_rows = self._comparison_rows(price_rows, baseline)
        task_rows = [self._task_row(task, catalog_by_id) for task in REVIEW_TASKS]
        checks = self._checks(source_audit, price_rows, comparison_rows, task_rows, source_reviews)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "ready")

        return {
            "id": "modelops-gemini-official-cheap-first-source-review",
            "status": status,
            "method": {
                "type": "metadata-only-gemini-official-cheap-first-source-review",
                "notes": [
                    "Compares local Gemini Flash-Lite, Flash, and Pro price metadata for cheap-first default review.",
                    "Uses the repository catalog and existing official source audit only; it does not call Google, Gemini, NewAPI, OpenAI, gateways, app AI endpoints, models, or the network.",
                    "Blocks default-promotion claims when official source reviews are stale or high-frequency tasks drift away from Flash-Lite.",
                ],
            },
            "summary": {
                "review_model_count": len(price_rows),
                "priced_text_model_count": sum(1 for row in price_rows if row["pricing_status"] == "token_priced"),
                "cheap_first_task_count": len(task_rows),
                "cheap_first_flash_lite_task_count": sum(1 for row in task_rows if row["flash_lite_aligned"]),
                "premium_or_review_task_count": sum(1 for row in task_rows if row["requires_review"]),
                "source_review_count": len(source_reviews),
                "source_review_stale_count": sum(1 for row in source_reviews if row.get("freshness_status") == "stale"),
                "default_promotion_block_count": sum(1 for row in source_reviews if row.get("default_promotion_allowed") is False)
                + sum(1 for row in task_rows if row["requires_review"]),
                "flash_lite_input_cost_usd_per_million": baseline["input_usd_per_million_tokens"] if baseline else None,
                "flash_lite_output_cost_usd_per_million": baseline["output_usd_per_million_tokens"] if baseline else None,
                "largest_output_cost_ratio_vs_flash_lite": max(
                    (row["output_cost_ratio_vs_flash_lite"] or 0 for row in comparison_rows),
                    default=0,
                ),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_returned": False,
            },
            "official_source_rows": [
                {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "url": row.get("url"),
                    "freshness_status": row.get("freshness_status"),
                    "review_age_days": row.get("review_age_days"),
                    "max_review_age_days": row.get("max_review_age_days"),
                    "default_promotion_allowed": row.get("default_promotion_allowed"),
                    "required_action": row.get("required_action"),
                }
                for row in source_reviews
            ],
            "price_rows": price_rows,
            "comparison_rows": comparison_rows,
            "task_default_rows": task_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(status, source_reviews, task_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "source_urls_returned": True,
                "model_ids_returned": True,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "headers_included": False,
                "request_bodies_included": False,
                "response_bodies_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
            },
            "claim_boundary": {
                "official_source_refresh_completed": False,
                "live_gateway_execution_claimed": False,
                "pricing_accuracy_claimed": False,
                "automatic_default_change_claimed": False,
                "production_quality_claimed": False,
                "allowed_claim": "The repository contains metadata-only cheap-first Gemini source-review evidence using local catalog prices.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_official_cheap_first_source_review.py tests/test_model_catalog_source_audit.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _source_audit(self, signals: dict[str, Any] | None) -> dict[str, Any]:
        if isinstance(signals, dict) and isinstance(signals.get("catalog_source_audit"), dict):
            return signals["catalog_source_audit"]
        return self.source_audit_service.build_audit()

    def _price_row(self, model_id: str, catalog_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
        row = catalog_by_id.get(model_id, {})
        pricing = row.get("pricing") if isinstance(row.get("pricing"), dict) else {}
        input_price = pricing.get("input_usd_per_million_tokens")
        output_price = pricing.get("output_usd_per_million_tokens")
        return {
            "model_id": model_id,
            "catalog_status": str(row.get("status") or "missing"),
            "cost_tier": str(row.get("cost_tier") or "missing"),
            "latency_tier": str(row.get("latency_tier") or "missing"),
            "capabilities": list(row.get("capabilities") or []),
            "input_usd_per_million_tokens": input_price,
            "output_usd_per_million_tokens": output_price,
            "pricing_status": "token_priced" if input_price is not None and output_price is not None else "missing",
            "pricing_source_url": str(pricing.get("source_url") or ""),
            "cheap_first_default_allowed": model_id.endswith("flash-lite")
            and str(row.get("status") or "") == "stable"
            and str(row.get("cost_tier") or "") in {"lowest", "low"}
            and input_price is not None
            and output_price is not None,
            "requires_operator_review": str(row.get("status") or "") != "stable"
            or str(row.get("cost_tier") or "") in {"premium", "review"},
        }

    def _comparison_rows(
        self,
        price_rows: list[dict[str, Any]],
        baseline: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        baseline_input = baseline.get("input_usd_per_million_tokens") if baseline else None
        baseline_output = baseline.get("output_usd_per_million_tokens") if baseline else None
        rows: list[dict[str, Any]] = []
        for row in price_rows:
            input_price = row.get("input_usd_per_million_tokens")
            output_price = row.get("output_usd_per_million_tokens")
            rows.append(
                {
                    "model_id": row["model_id"],
                    "cost_tier": row["cost_tier"],
                    "input_cost_ratio_vs_flash_lite": self._ratio(input_price, baseline_input),
                    "output_cost_ratio_vs_flash_lite": self._ratio(output_price, baseline_output),
                    "default_policy": "cheap_first_default"
                    if row["cheap_first_default_allowed"]
                    else ("premium_exception_review" if row["requires_operator_review"] else "balanced_fallback"),
                    "review_reason": self._comparison_review_reason(row),
                }
            )
        return rows

    def _task_row(self, task: str, catalog_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
        default_model = task_default_model(task)
        catalog_row = catalog_by_id.get(default_model, {})
        is_flash_lite = "flash-lite" in default_model
        is_stable = str(catalog_row.get("status") or "") == "stable"
        cost_tier = str(catalog_row.get("cost_tier") or "unknown")
        high_frequency = task in {"cheap", "fast", "classification", "ocr"}
        requires_review = high_frequency and not (is_flash_lite and is_stable and cost_tier in {"lowest", "low"})
        return {
            "task": task,
            "default_model": default_model,
            "catalog_status": str(catalog_row.get("status") or "unknown"),
            "cost_tier": cost_tier,
            "flash_lite_aligned": is_flash_lite and is_stable and cost_tier in {"lowest", "low"},
            "high_frequency": high_frequency,
            "requires_review": requires_review,
            "review_reason": "High-frequency route remains on stable Flash-Lite."
            if not requires_review
            else "High-frequency route is not on stable Flash-Lite and must block default promotion.",
        }

    def _checks(
        self,
        source_audit: dict[str, Any],
        price_rows: list[dict[str, Any]],
        comparison_rows: list[dict[str, Any]],
        task_rows: list[dict[str, Any]],
        source_reviews: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        stale_sources = [row["id"] for row in source_reviews if row.get("freshness_status") == "stale"]
        missing_prices = [row["model_id"] for row in price_rows if row["pricing_status"] != "token_priced"]
        flash_lite = next((row for row in price_rows if row["model_id"] == "gemini-2.5-flash-lite"), None)
        task_drifts = [row["task"] for row in task_rows if row["requires_review"]]
        pro_ratio = next(
            (
                row["output_cost_ratio_vs_flash_lite"]
                for row in comparison_rows
                if row["model_id"] == "gemini-2.5-pro"
            ),
            None,
        )
        return [
            {
                "id": "official-source-review-current",
                "status": "warn" if stale_sources else "pass",
                "reason": "Official Gemini pricing/model reviews are current for cheap-first default review."
                if not stale_sources
                else "Official Gemini source review is stale: " + ", ".join(stale_sources),
            },
            {
                "id": "text-model-prices-present",
                "status": "fail" if missing_prices else "pass",
                "reason": "Flash-Lite, Flash, and Pro text models all have local token price metadata."
                if not missing_prices
                else "Text model price metadata missing for: " + ", ".join(missing_prices),
            },
            {
                "id": "flash-lite-remains-cheapest-start",
                "status": "pass" if flash_lite and flash_lite["cheap_first_default_allowed"] else "fail",
                "reason": "Gemini 2.5 Flash-Lite remains the only default-allowed low-cost start model."
                if flash_lite and flash_lite["cheap_first_default_allowed"]
                else "Gemini 2.5 Flash-Lite is not safe as the cheap-first default.",
            },
            {
                "id": "premium-ratio-review-visible",
                "status": "pass" if pro_ratio and pro_ratio >= 10 else "warn",
                "reason": "Gemini 2.5 Pro output price ratio versus Flash-Lite is visible for premium exception review."
                if pro_ratio and pro_ratio >= 10
                else "Premium price ratio should be reviewed before any Pro default promotion.",
            },
            {
                "id": "high-frequency-defaults-flash-lite",
                "status": "fail" if task_drifts else "pass",
                "reason": "High-frequency tasks stay on stable Flash-Lite defaults."
                if not task_drifts
                else "High-frequency default drift detected for: " + ", ".join(task_drifts),
            },
            {
                "id": "source-audit-linked",
                "status": "pass" if source_audit.get("summary", {}).get("source_reference_count", 0) >= 2 else "fail",
                "reason": "Review links to the shared official Gemini source audit.",
            },
        ]

    def _recommended_actions(
        self,
        status: str,
        source_reviews: list[dict[str, Any]],
        task_rows: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        stale = [row for row in source_reviews if row.get("freshness_status") == "stale"]
        if stale:
            actions.append("Refresh official Gemini pricing/model source review before default promotion.")
        drifts = [row for row in task_rows if row["requires_review"]]
        if drifts:
            actions.append("Move high-frequency defaults back to stable Flash-Lite or keep promotion blocked.")
        if status == "ready":
            actions.append("Keep Flash-Lite as the cheap-first default and require explicit review for Flash/Pro promotion.")
        actions.append("Re-run typecheck, UI regression, and ModelOps readiness tests after any catalog price or default change.")
        return actions

    def _ratio(self, value: Any, baseline: Any) -> float | None:
        if not isinstance(value, (int, float)) or not isinstance(baseline, (int, float)) or baseline <= 0:
            return None
        return round(float(value) / float(baseline), 2)

    def _comparison_review_reason(self, row: dict[str, Any]) -> str:
        if row["cheap_first_default_allowed"]:
            return "Allowed cheap-first start for high-frequency tasks."
        if row["requires_operator_review"]:
            return "Premium, preview, review, or non-low-cost model; explicit operator review only."
        return "Balanced fallback after cheap-first checks or quality gate escalation."
