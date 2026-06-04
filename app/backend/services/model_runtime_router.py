from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import ModelBudgetDecision, model_budget_decision
from services.model_budget import TASK_GROUPS
from services.model_task_inference import task_inference_policy_for_api


@dataclass(frozen=True)
class RuntimeModelRoute:
    task: str
    requested_model: str | None
    requested_resolved_model: str
    resolved_model: str
    budget_mode: str
    cost_tier: str | None
    max_cost_tier: str
    is_known_model: bool
    is_over_budget: bool
    requires_operator_review: bool
    recommended_model: str
    allow_over_budget_model: bool
    routed_to_recommended_model: bool
    reason: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


def resolve_runtime_model(
    model: str | None,
    *,
    task: str = "fast",
    allow_over_budget_model: bool = False,
) -> RuntimeModelRoute:
    """Resolve a request model with cheap-first runtime enforcement."""

    requested = (model or "").strip() or None
    requested_decision = model_budget_decision(requested, task=task)
    should_use_recommended = _should_use_recommended(
        requested_decision,
        allow_over_budget_model=allow_over_budget_model,
    )
    selected_decision = (
        model_budget_decision(requested_decision.recommended_model, task=requested_decision.task)
        if should_use_recommended
        else requested_decision
    )

    return RuntimeModelRoute(
        task=selected_decision.task,
        requested_model=requested,
        requested_resolved_model=requested_decision.resolved_model,
        resolved_model=selected_decision.resolved_model,
        budget_mode=selected_decision.budget_mode,
        cost_tier=selected_decision.cost_tier,
        max_cost_tier=selected_decision.max_cost_tier,
        is_known_model=selected_decision.is_known_model,
        is_over_budget=requested_decision.is_over_budget,
        requires_operator_review=requested_decision.requires_operator_review,
        recommended_model=requested_decision.recommended_model,
        allow_over_budget_model=allow_over_budget_model,
        routed_to_recommended_model=should_use_recommended,
        reason=_route_reason(
            requested_decision,
            selected_decision,
            allow_over_budget_model=allow_over_budget_model,
            routed_to_recommended_model=should_use_recommended,
        ),
    )


def _should_use_recommended(
    decision: ModelBudgetDecision,
    *,
    allow_over_budget_model: bool,
) -> bool:
    if allow_over_budget_model:
        return False
    return decision.is_over_budget or decision.requires_operator_review


def _route_reason(
    requested_decision: ModelBudgetDecision,
    selected_decision: ModelBudgetDecision,
    *,
    allow_over_budget_model: bool,
    routed_to_recommended_model: bool,
) -> str:
    if routed_to_recommended_model:
        return (
            f"Requested model {requested_decision.resolved_model} is above the {requested_decision.task} budget "
            f"or requires operator review; routed to {selected_decision.resolved_model}."
        )
    if allow_over_budget_model and (
        requested_decision.is_over_budget or requested_decision.requires_operator_review
    ):
        return (
            f"Over-budget model {requested_decision.resolved_model} was allowed explicitly for "
            f"{requested_decision.task}."
        )
    if not requested_decision.is_known_model:
        return (
            f"Gateway-specific model {requested_decision.resolved_model} is allowed, but price and tier are unverified."
        )
    return f"Model {selected_decision.resolved_model} is within the {selected_decision.task} budget."


def runtime_router_policy_for_api() -> dict[str, Any]:
    """Expose runtime routing rules without leaking prompts or credentials."""
    return {
        "status": "ready",
        "request_fields": {
            "task": "Selects the task budget and default model. Use auto to infer from messages.",
            "model": "Optional model name or alias. Omitted values use the task default.",
            "allow_over_budget_model": (
                "False by default. When false, over-budget or operator-review models route to the task recommended model."
            ),
        },
        "enforcement": [
            "Default text calls use deterministic task inference instead of always using fast routing.",
            "Explicit over-budget models are downgraded to the task recommended model unless allow_over_budget_model is true.",
            "Premium models outside PDF/image exception paths require explicit allowance before runtime use.",
            "Gateway-specific model names remain pass-through, but pricing is marked unverified.",
            "Usage counters record the normalized task, not prompt text or document content.",
        ],
        "auto_task_inference": task_inference_policy_for_api(),
        "task_defaults": [
            model_budget_decision(None, task=task).to_api()
            for task in TASK_GROUPS
        ],
    }
