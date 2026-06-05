from __future__ import annotations

from typing import Any


CANARY_BATCHES = (
    ("canary_1_percent", 1, 99, 4),
    ("canary_10_percent", 10, 90, 8),
    ("canary_25_percent", 25, 75, 12),
)

ROLLBACK_TRIGGERS = (
    {
        "id": "route-failure-rate",
        "metric": "failure_rate",
        "threshold": 0.02,
        "action": "Rollback to the previous default if canary failure rate exceeds 2%.",
    },
    {
        "id": "over-budget-route-ratio",
        "metric": "over_budget_route_ratio",
        "threshold": 0.01,
        "action": "Rollback if more than 1% of canary requests exceed the configured task budget.",
    },
    {
        "id": "premium-request-ratio",
        "metric": "premium_request_ratio",
        "threshold": 0.05,
        "action": "Stop canary if premium or unknown-price routing exceeds the cheap-first guardrail.",
    },
    {
        "id": "operator-review-ratio",
        "metric": "operator_review_route_ratio",
        "threshold": 0.10,
        "action": "Hold rollout when operator-review routing exceeds 10%.",
    },
)


class ModelOpsCheapFirstCanaryPlanService:
    """Build a metadata-only canary plan for queued cheap-first default changes."""

    def build_plan(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        default_change_queue = _dict(data.get("default_change_queue"))
        release_decision = _dict(data.get("cheap_first_release_decision"))
        route_guardrails = _dict(data.get("route_guardrails"))
        cost_guardrails = _dict(data.get("cost_guardrails"))
        route_ops = _dict(data.get("route_telemetry_ops_summary"))

        route_status = _status(route_guardrails.get("status"), "missing")
        cost_status = _status(cost_guardrails.get("status"), "missing")
        route_ops_status = _status(route_ops.get("status"), "missing")
        release_status = _status(release_decision.get("status"), "missing")
        global_blocks = self._global_block_codes(route_status, cost_status)
        global_reviews = self._global_review_codes(route_status, cost_status, route_ops_status, release_status)

        items = [item for item in _list(default_change_queue.get("queue_items")) if isinstance(item, dict)]
        steps: list[dict[str, Any]] = []
        for item in items:
            steps.extend(self._steps_for_item(item, global_blocks=global_blocks, global_reviews=global_reviews))

        blocked_steps = [step for step in steps if step["step_status"] == "blocked"]
        review_steps = [step for step in steps if step["step_status"] == "review_required"]
        ready_steps = [step for step in steps if step["step_status"] in {"ready", "pending_after_prior_pass"}]
        monitor_steps = [step for step in steps if step["step_status"] == "monitor_only"]
        status = self._status(blocked_steps, review_steps, ready_steps, monitor_steps)

        return {
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-canary-plan",
                "notes": [
                    "Builds rollout review steps from the default-change queue and existing route/cost guardrails only.",
                    "Does not write configuration, shift traffic, call NewAPI/Gemini/OpenAI/Google, or run live probes.",
                    "Ready steps still require maintainer approval, validation commands, and observed canary metrics before rollout.",
                ],
            },
            "summary": {
                "queue_item_count": len(items),
                "canary_step_count": len(steps),
                "canary_required_count": sum(1 for item in items if item.get("queue_status") == "ready"),
                "ready_step_count": len(ready_steps),
                "review_required_step_count": len(review_steps),
                "blocked_step_count": len(blocked_steps),
                "monitor_only_step_count": len(monitor_steps),
                "rollback_trigger_count": len(ROLLBACK_TRIGGERS),
                "route_guardrail_status": route_status,
                "cost_guardrail_status": cost_status,
                "route_telemetry_ops_status": route_ops_status,
                "release_decision_status": release_status,
                "configuration_written": False,
                "gateway_called": False,
                "traffic_shifted": False,
            },
            "rollout_policy": {
                "batch_percentages": [batch for _, batch, _, _ in CANARY_BATCHES],
                "minimum_observation_window_hours": sum(hours for _, _, _, hours in CANARY_BATCHES),
                "holdout_required_until_final_review": True,
                "operator_approval_required": True,
                "validation_source": "local metadata, route telemetry aggregates, and maintainer-reviewed canary observations",
            },
            "success_thresholds": {
                "failure_rate_max": 0.02,
                "over_budget_route_ratio_max": 0.01,
                "premium_request_ratio_max": 0.05,
                "operator_review_route_ratio_max": 0.10,
            },
            "rollback_triggers": list(ROLLBACK_TRIGGERS),
            "canary_steps": steps,
            "blocking_step_ids": [step["id"] for step in blocked_steps],
            "review_step_ids": [step["id"] for step in review_steps],
            "recommended_actions": self._recommended_actions(status, blocked_steps, review_steps, ready_steps, monitor_steps),
            "privacy_boundary": {
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "configuration_written": False,
                "network_called": False,
                "traffic_shifted": False,
                "output_scope": "queue item ids, model ids, task names, rollout percentages, guardrail statuses, and validation commands only",
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
                "python -m pytest tests/test_model_ops_cheap_first_canary_plan.py tests/test_model_ops_default_change_queue.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _steps_for_item(
        self,
        item: dict[str, Any],
        *,
        global_blocks: list[str],
        global_reviews: list[str],
    ) -> list[dict[str, Any]]:
        queue_status = _status(item.get("queue_status"), "review_required")
        reason_codes = _dedupe([*_string_list(item.get("reason_codes")), *global_blocks, *global_reviews])
        task = str(item.get("task") or "unknown")
        if queue_status == "no_action":
            return [
                self._step(
                    item,
                    phase="monitor_existing_default",
                    step_status="monitor_only",
                    batch_percentage=0,
                    holdout_percentage=100,
                    observation_window_hours=24,
                    reason_codes=reason_codes or ["runtime-default-aligned"],
                    action=f"Keep monitoring the current {task} default; no canary is queued.",
                )
            ]
        if queue_status == "blocked" or global_blocks:
            return [
                self._step(
                    item,
                    phase="blocked_before_canary",
                    step_status="blocked",
                    batch_percentage=0,
                    holdout_percentage=100,
                    observation_window_hours=0,
                    reason_codes=reason_codes or ["canary-blocked"],
                    action=f"Do not start canary for {task} until blocking ModelOps checks pass.",
                )
            ]
        if queue_status == "review_required" or global_reviews:
            return [
                self._step(
                    item,
                    phase="maintainer_review",
                    step_status="review_required",
                    batch_percentage=0,
                    holdout_percentage=100,
                    observation_window_hours=0,
                    reason_codes=reason_codes or ["maintainer-review-required"],
                    action=f"Complete maintainer review before canarying the {task} default.",
                )
            ]
        if queue_status != "ready":
            return [
                self._step(
                    item,
                    phase="status_review",
                    step_status="review_required",
                    batch_percentage=0,
                    holdout_percentage=100,
                    observation_window_hours=0,
                    reason_codes=reason_codes or [f"unrecognized-queue-status:{queue_status}"],
                    action=f"Review unrecognized queue status before canarying the {task} default.",
                )
            ]

        steps: list[dict[str, Any]] = []
        for index, (phase, batch, holdout, hours) in enumerate(CANARY_BATCHES):
            steps.append(
                self._step(
                    item,
                    phase=phase,
                    step_status="ready" if index == 0 else "pending_after_prior_pass",
                    batch_percentage=batch,
                    holdout_percentage=holdout,
                    observation_window_hours=hours,
                    reason_codes=reason_codes or ["ready-after-standard-validation"],
                    action=self._canary_action(item, phase, batch),
                )
            )
        return steps

    def _step(
        self,
        item: dict[str, Any],
        *,
        phase: str,
        step_status: str,
        batch_percentage: int,
        holdout_percentage: int,
        observation_window_hours: int,
        reason_codes: list[str],
        action: str,
    ) -> dict[str, Any]:
        task = str(item.get("task") or "unknown")
        return {
            "id": f"{phase}-{task}",
            "source_queue_item_id": str(item.get("id") or f"default-change-{task}"),
            "task": task,
            "env_var": item.get("env_var"),
            "current_model": str(item.get("current_model") or ""),
            "recommended_model": str(item.get("recommended_model") or ""),
            "phase": phase,
            "step_status": step_status,
            "batch_percentage": batch_percentage,
            "holdout_percentage": holdout_percentage,
            "observation_window_hours": observation_window_hours,
            "requires_configuration_change": bool(item.get("requires_change")),
            "requires_operator_review": True,
            "reason_codes": _dedupe(reason_codes),
            "success_thresholds": {
                "failure_rate_max": 0.02,
                "over_budget_route_ratio_max": 0.01,
                "premium_request_ratio_max": 0.05,
                "operator_review_route_ratio_max": 0.10,
            },
            "rollback_trigger_ids": [trigger["id"] for trigger in ROLLBACK_TRIGGERS],
            "action": action,
        }

    def _canary_action(self, item: dict[str, Any], phase: str, batch_percentage: int) -> str:
        env_var = str(item.get("env_var") or "explicit model request")
        recommended_model = str(item.get("recommended_model") or "")
        return (
            f"After validation, review a {batch_percentage}% {phase.replace('_', ' ')} for "
            f"{env_var} -> {recommended_model}; rollback on any trigger breach."
        )

    def _global_block_codes(self, route_status: str, cost_status: str) -> list[str]:
        codes: list[str] = []
        if route_status in {"fail", "failed", "blocked", "error"}:
            codes.append("route-guardrails-blocked")
        if cost_status in {"fail", "failed", "blocked", "error"}:
            codes.append("cost-guardrails-blocked")
        return codes

    def _global_review_codes(self, route_status: str, cost_status: str, route_ops_status: str, release_status: str) -> list[str]:
        codes: list[str] = []
        if route_status in {"warn", "warning", "review_required", "missing"}:
            codes.append("route-guardrails-review")
        if cost_status in {"warn", "warning", "review_required", "missing"}:
            codes.append("cost-guardrails-review")
        if route_ops_status in {"warn", "warning", "review_required", "missing"}:
            codes.append("route-telemetry-ops-review")
        if release_status in {"warn", "warning", "review_required", "missing"}:
            codes.append("release-decision-review")
        return codes

    def _status(
        self,
        blocked_steps: list[dict[str, Any]],
        review_steps: list[dict[str, Any]],
        ready_steps: list[dict[str, Any]],
        monitor_steps: list[dict[str, Any]],
    ) -> str:
        if blocked_steps:
            return "blocked"
        if review_steps:
            return "review_required"
        if ready_steps:
            return "ready"
        if monitor_steps:
            return "monitor_only"
        return "not_run"

    def _recommended_actions(
        self,
        status: str,
        blocked_steps: list[dict[str, Any]],
        review_steps: list[dict[str, Any]],
        ready_steps: list[dict[str, Any]],
        monitor_steps: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if blocked_steps:
            actions.append("Resolve blocked canary plan steps before editing model defaults or routing traffic.")
        if review_steps:
            actions.append("Complete maintainer review and attach sanitized canary observation criteria before rollout.")
        if ready_steps:
            actions.append("Run the validation commands, approve configuration change separately, and observe canary thresholds before increasing batch size.")
        if status == "monitor_only" and monitor_steps:
            actions.append("No canary is queued; keep monitoring route and cost guardrails before any future default edit.")
        return actions or ["No canary plan steps were generated."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _status(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    return text or fallback


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
