from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK, TASK_GROUPS
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_catalog import model_profile
from services.model_escalation_policy import ModelEscalationPolicyService


LATENCY_RANK = {"fastest": 0, "fast": 1, "medium": 2, "slower": 3, "unknown": 99}


@dataclass(frozen=True)
class FallbackStep:
    order: int
    role: str
    trigger: str
    model_alias: str | None
    resolved_model: str
    cost_tier: str
    latency_tier: str
    model_status: str
    requires_operator_review: bool
    source: str
    note: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class ModelFallbackChainService:
    """Build cheap-first model fallback chains for configured Gemini routing tasks."""

    def __init__(
        self,
        capability_matrix: ModelCapabilityMatrixService | None = None,
        escalation_policy: ModelEscalationPolicyService | None = None,
    ) -> None:
        self.capability_matrix = capability_matrix or ModelCapabilityMatrixService()
        self.escalation_policy = escalation_policy or ModelEscalationPolicyService()

    def build_chains(self) -> dict[str, Any]:
        matrix_rows = {row["task"]: row for row in self.capability_matrix.build_matrix()["tasks"]}
        plan_rows = {plan["task"]: plan for plan in self.escalation_policy.build_policy()["plans"]}
        task_order = list(dict.fromkeys([*matrix_rows.keys(), *plan_rows.keys()]))
        chains = [
            self._build_chain(task, matrix_rows.get(task), plan_rows.get(task))
            for task in task_order
        ]
        failing = [chain for chain in chains if chain["status"] == "fail"]
        warning = [chain for chain in chains if chain["status"] == "warn"]

        return {
            "status": "fail" if failing else ("warn" if warning else "pass"),
            "method": {
                "strategy": "cheap-first-fallback-chain",
                "notes": [
                    "Escalation policy steps define runtime fallback behavior for core tasks.",
                    "Capability matrix candidates fill explicit Gemini tasks that do not have runtime aliases yet.",
                    "Premium fallback steps outside PDF/image tasks require operator review.",
                    "No API keys, prompts, documents, file names, user identifiers, or model outputs are stored.",
                ],
            },
            "summary": {
                "chain_count": len(chains),
                "pass_count": sum(1 for chain in chains if chain["status"] == "pass"),
                "warn_count": len(warning),
                "fail_count": len(failing),
                "cheap_primary_count": sum(
                    1
                    for chain in chains
                    if chain["steps"]
                    and chain["steps"][0]["cost_tier"] in {"lowest", "low"}
                ),
                "operator_review_step_count": sum(
                    1
                    for chain in chains
                    for step in chain["steps"]
                    if step["requires_operator_review"]
                ),
                "premium_exception_task_count": sum(
                    1
                    for chain in chains
                    if any(step["cost_tier"] == "premium" for step in chain["steps"])
                ),
            },
            "chains": chains,
        }

    def _build_chain(
        self,
        task: str,
        matrix_row: dict[str, Any] | None,
        plan_row: dict[str, Any] | None,
    ) -> dict[str, Any]:
        steps = self._steps_from_plan(task, plan_row) if plan_row else self._steps_from_matrix(task, matrix_row)
        max_cost_tier = self._max_cost_tier(task, matrix_row)
        checks = self._checks(task=task, matrix_row=matrix_row, steps=steps, max_cost_tier=max_cost_tier)
        failed = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        display_name = self._display_name(task, matrix_row, plan_row)

        return {
            "task": task,
            "display_name": display_name,
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "budget_mode": TASK_GROUPS.get(task, {}).get("budget_mode", "explicit"),
            "max_cost_tier": max_cost_tier,
            "runtime_default_model": matrix_row.get("runtime_default_model") if matrix_row else None,
            "recommended_model": matrix_row.get("recommended_model") if matrix_row else None,
            "source": "escalation_policy" if plan_row else "capability_matrix",
            "hard_stop_signals": plan_row.get("hard_stop_signals", []) if plan_row else [],
            "steps": [step.to_api() for step in steps],
            "checks": checks,
            "recommended_action": self._recommended_action(task, failed, warnings),
        }

    def _steps_from_plan(self, task: str, plan_row: dict[str, Any] | None) -> list[FallbackStep]:
        if not plan_row:
            return []
        steps: list[FallbackStep] = []
        for raw in plan_row["steps"]:
            profile = model_profile(raw["resolved_model"])
            cost_tier = profile.cost_tier if profile else "unknown"
            role = self._role_from_policy_step(raw, cost_tier)
            steps.append(
                FallbackStep(
                    order=int(raw["order"]),
                    role=role,
                    trigger=str(raw["trigger"]),
                    model_alias=raw.get("model_alias"),
                    resolved_model=str(raw["resolved_model"]),
                    cost_tier=cost_tier,
                    latency_tier=profile.latency_tier if profile else "unknown",
                    model_status=profile.status if profile else "unknown",
                    requires_operator_review=bool(raw.get("requires_operator_review")),
                    source="escalation_policy",
                    note=self._step_note(task=task, role=role, cost_tier=cost_tier),
                )
            )
        return steps

    def _steps_from_matrix(self, task: str, matrix_row: dict[str, Any] | None) -> list[FallbackStep]:
        if not matrix_row:
            return []
        max_cost_tier = self._max_cost_tier(task, matrix_row)
        selected = self._select_matrix_candidates(matrix_row["candidates"], max_cost_tier=max_cost_tier)
        steps: list[FallbackStep] = []
        for index, candidate in enumerate(selected):
            cost_tier = str(candidate.get("cost_tier") or "unknown")
            over_budget = bool(candidate.get("over_task_budget"))
            role = "primary" if index == 0 and not over_budget else ("premium-exception" if cost_tier == "premium" else "fallback")
            requires_operator_review = cost_tier == "premium" and task not in {"pdf", "image"}
            steps.append(
                FallbackStep(
                    order=index + 1,
                    role=role,
                    trigger="capability fallback candidate" if index else "recommended capability match",
                    model_alias=None,
                    resolved_model=str(candidate["model_id"]),
                    cost_tier=cost_tier,
                    latency_tier=str(candidate.get("latency_tier") or "unknown"),
                    model_status=str(candidate.get("status") or "unknown"),
                    requires_operator_review=requires_operator_review,
                    source="capability_matrix",
                    note=self._step_note(task=task, role=role, cost_tier=cost_tier),
                )
            )
        return steps

    def _select_matrix_candidates(self, candidates: list[dict[str, Any]], *, max_cost_tier: str) -> list[dict[str, Any]]:
        within_budget = [candidate for candidate in candidates if not candidate.get("over_task_budget")]
        premium = [
            candidate
            for candidate in candidates
            if candidate.get("cost_tier") == "premium"
            and candidate not in within_budget
        ]
        selected = within_budget[:3]
        if premium:
            selected.append(premium[0])
        if not selected and candidates:
            selected = candidates[:1]
        selected.sort(
            key=lambda item: (
                0 if item in within_budget else 1,
                COST_TIER_RANK.get(str(item.get("cost_tier") or "unknown"), 99),
                LATENCY_RANK.get(str(item.get("latency_tier") or "unknown"), 99),
                str(item.get("model_id")),
            )
        )
        return selected

    def _checks(
        self,
        *,
        task: str,
        matrix_row: dict[str, Any] | None,
        steps: list[FallbackStep],
        max_cost_tier: str,
    ) -> list[dict[str, Any]]:
        primary = steps[0] if steps else None
        return [
            self._check_has_primary(primary),
            self._check_primary_budget(task=task, primary=primary, max_cost_tier=max_cost_tier),
            self._check_premium_review(task=task, steps=steps),
            self._check_runtime_alignment(task=task, matrix_row=matrix_row, primary=primary),
        ]

    def _check_has_primary(self, primary: FallbackStep | None) -> dict[str, Any]:
        return {
            "id": "primary-model",
            "status": "pass" if primary else "fail",
            "reason": "Fallback chain has a primary model." if primary else "Fallback chain has no primary model.",
        }

    def _check_primary_budget(self, *, task: str, primary: FallbackStep | None, max_cost_tier: str) -> dict[str, Any]:
        if not primary:
            return {"id": "primary-budget", "status": "fail", "reason": "No primary model is available."}
        if task in {"pdf", "image"}:
            return {
                "id": "primary-budget",
                "status": "pass",
                "reason": "Task is an explicit premium/media exception.",
            }
        primary_rank = COST_TIER_RANK.get(primary.cost_tier, 99)
        max_rank = COST_TIER_RANK.get(max_cost_tier, 99)
        return {
            "id": "primary-budget",
            "status": "pass" if primary_rank <= max_rank else "fail",
            "reason": "Primary model is within the task cost budget."
            if primary_rank <= max_rank
            else "Primary model exceeds the task cost budget.",
        }

    def _check_premium_review(self, *, task: str, steps: list[FallbackStep]) -> dict[str, Any]:
        unsafe_steps = [
            step
            for step in steps
            if step.cost_tier == "premium"
            and not step.requires_operator_review
            and task not in {"pdf", "image"}
        ]
        return {
            "id": "premium-operator-review",
            "status": "pass" if not unsafe_steps else "fail",
            "reason": "Premium fallback steps outside explicit exceptions require operator review."
            if not unsafe_steps
            else "At least one premium fallback step can run without operator review.",
        }

    def _check_runtime_alignment(
        self,
        *,
        task: str,
        matrix_row: dict[str, Any] | None,
        primary: FallbackStep | None,
    ) -> dict[str, Any]:
        if not matrix_row or not primary:
            return {
                "id": "runtime-default",
                "status": "pass",
                "reason": "No matrix runtime default applies to this chain.",
            }
        default_alias = matrix_row["requirement"].get("default_alias")
        if default_alias == "explicit":
            return {
                "id": "runtime-default",
                "status": "pass",
                "reason": "Task is explicitly selected rather than default-routed.",
            }
        runtime_default = matrix_row.get("runtime_default_model")
        status = "pass" if runtime_default == primary.resolved_model else "warn"
        return {
            "id": "runtime-default",
            "status": status,
            "reason": "Runtime default matches the fallback primary model."
            if status == "pass"
            else "Runtime default differs from the fallback primary model; review configuration.",
        }

    def _role_from_policy_step(self, raw: dict[str, Any], cost_tier: str) -> str:
        if raw.get("order") == 1:
            return "primary"
        if cost_tier == "premium":
            return "premium-exception"
        return str(raw.get("mode") or "fallback")

    def _step_note(self, *, task: str, role: str, cost_tier: str) -> str:
        if role == "primary":
            return "Start here for the task unless a deterministic stop signal is present."
        if role == "premium-exception":
            if task in {"pdf", "image"}:
                return "Premium/media exception is allowed for this task family."
            return "Use only after quality failure or operator approval."
        if cost_tier == "unknown":
            return "Gateway-specific model; verify price and availability before using as a default."
        return "Use when the previous lower-cost step is unavailable or fails deterministic checks."

    def _max_cost_tier(self, task: str, matrix_row: dict[str, Any] | None) -> str:
        if matrix_row:
            return str(matrix_row["requirement"]["max_cost_tier"])
        return str(TASK_GROUPS.get(task, {}).get("max_cost_tier", "premium"))

    def _display_name(
        self,
        task: str,
        matrix_row: dict[str, Any] | None,
        plan_row: dict[str, Any] | None,
    ) -> str:
        if plan_row:
            return str(plan_row["display_name"])
        if matrix_row:
            return str(matrix_row["requirement"]["display_name"])
        return task

    def _recommended_action(
        self,
        task: str,
        failed: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> str:
        if failed:
            return f"Fix fallback chain for {task} before release: {', '.join(item['id'] for item in failed)}."
        if warnings:
            return f"Review fallback chain configuration for {task}: {', '.join(item['id'] for item in warnings)}."
        return "Fallback chain is aligned with cheap-first routing policy."
