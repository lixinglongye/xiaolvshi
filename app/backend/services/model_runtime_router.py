from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import ModelBudgetDecision, model_budget_decision
from services.model_budget import TASK_GROUPS
from services.model_catalog import canonical_model_id, model_profile
from services.model_task_inference import task_inference_policy_for_api


ROUTE_REASON_CODES = (
    "task_default_selected",
    "known_catalog_model",
    "unknown_catalog_model",
    "unverified_price_tier",
    "gateway_passthrough",
    "unknown_gateway_routed_to_recommended",
    "explicit_gateway_passthrough_allowed",
    "lifecycle_preview",
    "lifecycle_review",
    "lifecycle_non_stable",
    "non_stable_model_routed_to_recommended",
    "explicit_non_stable_model_allowed",
    "over_task_budget",
    "operator_review_required",
    "routed_to_recommended_model",
    "explicit_over_budget_allowed",
    "within_task_budget",
    "resolved_to_recommended_model",
    "unknown_reason_code",
)


@dataclass(frozen=True)
class RuntimeModelRoute:
    task: str
    requested_model: str | None
    requested_resolved_model: str
    requested_canonical_model: str | None
    requested_cost_tier: str | None
    requested_model_status: str
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
    explicit_model_requested: bool
    explicit_model_fit_status: str
    explicit_model_fit_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    reason: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        data["explicit_model_fit_reason_codes"] = list(self.explicit_model_fit_reason_codes)
        return data


def resolve_runtime_model(
    model: str | None,
    *,
    task: str = "fast",
    allow_over_budget_model: bool = False,
) -> RuntimeModelRoute:
    """Resolve a request model with cheap-first runtime enforcement."""

    requested = (model or "").strip() or None
    requested_decision = model_budget_decision(requested, task=task)
    requested_profile = model_profile(requested_decision.resolved_model)
    explicit_model_requested = _explicit_model_requested(requested)
    runtime_review_required = _requires_runtime_review(
        requested_decision,
        explicit_model_requested=explicit_model_requested,
        requested_profile=requested_profile,
    )
    should_use_recommended = _should_use_recommended(
        requested_decision,
        explicit_model_requested=explicit_model_requested,
        requested_profile=requested_profile,
        allow_over_budget_model=allow_over_budget_model,
    )
    selected_decision = (
        model_budget_decision(requested_decision.recommended_model, task=requested_decision.task)
        if should_use_recommended
        else requested_decision
    )
    reason_codes = _route_reason_codes(
        requested_decision,
        selected_decision,
        requested_profile=requested_profile,
        explicit_model_requested=explicit_model_requested,
        runtime_review_required=runtime_review_required,
        allow_over_budget_model=allow_over_budget_model,
        routed_to_recommended_model=should_use_recommended,
    )

    return RuntimeModelRoute(
        task=selected_decision.task,
        requested_model=requested,
        requested_resolved_model=requested_decision.resolved_model,
        requested_canonical_model=canonical_model_id(requested_decision.resolved_model),
        requested_cost_tier=requested_profile.cost_tier if requested_profile else None,
        requested_model_status=requested_profile.status if requested_profile else "unknown",
        resolved_model=selected_decision.resolved_model,
        budget_mode=selected_decision.budget_mode,
        cost_tier=selected_decision.cost_tier,
        max_cost_tier=selected_decision.max_cost_tier,
        is_known_model=selected_decision.is_known_model,
        is_over_budget=requested_decision.is_over_budget,
        requires_operator_review=runtime_review_required,
        recommended_model=requested_decision.recommended_model,
        allow_over_budget_model=allow_over_budget_model,
        routed_to_recommended_model=should_use_recommended,
        explicit_model_requested=explicit_model_requested,
        explicit_model_fit_status=_explicit_model_fit_status(
            explicit_model_requested=explicit_model_requested,
            runtime_review_required=runtime_review_required,
            allow_over_budget_model=allow_over_budget_model,
            routed_to_recommended_model=should_use_recommended,
        ),
        explicit_model_fit_reason_codes=tuple(
            code
            for code in reason_codes
            if code
            in {
                "unknown_catalog_model",
                "unverified_price_tier",
                "unknown_gateway_routed_to_recommended",
                "explicit_gateway_passthrough_allowed",
                "lifecycle_preview",
                "lifecycle_review",
                "lifecycle_non_stable",
                "non_stable_model_routed_to_recommended",
                "explicit_non_stable_model_allowed",
                "over_task_budget",
                "operator_review_required",
                "routed_to_recommended_model",
                "explicit_over_budget_allowed",
            }
        ),
        reason_codes=reason_codes,
        reason=_route_reason(
            requested_decision,
            selected_decision,
            requested_profile=requested_profile,
            explicit_model_requested=explicit_model_requested,
            runtime_review_required=runtime_review_required,
            allow_over_budget_model=allow_over_budget_model,
            routed_to_recommended_model=should_use_recommended,
        ),
    )


def _should_use_recommended(
    decision: ModelBudgetDecision,
    *,
    explicit_model_requested: bool,
    requested_profile: Any,
    allow_over_budget_model: bool,
) -> bool:
    if allow_over_budget_model:
        return False
    if decision.is_over_budget or decision.requires_operator_review:
        return True
    return _explicit_model_needs_fit_review(
        decision,
        explicit_model_requested=explicit_model_requested,
        requested_profile=requested_profile,
    )


def _route_reason_codes(
    requested_decision: ModelBudgetDecision,
    selected_decision: ModelBudgetDecision,
    *,
    requested_profile: Any,
    explicit_model_requested: bool,
    runtime_review_required: bool,
    allow_over_budget_model: bool,
    routed_to_recommended_model: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    non_stable_status = _non_stable_status(requested_profile)
    if not explicit_model_requested:
        codes.append("task_default_selected")
    if not requested_decision.is_known_model:
        codes.extend(["unknown_catalog_model", "unverified_price_tier"])
        if routed_to_recommended_model:
            codes.append("unknown_gateway_routed_to_recommended")
        else:
            codes.append("gateway_passthrough")
            if explicit_model_requested and allow_over_budget_model:
                codes.append("explicit_gateway_passthrough_allowed")
    else:
        codes.append("known_catalog_model")
    if non_stable_status:
        codes.append(_lifecycle_reason_code(non_stable_status))
        if routed_to_recommended_model:
            codes.append("non_stable_model_routed_to_recommended")
        elif explicit_model_requested and allow_over_budget_model:
            codes.append("explicit_non_stable_model_allowed")
    if requested_decision.is_over_budget:
        codes.append("over_task_budget")
    if runtime_review_required:
        codes.append("operator_review_required")
    if routed_to_recommended_model:
        codes.append("routed_to_recommended_model")
    elif allow_over_budget_model and (
        requested_decision.is_over_budget or requested_decision.requires_operator_review
    ):
        codes.append("explicit_over_budget_allowed")
    elif allow_over_budget_model and runtime_review_required:
        pass
    else:
        codes.append("within_task_budget")
    if selected_decision.resolved_model == requested_decision.recommended_model:
        codes.append("resolved_to_recommended_model")
    return tuple(_dedupe(codes))


def _route_reason(
    requested_decision: ModelBudgetDecision,
    selected_decision: ModelBudgetDecision,
    *,
    requested_profile: Any,
    explicit_model_requested: bool,
    runtime_review_required: bool,
    allow_over_budget_model: bool,
    routed_to_recommended_model: bool,
) -> str:
    if routed_to_recommended_model:
        if explicit_model_requested and not requested_decision.is_known_model:
            return (
                f"Requested gateway model {requested_decision.resolved_model} is not in the local catalog; "
                f"routed to {selected_decision.resolved_model} until price, lifecycle, and task fit are reviewed."
            )
        non_stable_status = _non_stable_status(requested_profile)
        if explicit_model_requested and non_stable_status:
            return (
                f"Requested model {requested_decision.resolved_model} has lifecycle status {non_stable_status}; "
                f"routed to {selected_decision.resolved_model} until it is reviewed for runtime use."
            )
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
            f"Gateway-specific model {requested_decision.resolved_model} is allowed by explicit review exception, "
            "but price, lifecycle, and tier are unverified."
        )
    non_stable_status = _non_stable_status(requested_profile)
    if explicit_model_requested and runtime_review_required and non_stable_status:
        return (
            f"Non-stable model {requested_decision.resolved_model} was allowed explicitly for "
            f"{requested_decision.task}; lifecycle status is {non_stable_status}."
        )
    return f"Model {selected_decision.resolved_model} is within the {selected_decision.task} budget."


def _explicit_model_requested(requested_model: str | None) -> bool:
    value = (requested_model or "").strip().lower()
    if not value:
        return False
    return not (value == "auto" or value.startswith("auto-"))


def _requires_runtime_review(
    decision: ModelBudgetDecision,
    *,
    explicit_model_requested: bool,
    requested_profile: Any,
) -> bool:
    return bool(
        decision.requires_operator_review
        or _explicit_model_needs_fit_review(
            decision,
            explicit_model_requested=explicit_model_requested,
            requested_profile=requested_profile,
        )
    )


def _explicit_model_needs_fit_review(
    decision: ModelBudgetDecision,
    *,
    explicit_model_requested: bool,
    requested_profile: Any,
) -> bool:
    if not explicit_model_requested:
        return False
    if not decision.is_known_model:
        return True
    return _non_stable_status(requested_profile) != ""


def _non_stable_status(profile: Any) -> str:
    status = str(getattr(profile, "status", "") or "").strip().lower()
    return "" if status in {"", "stable"} else status


def _lifecycle_reason_code(status: str) -> str:
    if status == "preview":
        return "lifecycle_preview"
    if status == "review":
        return "lifecycle_review"
    return "lifecycle_non_stable"


def _explicit_model_fit_status(
    *,
    explicit_model_requested: bool,
    runtime_review_required: bool,
    allow_over_budget_model: bool,
    routed_to_recommended_model: bool,
) -> str:
    if not explicit_model_requested:
        return "default"
    if routed_to_recommended_model:
        return "enforced"
    if allow_over_budget_model and runtime_review_required:
        return "allowed_review_exception"
    if runtime_review_required:
        return "review_required"
    return "ready"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


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
            "Unknown gateway-specific explicit model names are downgraded to the task recommended model unless allow_over_budget_model is true.",
            "Preview or review-lifecycle explicit models are downgraded to stable task recommendations unless allow_over_budget_model is true.",
            "Premium models outside PDF/image exception paths require explicit allowance before runtime use.",
            "Usage counters record the normalized task, not prompt text or document content.",
        ],
        "auto_task_inference": task_inference_policy_for_api(),
        "task_defaults": [
            model_budget_decision(None, task=task).to_api()
            for task in TASK_GROUPS
        ],
    }
