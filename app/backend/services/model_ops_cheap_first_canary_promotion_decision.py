from __future__ import annotations

from typing import Any


class ModelOpsCheapFirstCanaryPromotionDecisionService:
    """Build a metadata-only advance/hold/rollback decision from canary evidence."""

    def build_decision(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        canary_plan = _dict(data.get("cheap_first_canary_plan"))
        observation = _dict(data.get("cheap_first_canary_observation"))
        plan_status = _status(canary_plan.get("status"), "missing")
        observation_status = _status(observation.get("status"), "not_supplied")
        observation_summary = _dict(observation.get("summary"))
        canary_steps = [step for step in _list(canary_plan.get("canary_steps")) if isinstance(step, dict)]
        observation_rows = [row for row in _list(observation.get("observation_rows")) if isinstance(row, dict)]
        decisions = [
            self._decision(step, observation_rows, plan_status, observation_status, observation_summary)
            for step in canary_steps
        ]
        rollback = [item for item in decisions if item["promotion_status"] == "rollback_required"]
        hold = [item for item in decisions if item["promotion_status"] == "hold_for_review"]
        advance = [item for item in decisions if item["promotion_status"] == "advance_next_batch"]
        monitor = [item for item in decisions if item["promotion_status"] == "monitor_only"]
        not_ready = [item for item in decisions if item["promotion_status"] == "not_ready"]
        status = self._status(rollback, hold, advance, monitor, not_ready)

        return {
            "status": status,
            "decision": {
                "status": status,
                "label": self._label(status),
                "default_action": self._default_action(status),
                "configuration_change_allowed": False,
                "traffic_shift_allowed": False,
                "requires_maintainer_approval": True,
            },
            "method": {
                "type": "model-ops-cheap-first-canary-promotion-decision",
                "notes": [
                    "Consumes the metadata-only canary plan and aggregate observation review.",
                    "Does not write configuration, advance traffic, call a gateway, or persist rollout state.",
                    "Treats failed canary observations as rollback-required and missing/low-volume observations as hold-for-review.",
                ],
            },
            "summary": {
                "decision_item_count": len(decisions),
                "advance_decision_count": len(advance),
                "hold_decision_count": len(hold),
                "rollback_decision_count": len(rollback),
                "monitor_only_count": len(monitor),
                "not_ready_count": len(not_ready),
                "source_plan_status": plan_status,
                "source_observation_status": observation_status,
                "observation_count": _safe_int(observation_summary.get("observation_count")),
                "failing_observation_count": _safe_int(observation_summary.get("failing_observation_count")),
                "warning_observation_count": _safe_int(observation_summary.get("warning_observation_count")),
                "rollback_trigger_breach_count": _safe_int(observation_summary.get("rollback_trigger_breach_count")),
                "configuration_written": False,
                "gateway_called": False,
                "traffic_shifted": False,
            },
            "promotion_items": decisions,
            "advance_item_ids": [item["id"] for item in advance],
            "hold_item_ids": [item["id"] for item in hold],
            "rollback_item_ids": [item["id"] for item in rollback],
            "recommended_actions": self._recommended_actions(status, rollback, hold, advance, monitor, not_ready),
            "privacy_boundary": {
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "configuration_written": False,
                "network_called": False,
                "traffic_shifted": False,
                "output_scope": "canary step ids, aggregate observation statuses, decision labels, and validation commands only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "automatic_canary_rollout_claimed": False,
                "production_traffic_shifted": False,
                "public_benchmark_scores_included": False,
                "production_accuracy_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_canary_promotion_decision.py tests/test_model_ops_cheap_first_canary_observation.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _decision(
        self,
        step: dict[str, Any],
        observation_rows: list[dict[str, Any]],
        plan_status: str,
        observation_status: str,
        observation_summary: dict[str, Any],
    ) -> dict[str, Any]:
        step_id = str(step.get("id") or "unknown-step")
        step_status = _status(step.get("step_status"), "missing")
        rows = [row for row in observation_rows if row.get("step_id") == step_id]
        row_statuses = {_status(row.get("status"), "missing") for row in rows}
        reason_codes: list[str] = []

        if step_status == "monitor_only":
            promotion_status = "monitor_only"
            reason_codes.append("current-default-monitor-only")
        elif plan_status in {"blocked", "fail", "failed", "error"} or step_status == "blocked":
            promotion_status = "not_ready"
            reason_codes.append("canary-plan-blocked")
        elif step_status == "review_required":
            promotion_status = "not_ready"
            reason_codes.append("canary-step-review-required")
        elif observation_summary.get("forbidden_payload_field_count") or observation_summary.get("secret_like_value_count"):
            promotion_status = "rollback_required"
            reason_codes.append("observation-payload-rejected")
        elif observation_status == "fail" or "fail" in row_statuses:
            promotion_status = "rollback_required"
            reason_codes.append("rollback-trigger-breached")
        elif observation_status in {"review_required", "warn", "warning"} or "warn" in row_statuses:
            promotion_status = "hold_for_review"
            reason_codes.append("observation-review-required")
        elif not rows:
            promotion_status = "hold_for_review"
            reason_codes.append("observation-missing-for-step")
        elif step_status in {"ready", "pending_after_prior_pass"} and row_statuses == {"pass"}:
            promotion_status = "advance_next_batch"
            reason_codes.append("canary-observation-passed")
        else:
            promotion_status = "hold_for_review"
            reason_codes.append("canary-state-review-required")

        return {
            "id": f"promotion-{step_id}",
            "source_step_id": step_id,
            "task": str(step.get("task") or "unknown"),
            "phase": str(step.get("phase") or "unknown"),
            "step_status": step_status,
            "promotion_status": promotion_status,
            "observation_statuses": sorted(row_statuses),
            "matched_observation_count": len(rows),
            "batch_percentage": _safe_int(step.get("batch_percentage")),
            "holdout_percentage": _safe_int(step.get("holdout_percentage")),
            "reason_codes": reason_codes,
            "configuration_change_allowed": False,
            "traffic_shift_allowed": False,
            "action": self._item_action(promotion_status, step),
        }

    def _item_action(self, promotion_status: str, step: dict[str, Any]) -> str:
        task = str(step.get("task") or "unknown")
        if promotion_status == "rollback_required":
            return f"Rollback or keep the previous {task} default; do not advance this canary."
        if promotion_status == "hold_for_review":
            return f"Hold the {task} canary until aggregate observations pass and maintainer review is attached."
        if promotion_status == "advance_next_batch":
            return f"Maintainer may review the next {task} batch, but this service will not change traffic or configuration."
        if promotion_status == "monitor_only":
            return f"Keep monitoring the current {task} default; no canary promotion is queued."
        return f"Do not advance the {task} canary until the source plan is ready."

    def _status(
        self,
        rollback: list[dict[str, Any]],
        hold: list[dict[str, Any]],
        advance: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
        not_ready: list[dict[str, Any]],
    ) -> str:
        if rollback:
            return "rollback_required"
        if hold:
            return "hold_for_review"
        if not_ready and not advance:
            return "not_ready"
        if advance:
            return "advance_next_batch"
        if monitor:
            return "monitor_only"
        return "not_supplied"

    def _label(self, status: str) -> str:
        return {
            "rollback_required": "rollback canary or keep previous defaults",
            "hold_for_review": "hold canary for maintainer review",
            "advance_next_batch": "eligible for next batch review",
            "monitor_only": "monitor current cheap-first defaults",
            "not_ready": "source plan not ready",
        }.get(status, "no canary promotion evidence supplied")

    def _default_action(self, status: str) -> str:
        return {
            "rollback_required": "do_not_advance_and_review_rollback",
            "hold_for_review": "hold_current_batch",
            "advance_next_batch": "review_next_batch_without_automatic_change",
            "monitor_only": "keep_monitoring_current_defaults",
            "not_ready": "resolve_source_plan_before_promotion",
        }.get(status, "submit_canary_observations")

    def _recommended_actions(
        self,
        status: str,
        rollback: list[dict[str, Any]],
        hold: list[dict[str, Any]],
        advance: list[dict[str, Any]],
        monitor: list[dict[str, Any]],
        not_ready: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if rollback:
            actions.append("Rollback or keep previous defaults for canary steps with failing observation evidence.")
        if hold:
            actions.append("Hold canary batch increases until aggregate observations pass and maintainer review is attached.")
        if advance:
            actions.append("Review next-batch promotion manually; this packet does not shift traffic or write configuration.")
        if status == "monitor_only" and monitor:
            actions.append("No canary promotion is queued; keep monitoring cheap-first route and cost guardrails.")
        if not_ready:
            actions.append("Resolve source canary plan blockers before reviewing promotion decisions.")
        return actions or ["Submit canary observations before making a canary promotion decision."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _status(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    return text or fallback


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return 0
