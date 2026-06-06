from __future__ import annotations

import re
from typing import Any

from services.billing_usage_quota_policy import (
    ACTION_PREMIUM_MODEL_ESCALATION,
    BillingUsageQuotaPolicyService,
    UsageRequest,
    UsageSnapshot,
)
from services.model_budget import model_budget_decision, normalize_budget_task
from services.model_catalog import estimate_token_cost_usd, model_profile, resolve_model
from services.model_escalation_policy import ModelEscalationPolicyService


FORBIDDEN_KEY_PATTERN = re.compile(
    r"(api[_-]?key|authorization|password|secret|prompt|headers?|raw[_-]?(model[_-]?)?output|raw[_-]?response|legal[_-]?text|document[_-]?text|client[_-]?email|email|request[_-]?body|response[_-]?body|messages?|content)",
    re.IGNORECASE,
)
ALLOWED_AGGREGATE_KEYS = {"prompt_tokens", "completion_tokens"}
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b)"
)

DEFAULT_PAYLOAD = {
    "task": "classification",
    "attempt_index": 1,
    "failure_signals": ["schema_missing_required"],
    "current_model": "auto-fast",
    "prompt_tokens": 1600,
    "completion_tokens": 512,
    "plan_type": "personal",
    "subscription_status": "active",
    "user_role": "user",
    "premium_escalations_used_month": 0,
    "operator_approved": False,
}

TASK_COST_LIMITS = {
    "fast": {"warn_incremental_usd": 0.003, "fail_incremental_usd": 0.010},
    "classification": {"warn_incremental_usd": 0.003, "fail_incremental_usd": 0.010},
    "ocr": {"warn_incremental_usd": 0.005, "fail_incremental_usd": 0.020},
    "review": {"warn_incremental_usd": 0.080, "fail_incremental_usd": 0.250},
    "grounded-research": {"warn_incremental_usd": 0.060, "fail_incremental_usd": 0.180},
    "agentic": {"warn_incremental_usd": 0.030, "fail_incremental_usd": 0.100},
    "pdf": {"warn_incremental_usd": 0.300, "fail_incremental_usd": 1.200},
}


class ModelFailureUpgradeBudgetService:
    """Plan cheap-first failure retries and upgrades from sanitized metadata only."""

    def __init__(
        self,
        escalation_policy: ModelEscalationPolicyService | None = None,
        quota_policy: BillingUsageQuotaPolicyService | None = None,
    ) -> None:
        self.escalation_policy = escalation_policy or ModelEscalationPolicyService()
        self.quota_policy = quota_policy or BillingUsageQuotaPolicyService()

    def build_decision(self, payload: Any = None) -> dict[str, Any]:
        uses_default_payload = payload is None
        data = dict(DEFAULT_PAYLOAD) if uses_default_payload else _dict(payload)
        forbidden_field_count = _count_forbidden_keys(data)
        secret_like_value_count = _count_secret_like_values(data)
        task = normalize_budget_task(_safe_token(data.get("task"), "review"))
        attempt_index = _safe_int(data.get("attempt_index"), default=0)
        prompt_tokens = _bounded_int(data.get("prompt_tokens"), default=0, max_value=250_000)
        completion_tokens = _bounded_int(data.get("completion_tokens"), default=0, max_value=20_000)
        failure_signals = _safe_signal_list(data.get("failure_signals"))
        operator_approved = bool(data.get("operator_approved"))
        current_model = resolve_model(_safe_model(data.get("current_model")) or None, task=task)

        policy = self.escalation_policy.build_policy()
        plan = self._plan_for_task(policy, task)
        escalation = self.escalation_policy.evaluate(task, failure_signals)
        max_attempts = _safe_int(plan.get("max_attempts"), default=1) if plan else 1
        next_step = escalation.get("next_step") if isinstance(escalation.get("next_step"), dict) else None
        next_model = str(next_step.get("resolved_model")) if next_step else current_model
        next_profile = model_profile(next_model)
        current_profile = model_profile(current_model)
        next_budget = model_budget_decision(next_model, task=task)

        current_cost = estimate_token_cost_usd(current_model, prompt_tokens, completion_tokens)
        next_cost = estimate_token_cost_usd(next_model, prompt_tokens, completion_tokens)
        incremental_cost = _incremental_cost(current_cost, next_cost)
        quota_decision = self._quota_decision(
            next_budget.cost_tier,
            plan_type=str(data.get("plan_type") or "personal"),
            subscription_status=str(data.get("subscription_status") or "active"),
            user_role=str(data.get("user_role") or "user"),
            premium_escalations_used_month=_safe_int(data.get("premium_escalations_used_month"), default=0),
            operator_approved=operator_approved,
        )
        checks = self._checks(
            forbidden_field_count=forbidden_field_count,
            secret_like_value_count=secret_like_value_count,
            attempt_index=attempt_index,
            max_attempts=max_attempts,
            escalation=escalation,
            next_budget=next_budget.to_api(),
            quota_decision=quota_decision,
            incremental_cost=incremental_cost,
            task=task,
            next_cost=next_cost,
        )
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        decision = self._decision(
            forbidden_field_count=forbidden_field_count,
            secret_like_value_count=secret_like_value_count,
            attempt_index=attempt_index,
            max_attempts=max_attempts,
            escalation=escalation,
            next_budget=next_budget.to_api(),
            quota_decision=quota_decision,
            blocking=blocking,
            warnings=warnings,
        )
        status = "fail" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "model-failure-upgrade-budget",
            "title": "Model failure upgrade budget",
            "status": status,
            "method": {
                "type": "cheap-first-failure-upgrade-budget",
                "notes": [
                    "Plans the next cheap-first retry or upgrade from sanitized failure metadata.",
                    "Uses local escalation, budget, catalog pricing, and premium quota policy only.",
                    "Does not execute retries, call models, call gateways, write config, or shift traffic.",
                    "Rejects prompts, raw legal text, raw model output, headers, credentials, and identifiers.",
                ],
                "research_basis": [
                    {
                        "id": "frugalgpt",
                        "url": "https://arxiv.org/abs/2305.05176",
                        "signal": "LLM cascades reduce cost by starting with cheaper models and escalating only when needed.",
                    },
                    {
                        "id": "routellm",
                        "url": "https://arxiv.org/abs/2406.18665",
                        "signal": "Router systems can trade off cost and quality by selecting stronger models for harder prompts.",
                    },
                    {
                        "id": "language-model-cascades",
                        "url": "https://arxiv.org/abs/2207.10342",
                        "signal": "Cascade policies need explicit deferral and stopping rules to control cost and quality.",
                    },
                ],
            },
            "payload_shape": self.payload_shape(),
            "summary": {
                "default_payload_used": uses_default_payload,
                "task": task,
                "attempt_index": attempt_index,
                "max_attempts": max_attempts,
                "attempt_budget_remaining": max(0, max_attempts - attempt_index),
                "failure_signal_count": len(failure_signals),
                "operator_approved": operator_approved,
                "current_model_known": current_profile is not None,
                "next_model_known": next_profile is not None,
                "current_cost_usd": current_cost,
                "next_cost_usd": next_cost,
                "incremental_cost_usd": incremental_cost,
                "next_cost_tier": next_budget.cost_tier,
                "premium_quota_allowed": None if quota_decision is None else bool(quota_decision["allowed"]),
                "forbidden_payload_field_count": forbidden_field_count,
                "secret_like_value_count": secret_like_value_count,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
            },
            "decision": {
                "decision": decision,
                "task": task,
                "current_model": current_model,
                "current_cost_tier": current_profile.cost_tier if current_profile else "unknown",
                "next_model": next_model,
                "next_cost_tier": next_budget.cost_tier or "unknown",
                "next_step": _safe_next_step(next_step),
                "policy_decision": escalation.get("decision"),
                "failure_signals": failure_signals,
                "requires_operator_review": bool(next_budget.requires_operator_review),
                "quota_decision": _safe_quota_decision(quota_decision),
                "cost_delta": {
                    "current_cost_usd": current_cost,
                    "next_cost_usd": next_cost,
                    "incremental_cost_usd": incremental_cost,
                },
            },
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(decision, blocking, warnings),
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "headers_included": False,
                "emails_included": False,
                "phone_numbers_included": False,
                "identity_numbers_included": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "output_scope": "task id, failure signal ids, attempt counters, model ids, cost tiers, quota reason codes, and check ids only",
            },
            "claim_boundary": {
                "retry_executed": False,
                "gateway_health_claimed": False,
                "production_accuracy_claimed": False,
                "automatic_traffic_shift_claimed": False,
                "premium_call_authorized": decision == "allow_premium_upgrade_after_operator_review",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_failure_upgrade_budget.py tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def payload_shape(self) -> dict[str, Any]:
        return {
            "required": ["task", "attempt_index", "failure_signals"],
            "optional": [
                "current_model",
                "prompt_tokens",
                "completion_tokens",
                "plan_type",
                "subscription_status",
                "user_role",
                "premium_escalations_used_month",
                "operator_approved",
            ],
            "forbidden": [
                "api_key",
                "authorization",
                "headers",
                "prompt",
                "messages",
                "content",
                "raw_model_output",
                "raw_response",
                "legal_text",
                "document_text",
                "email",
                "phone",
                "identity_number",
            ],
            "example": {
                "task": "classification",
                "attempt_index": 1,
                "failure_signals": ["schema_missing_required"],
                "current_model": "auto-fast",
                "prompt_tokens": 1600,
                "completion_tokens": 512,
                "plan_type": "personal",
                "premium_escalations_used_month": 0,
                "operator_approved": False,
            },
        }

    def _plan_for_task(self, policy: dict[str, Any], task: str) -> dict[str, Any]:
        plans = policy.get("plans") if isinstance(policy, dict) else []
        for plan in plans if isinstance(plans, list) else []:
            if isinstance(plan, dict) and plan.get("task") == task:
                return plan
        return {}

    def _quota_decision(
        self,
        cost_tier: str | None,
        *,
        plan_type: str,
        subscription_status: str,
        user_role: str,
        premium_escalations_used_month: int,
        operator_approved: bool,
    ) -> dict[str, Any] | None:
        if cost_tier != "premium":
            return None
        return self.quota_policy.evaluate(
            UsageSnapshot(
                plan_type=_safe_plan(plan_type),
                subscription_status=_safe_token(subscription_status, "active"),
                user_role=_safe_token(user_role, "user"),
                premium_escalations_used_month=max(0, premium_escalations_used_month),
            ),
            UsageRequest(
                action=ACTION_PREMIUM_MODEL_ESCALATION,
                requested_model_tier="premium",
                operator_approved=operator_approved,
            ),
        )

    def _checks(
        self,
        *,
        forbidden_field_count: int,
        secret_like_value_count: int,
        attempt_index: int,
        max_attempts: int,
        escalation: dict[str, Any],
        next_budget: dict[str, Any],
        quota_decision: dict[str, Any] | None,
        incremental_cost: float | None,
        task: str,
        next_cost: float | None,
    ) -> list[dict[str, Any]]:
        limits = TASK_COST_LIMITS.get(task, TASK_COST_LIMITS["review"])
        quota_allowed = True if quota_decision is None else bool(quota_decision.get("allowed"))
        cost_tier = next_budget.get("cost_tier")
        policy_allows_upgrade = escalation.get("decision") in {"escalate", "verify"}
        non_premium_policy_upgrade = policy_allows_upgrade and cost_tier in {"lowest", "low", "medium"}
        return [
            {
                "id": "sanitized-payload-fields",
                "status": "fail" if forbidden_field_count or secret_like_value_count else "pass",
                "reason": (
                    "Payload contains forbidden field names or secret-like values."
                    if forbidden_field_count or secret_like_value_count
                    else "Payload contains only upgrade decision metadata."
                ),
            },
            {
                "id": "attempt-budget",
                "status": "fail" if attempt_index >= max_attempts else "pass",
                "reason": "Attempt budget is available." if attempt_index < max_attempts else "No retry or upgrade attempts remain.",
            },
            {
                "id": "hard-stop-signal",
                "status": "fail" if escalation.get("decision") == "stop" else "pass",
                "reason": "No hard-stop signal is active." if escalation.get("decision") != "stop" else "Hard-stop signal prevents retry or upgrade.",
            },
            {
                "id": "task-budget-tier",
                "status": "fail" if bool(next_budget.get("is_over_budget")) and cost_tier == "premium" and not quota_allowed else (
                    "warn" if (cost_tier is None or (bool(next_budget.get("is_over_budget")) and not non_premium_policy_upgrade)) else "pass"
                ),
                "reason": "Next model tier is within task budget."
                if (not bool(next_budget.get("is_over_budget")) or non_premium_policy_upgrade) and cost_tier is not None
                else "Next model is over task budget or has unknown tier.",
            },
            {
                "id": "incremental-cost",
                "status": self._cost_status(incremental_cost, limits, next_cost),
                "reason": self._cost_reason(incremental_cost, limits, next_cost),
                "value": incremental_cost,
                "warn_threshold": limits["warn_incremental_usd"],
                "fail_threshold": limits["fail_incremental_usd"],
            },
            {
                "id": "premium-quota-and-approval",
                "status": "fail" if quota_decision is not None and not quota_allowed else "pass",
                "reason": "Premium upgrade quota and approval are available."
                if quota_decision is not None and quota_allowed
                else (
                    "Next model is not premium; premium quota is not required."
                    if quota_decision is None
                    else "Premium upgrade is blocked by quota or operator approval policy."
                ),
            },
            {
                "id": "no-model-or-gateway-call",
                "status": "pass",
                "reason": "Failure upgrade budget is evaluated offline without executing retry or gateway calls.",
            },
        ]

    def _cost_status(self, incremental_cost: float | None, limits: dict[str, float], next_cost: float | None) -> str:
        if next_cost is None or incremental_cost is None:
            return "warn"
        if incremental_cost >= limits["fail_incremental_usd"]:
            return "fail"
        if incremental_cost >= limits["warn_incremental_usd"]:
            return "warn"
        return "pass"

    def _cost_reason(self, incremental_cost: float | None, limits: dict[str, float], next_cost: float | None) -> str:
        if next_cost is None or incremental_cost is None:
            return "Pricing is unavailable for the current or next model; keep the upgrade in maintainer review."
        if incremental_cost >= limits["fail_incremental_usd"]:
            return "Incremental upgrade cost exceeds the task fail threshold."
        if incremental_cost >= limits["warn_incremental_usd"]:
            return "Incremental upgrade cost is allowed only with maintainer review."
        return "Incremental upgrade cost stays within the task budget."

    def _decision(
        self,
        *,
        forbidden_field_count: int,
        secret_like_value_count: int,
        attempt_index: int,
        max_attempts: int,
        escalation: dict[str, Any],
        next_budget: dict[str, Any],
        quota_decision: dict[str, Any] | None,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> str:
        if forbidden_field_count or secret_like_value_count:
            return "reject_unsanitized_payload"
        if escalation.get("decision") == "stop":
            return "stop_hard_signal"
        if attempt_index >= max_attempts:
            return "stop_attempt_budget_exhausted"
        if quota_decision is not None and not quota_decision.get("allowed"):
            return "block_premium_upgrade"
        if blocking:
            return "block_upgrade"
        if next_budget.get("cost_tier") == "premium":
            return "allow_premium_upgrade_after_operator_review"
        if escalation.get("decision") == "escalate":
            return "allow_retry_up"
        if escalation.get("decision") == "verify":
            return "allow_verification_step"
        if warnings:
            return "review_before_upgrade"
        return "continue_cheap_first"

    def _recommended_actions(self, decision: str, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        if decision == "reject_unsanitized_payload":
            actions.append("Resubmit only task ids, failure signal ids, attempt counters, token counts, plan type, and approval booleans.")
        if decision == "block_premium_upgrade":
            actions.append("Keep the current cheap-first route or obtain operator approval and premium quota before using a Pro model.")
        if decision in {"stop_hard_signal", "stop_attempt_budget_exhausted"}:
            actions.append("Stop automatic retries and route the case to deterministic repair or human review.")
        if decision == "allow_retry_up":
            actions.append("Allow one bounded retry on the next non-premium model, then record aggregate outcome metrics.")
        if decision == "allow_verification_step":
            actions.append("Run a verification step before changing model tier or default routing.")
        if decision == "allow_premium_upgrade_after_operator_review":
            actions.append("Use premium only for this exception path and consume quota after the call succeeds.")
        for check in warnings[:3]:
            actions.append(f"Review warning: {check['id']}.")
        for check in blocking[:3]:
            actions.append(f"Resolve blocker: {check['id']}.")
        if not actions:
            actions.append("Continue cheap-first routing and rerun this budget when deterministic failure signals appear.")
        return _dedupe(actions)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _bounded_int(value: Any, *, default: int, max_value: int) -> int:
    return min(max_value, _safe_int(value, default=default))


def _safe_token(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower().replace(" ", "-")[:80]
    if not text or SECRET_VALUE_PATTERN.search(text):
        return fallback
    cleaned = re.sub(r"[^a-z0-9_.:-]+", "-", text).strip("-")
    return cleaned or fallback


def _safe_model(value: Any) -> str | None:
    text = str(value or "").strip()[:120]
    if not text or SECRET_VALUE_PATTERN.search(text):
        return None
    if FORBIDDEN_KEY_PATTERN.search(text):
        return None
    cleaned = re.sub(r"[^A-Za-z0-9_.:/@+-]+", "-", text).strip("-")
    return cleaned or None


def _safe_signal_list(value: Any) -> list[str]:
    if isinstance(value, str):
        raw = [value]
    elif isinstance(value, list):
        raw = value[:20]
    else:
        raw = []
    return _dedupe([_safe_token(item, "") for item in raw if _safe_token(item, "")])


def _safe_plan(value: str) -> str:
    plan = _safe_token(value, "personal")
    return plan if plan in {"free", "personal", "lawyer", "enterprise", "admin"} else "personal"


def _incremental_cost(current_cost: float | None, next_cost: float | None) -> float | None:
    if current_cost is None or next_cost is None:
        return None
    return round(max(0.0, next_cost - current_cost), 8)


def _safe_next_step(next_step: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_step:
        return None
    return {
        "order": _safe_int(next_step.get("order"), default=0),
        "mode": _safe_token(next_step.get("mode"), "unknown"),
        "task": normalize_budget_task(str(next_step.get("task") or "review")),
        "model_alias": _safe_model(next_step.get("model_alias")),
        "resolved_model": _safe_model(next_step.get("resolved_model")) or "",
        "trigger": _safe_token(next_step.get("trigger"), "policy"),
        "requires_operator_review": bool(next_step.get("requires_operator_review")),
        "stop_after_failure": bool(next_step.get("stop_after_failure")),
    }


def _safe_quota_decision(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    reasons = value.get("over_limit_reasons") if isinstance(value.get("over_limit_reasons"), list) else []
    return {
        "status": _safe_token(value.get("status"), "unknown"),
        "allowed": bool(value.get("allowed")),
        "effective_plan_type": _safe_plan(str(value.get("effective_plan_type") or "personal")),
        "remaining_before": {
            "premium_escalations": _safe_int((value.get("remaining_before") or {}).get("premium_escalations"), default=0)
            if isinstance(value.get("remaining_before"), dict)
            else 0
        },
        "remaining_after": {
            "premium_escalations": _safe_int((value.get("remaining_after") or {}).get("premium_escalations"), default=0)
            if isinstance(value.get("remaining_after"), dict)
            else 0
        },
        "over_limit_codes": [_safe_token(item.get("code"), "unknown") for item in reasons if isinstance(item, dict)],
    }


def _count_forbidden_keys(value: Any) -> int:
    if isinstance(value, dict):
        count = sum(
            1
            for key in value
            if str(key) not in ALLOWED_AGGREGATE_KEYS and FORBIDDEN_KEY_PATTERN.search(str(key))
        )
        return count + sum(_count_forbidden_keys(item) for item in value.values())
    if isinstance(value, list):
        return sum(_count_forbidden_keys(item) for item in value)
    return 0


def _count_secret_like_values(value: Any) -> int:
    if isinstance(value, dict):
        return sum(_count_secret_like_values(item) for item in value.values())
    if isinstance(value, list):
        return sum(_count_secret_like_values(item) for item in value)
    if isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        return 1
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
