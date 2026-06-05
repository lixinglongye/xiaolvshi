from __future__ import annotations

from typing import Any


class ModelOpsDefaultChangeQueueService:
    """Build a metadata-only queue for cheap-first default model changes."""

    def build_queue(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        release_decision = _dict(data.get("cheap_first_release_decision"))
        default_optimization = _dict(data.get("default_optimization"))
        gateway_probe = _dict(data.get("gateway_probe_evaluation"))
        price_refresh = _dict(data.get("price_refresh_monitor"))
        catalog_audit = _dict(data.get("catalog_source_audit"))
        release_status = str(release_decision.get("status") or "missing").lower()
        release_summary = _dict(release_decision.get("summary"))
        release_blocks = bool(release_summary.get("default_promotion_blocked")) or release_status == "fail"
        release_review = bool(release_summary.get("maintainer_review_required")) or release_status in {
            "warn",
            "review_required",
        }
        gateway_status = str(gateway_probe.get("status") or "missing").lower()
        price_status = str(price_refresh.get("status") or "missing").lower()
        catalog_status = str(catalog_audit.get("status") or "missing").lower()
        items = [
            self._item(
                row,
                release_blocks=release_blocks,
                release_review=release_review,
                gateway_status=gateway_status,
                price_status=price_status,
                catalog_status=catalog_status,
            )
            for row in _list(default_optimization.get("recommendations"))
            if isinstance(row, dict)
        ]
        blocking = [item for item in items if item["queue_status"] == "blocked"]
        review = [item for item in items if item["queue_status"] == "review_required"]
        ready = [item for item in items if item["queue_status"] == "ready"]
        no_action = [item for item in items if item["queue_status"] == "no_action"]
        status = "blocked" if blocking else ("review_required" if review else "ready")

        return {
            "status": status,
            "method": {
                "type": "model-ops-default-change-queue",
                "notes": [
                    "Builds maintainer queue entries from existing ModelOps metadata only.",
                    "Does not write .env files, change runtime defaults, call NewAPI/Gemini/OpenAI/Google, or run probes.",
                    "Warn and review states keep changes in maintainer review rather than promoting defaults automatically.",
                ],
            },
            "summary": {
                "queue_item_count": len(items),
                "change_request_count": sum(1 for item in items if item["requires_change"]),
                "ready_change_count": len(ready),
                "review_required_count": len(review),
                "blocked_change_count": len(blocking),
                "no_action_count": len(no_action),
                "release_decision_status": release_status,
                "gateway_probe_status": gateway_status,
                "price_refresh_status": price_status,
                "catalog_source_audit_status": catalog_status,
                "configuration_written": False,
                "gateway_called": False,
            },
            "queue_items": items,
            "blocking_item_ids": [item["id"] for item in blocking],
            "review_item_ids": [item["id"] for item in review],
            "recommended_actions": self._recommended_actions(blocking, review, ready, no_action),
            "privacy_boundary": {
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "configuration_written": False,
                "network_called": False,
                "output_scope": "task ids, env var names, model ids, queue status, reason codes, and validation commands only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "public_benchmark_scores_included": False,
                "production_accuracy_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_default_change_queue.py tests/test_model_ops_cheap_first_release_decision.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _item(
        self,
        row: dict[str, Any],
        *,
        release_blocks: bool,
        release_review: bool,
        gateway_status: str,
        price_status: str,
        catalog_status: str,
    ) -> dict[str, Any]:
        task = str(row.get("task") or "unknown")
        requires_change = bool(row.get("requires_change"))
        row_status = str(row.get("status") or "missing").lower()
        operator_review = bool(row.get("requires_operator_review"))
        reason_codes: list[str] = []
        if release_blocks:
            reason_codes.append("release-decision-blocked")
        if row_status == "fail":
            reason_codes.append("default-optimization-failed")
        if price_status == "fail":
            reason_codes.append("price-refresh-blocked")
        if catalog_status == "fail":
            reason_codes.append("catalog-source-blocked")
        if not requires_change:
            queue_status = "no_action"
            reason_codes.append("runtime-default-aligned")
        elif reason_codes:
            queue_status = "blocked"
        elif release_review or operator_review or row_status == "warn":
            queue_status = "review_required"
            reason_codes.append("maintainer-review-required")
        elif gateway_status in {"not_run", "missing", "warn", "warning", "review_required"}:
            queue_status = "review_required"
            reason_codes.append("sanitized-gateway-probe-review")
        elif price_status in {"warn", "warning", "review_required"}:
            queue_status = "review_required"
            reason_codes.append("price-refresh-review")
        elif catalog_status in {"warn", "warning", "review_required"}:
            queue_status = "review_required"
            reason_codes.append("catalog-source-review")
        else:
            queue_status = "ready"
            reason_codes.append("ready-after-standard-validation")

        return {
            "id": f"default-change-{task}",
            "task": task,
            "env_var": row.get("env_var"),
            "current_model": str(row.get("current_model") or ""),
            "recommended_model": str(row.get("recommended_model") or ""),
            "requires_change": requires_change,
            "requires_operator_review": operator_review,
            "queue_status": queue_status,
            "default_optimization_status": row_status,
            "current_cost_tier": row.get("current_cost_tier"),
            "recommended_cost_tier": row.get("recommended_cost_tier"),
            "estimated_monthly_savings_usd": row.get("estimated_monthly_savings_usd"),
            "reason_codes": _dedupe(reason_codes),
            "action": self._action(queue_status, row),
        }

    def _action(self, queue_status: str, row: dict[str, Any]) -> str:
        task = str(row.get("task") or "unknown")
        env_var = str(row.get("env_var") or "explicit model request")
        recommended_model = str(row.get("recommended_model") or "")
        if queue_status == "no_action":
            return f"Keep the current {task} default; no default model change is queued."
        if queue_status == "blocked":
            return f"Do not change {env_var} until blocking ModelOps checks pass."
        if queue_status == "review_required":
            return f"Review evidence before setting {env_var} to {recommended_model}."
        return f"After validation, maintainer may set {env_var} to {recommended_model}."

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        review: list[dict[str, Any]],
        ready: list[dict[str, Any]],
        no_action: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if blocking:
            actions.append("Resolve blocked default-change queue items before editing model default environment variables.")
        if review:
            actions.append("Complete maintainer review for queued default changes; keep explicit experiments separate from defaults.")
        if ready:
            actions.append("Run validation commands and update defaults only through maintainer-approved configuration changes.")
        if no_action and not actions:
            actions.append("Current cheap-first defaults do not need changes; rerun this queue before any model default edit.")
        return actions or ["No default model change queue items were generated."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
