"""Local billing usage and quota policy.

This module is intentionally deterministic and local-only. It does not call a
payment provider, does not perform network I/O, and does not store prompts,
document text, file names, user IDs, API keys, or payment secrets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from services.product_catalog import PLAN_LIMITS


ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
UNLIMITED_QUOTA_THRESHOLD = 999999

ACTION_DOCUMENT_UPLOAD = "document_upload"
ACTION_REVIEW = "review"
ACTION_GENERATED_DOCUMENT = "generated_document"
ACTION_PREMIUM_MODEL_ESCALATION = "premium_model_escalation"

KNOWN_ACTIONS = {
    ACTION_DOCUMENT_UPLOAD,
    ACTION_REVIEW,
    ACTION_GENERATED_DOCUMENT,
    ACTION_PREMIUM_MODEL_ESCALATION,
}

ACTION_ALIASES = {
    "upload": ACTION_DOCUMENT_UPLOAD,
    "document-upload": ACTION_DOCUMENT_UPLOAD,
    "document_upload": ACTION_DOCUMENT_UPLOAD,
    "review-credit": ACTION_REVIEW,
    "review_credit": ACTION_REVIEW,
    "review": ACTION_REVIEW,
    "generated-doc": ACTION_GENERATED_DOCUMENT,
    "generated_doc": ACTION_GENERATED_DOCUMENT,
    "generated-document": ACTION_GENERATED_DOCUMENT,
    "generated_document": ACTION_GENERATED_DOCUMENT,
    "premium": ACTION_PREMIUM_MODEL_ESCALATION,
    "premium-escalation": ACTION_PREMIUM_MODEL_ESCALATION,
    "premium_model_escalation": ACTION_PREMIUM_MODEL_ESCALATION,
}

CONTENT_FIELD_EXCLUSIONS = (
    "api_key",
    "document_text",
    "file_name",
    "payment_session_id",
    "prompt",
    "raw_content",
    "secret",
    "user_email",
    "user_id",
)


LOCAL_PLAN_LIMITS: dict[str, dict[str, Any]] = {
    "free": {
        "review_credits_monthly": PLAN_LIMITS["free"]["report_quota_monthly"],
        "document_uploads_monthly": 5,
        "document_storage_mb": 100,
        "max_upload_mb": 10,
        "generated_docs_monthly": 2,
        "premium_escalations_monthly": 0,
        "premium_model_allowed": False,
        "premium_requires_operator_approval": True,
        "low_cost_model_first": True,
    },
    "personal": {
        "review_credits_monthly": PLAN_LIMITS["personal"]["report_quota_monthly"],
        "document_uploads_monthly": 50,
        "document_storage_mb": 1000,
        "max_upload_mb": 25,
        "generated_docs_monthly": 20,
        "premium_escalations_monthly": 2,
        "premium_model_allowed": True,
        "premium_requires_operator_approval": True,
        "low_cost_model_first": True,
    },
    "lawyer": {
        "review_credits_monthly": PLAN_LIMITS["lawyer"]["report_quota_monthly"],
        "document_uploads_monthly": 250,
        "document_storage_mb": 5000,
        "max_upload_mb": 50,
        "generated_docs_monthly": 100,
        "premium_escalations_monthly": 10,
        "premium_model_allowed": True,
        "premium_requires_operator_approval": True,
        "low_cost_model_first": True,
    },
    "enterprise": {
        "review_credits_monthly": PLAN_LIMITS["enterprise"]["report_quota_monthly"],
        "document_uploads_monthly": 5000,
        "document_storage_mb": 100000,
        "max_upload_mb": 100,
        "generated_docs_monthly": 1000,
        "premium_escalations_monthly": 100,
        "premium_model_allowed": True,
        "premium_requires_operator_approval": False,
        "low_cost_model_first": True,
    },
    "admin": {
        "review_credits_monthly": UNLIMITED_QUOTA_THRESHOLD,
        "document_uploads_monthly": UNLIMITED_QUOTA_THRESHOLD,
        "document_storage_mb": UNLIMITED_QUOTA_THRESHOLD,
        "max_upload_mb": UNLIMITED_QUOTA_THRESHOLD,
        "generated_docs_monthly": UNLIMITED_QUOTA_THRESHOLD,
        "premium_escalations_monthly": UNLIMITED_QUOTA_THRESHOLD,
        "premium_model_allowed": True,
        "premium_requires_operator_approval": False,
        "low_cost_model_first": False,
    },
}


@dataclass(frozen=True)
class UsageSnapshot:
    plan_type: str
    subscription_status: str = "active"
    user_role: str = "user"
    document_uploads_used_month: int = 0
    document_storage_mb_used: int = 0
    review_credits_used_month: int = 0
    generated_docs_used_month: int = 0
    premium_escalations_used_month: int = 0


@dataclass(frozen=True)
class UsageRequest:
    action: str
    units: int = 1
    upload_size_mb: int = 0
    requested_model_tier: str = "cheap"
    operator_approved: bool = False


@dataclass(frozen=True)
class OverLimitReason:
    code: str
    message: str
    metric: str | None = None
    limit: int | bool | None = None
    used: int | None = None
    requested: int | bool | None = None
    remaining: int | None = None

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UsageDecision:
    status: str
    allowed: bool
    action: str
    plan_type: str
    effective_plan_type: str
    subscription_status: str
    requested_units: int
    requested_upload_size_mb: int
    requested_model_tier: str
    recommended_model_tier: str
    limits: dict[str, Any]
    remaining_before: dict[str, int]
    remaining_after: dict[str, int]
    consumption: dict[str, int]
    over_limit_reasons: tuple[OverLimitReason, ...]
    policy_notes: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "allowed": self.allowed,
            "action": self.action,
            "plan_type": self.plan_type,
            "effective_plan_type": self.effective_plan_type,
            "subscription_status": self.subscription_status,
            "requested_units": self.requested_units,
            "requested_upload_size_mb": self.requested_upload_size_mb,
            "requested_model_tier": self.requested_model_tier,
            "recommended_model_tier": self.recommended_model_tier,
            "limits": dict(self.limits),
            "remaining_before": dict(self.remaining_before),
            "remaining_after": dict(self.remaining_after),
            "consumption": dict(self.consumption),
            "over_limit_reasons": [reason.to_api() for reason in self.over_limit_reasons],
            "policy_notes": list(self.policy_notes),
            "requires_real_payment": False,
            "requires_network": False,
        }


@dataclass(frozen=True)
class PrivacySafeUsageEvent:
    plan_type: str
    action: str
    allowed: bool
    units: int = 1
    requested_model_tier: str = "cheap"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    over_limit_codes: tuple[str, ...] = ()


class BillingUsageQuotaPolicyService:
    """Pure local quota policy for a low-cost model-first product."""

    def plan_limits(self) -> dict[str, dict[str, Any]]:
        return {plan: dict(limits) for plan, limits in LOCAL_PLAN_LIMITS.items()}

    def evaluate(self, snapshot: UsageSnapshot, request: UsageRequest) -> dict[str, Any]:
        decision = self.evaluate_decision(snapshot, request)
        return decision.to_api()

    def evaluate_decision(self, snapshot: UsageSnapshot, request: UsageRequest) -> UsageDecision:
        action = normalize_action(request.action)
        requested_units = max(1, _safe_int(request.units))
        requested_upload_size_mb = max(0, _safe_int(request.upload_size_mb))
        requested_model_tier = _model_tier(request.requested_model_tier)
        effective_plan = _effective_plan(snapshot)
        limits = LOCAL_PLAN_LIMITS.get(effective_plan)

        if limits is None:
            reason = OverLimitReason(
                code="unknown_plan",
                message="Plan type is not configured for billing usage quotas.",
                metric="plan_type",
            )
            return self._decision(
                snapshot=snapshot,
                action=action,
                requested_units=requested_units,
                requested_upload_size_mb=requested_upload_size_mb,
                requested_model_tier=requested_model_tier,
                limits={},
                effective_plan=effective_plan,
                reasons=[reason],
            )

        remaining_before = _remaining(snapshot, limits)
        consumption = self._consumption_for(action, requested_units, requested_upload_size_mb)
        reasons: list[OverLimitReason] = []

        if action not in KNOWN_ACTIONS:
            reasons.append(
                OverLimitReason(
                    code="unknown_action",
                    message="Usage action is not configured for quota evaluation.",
                    metric="action",
                )
            )

        if (
            snapshot.subscription_status not in ACTIVE_SUBSCRIPTION_STATUSES
            and effective_plan != "admin"
        ):
            reasons.append(
                OverLimitReason(
                    code="inactive_subscription",
                    message="Subscription must be active or trialing before consuming usage.",
                    metric="subscription_status",
                )
            )

        if requested_model_tier == "premium" and action != ACTION_PREMIUM_MODEL_ESCALATION:
            reasons.append(
                OverLimitReason(
                    code="premium_escalation_required",
                    message="Premium model use must be evaluated as an explicit escalation before the task runs.",
                    metric="requested_model_tier",
                    limit=True,
                    requested=True,
                )
            )

        if action == ACTION_DOCUMENT_UPLOAD:
            reasons.extend(
                self._document_upload_reasons(
                    limits=limits,
                    snapshot=snapshot,
                    requested_units=requested_units,
                    requested_upload_size_mb=requested_upload_size_mb,
                )
            )
        elif action == ACTION_REVIEW:
            reasons.extend(
                self._quota_reasons(
                    metric="review_credits",
                    code="review_credits_exhausted",
                    message="Monthly review credits are exhausted.",
                    limit=_safe_int(limits["review_credits_monthly"]),
                    used=max(0, _safe_int(snapshot.review_credits_used_month)),
                    requested=requested_units,
                )
            )
        elif action == ACTION_GENERATED_DOCUMENT:
            reasons.extend(
                self._quota_reasons(
                    metric="generated_docs",
                    code="generated_docs_exhausted",
                    message="Monthly generated document quota is exhausted.",
                    limit=_safe_int(limits["generated_docs_monthly"]),
                    used=max(0, _safe_int(snapshot.generated_docs_used_month)),
                    requested=requested_units,
                )
            )
        elif action == ACTION_PREMIUM_MODEL_ESCALATION:
            reasons.extend(
                self._premium_escalation_reasons(
                    limits=limits,
                    snapshot=snapshot,
                    requested_units=requested_units,
                    operator_approved=request.operator_approved,
                )
            )

        allowed = not reasons
        remaining_after = _consume_remaining(remaining_before, consumption) if allowed else remaining_before
        return UsageDecision(
            status="ready" if allowed else "blocked",
            allowed=allowed,
            action=action,
            plan_type=snapshot.plan_type,
            effective_plan_type=effective_plan,
            subscription_status=snapshot.subscription_status,
            requested_units=requested_units,
            requested_upload_size_mb=requested_upload_size_mb,
            requested_model_tier=requested_model_tier,
            recommended_model_tier=self._recommended_model_tier(limits, requested_model_tier, action),
            limits=dict(limits),
            remaining_before=remaining_before,
            remaining_after=remaining_after,
            consumption=consumption,
            over_limit_reasons=tuple(reasons),
            policy_notes=tuple(self._policy_notes(limits=limits, action=action, allowed=allowed)),
        )

    def aggregate_usage(
        self,
        events: Iterable[PrivacySafeUsageEvent | Mapping[str, Any]],
    ) -> dict[str, Any]:
        totals = {
            "events": 0,
            "allowed_events": 0,
            "blocked_events": 0,
            "units": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "premium_model_events": 0,
        }
        by_plan: dict[str, dict[str, int]] = {}
        by_action: dict[str, dict[str, int]] = {}
        over_limit_reasons: dict[str, int] = {}

        for raw_event in events:
            event = _event_mapping(raw_event)
            plan = _known_or_unknown_plan(str(event.get("plan_type") or "unknown"))
            action = normalize_action(str(event.get("action") or "unknown"))
            allowed = bool(event.get("allowed"))
            units = max(0, _safe_int(event.get("units"), default=1))
            prompt_tokens = max(0, _safe_int(event.get("prompt_tokens")))
            completion_tokens = max(0, _safe_int(event.get("completion_tokens")))
            model_tier = _model_tier(str(event.get("requested_model_tier") or "cheap"))

            totals["events"] += 1
            totals["units"] += units
            totals["prompt_tokens"] += prompt_tokens
            totals["completion_tokens"] += completion_tokens
            totals["total_tokens"] += prompt_tokens + completion_tokens
            if allowed:
                totals["allowed_events"] += 1
            else:
                totals["blocked_events"] += 1
            if model_tier == "premium" or action == ACTION_PREMIUM_MODEL_ESCALATION:
                totals["premium_model_events"] += 1

            _increment_bucket(by_plan, plan, "events", 1)
            _increment_bucket(by_plan, plan, "units", units)
            _increment_bucket(by_action, action, "events", 1)
            _increment_bucket(by_action, action, "units", units)
            _increment_bucket(by_action, action, "allowed_events" if allowed else "blocked_events", 1)

            for code in _safe_codes(event.get("over_limit_codes")):
                over_limit_reasons[code] = over_limit_reasons.get(code, 0) + 1

        return {
            "status": "ready",
            "scope": "billing-usage-quota",
            "privacy_mode": "aggregate-only",
            "totals": totals,
            "by_plan": dict(sorted(by_plan.items())),
            "by_action": dict(sorted(by_action.items())),
            "over_limit_reasons": dict(sorted(over_limit_reasons.items())),
            "content_fields_recorded": [],
            "excluded_fields": list(CONTENT_FIELD_EXCLUSIONS),
            "requires_real_payment": False,
            "requires_network": False,
        }

    def build_policy_evidence(self) -> dict[str, Any]:
        return {
            "status": "backend_evidence_ready",
            "scope": "billing-usage-quota",
            "model_strategy": "low-cost-model-first",
            "implemented_controls": [
                "plan-limit-snapshot",
                "document-upload-count-and-size-guard",
                "document-storage-guard",
                "review-credit-guard",
                "generated-document-guard",
                "premium-model-escalation-guard",
                "structured-over-limit-reasons",
                "privacy-safe-usage-aggregation",
            ],
            "plan_limits": self.plan_limits(),
            "non_goals": [
                "real-payment-processing",
                "payment-provider-webhooks",
                "network-calls",
                "secret-storage",
                "router-integration",
                "release-or-ledger-changes",
            ],
            "validation_commands": [
                "python -m pytest tests/test_billing_usage_quota_policy.py -q",
                "python -m compileall services/billing_usage_quota_policy.py tests/test_billing_usage_quota_policy.py",
            ],
            "privacy_note": (
                "Usage aggregation records counters, plan/action categories, model tier, token counts, "
                "and reason codes only; prompts, document text, file names, user IDs, and secrets are excluded."
            ),
        }

    def _document_upload_reasons(
        self,
        *,
        limits: Mapping[str, Any],
        snapshot: UsageSnapshot,
        requested_units: int,
        requested_upload_size_mb: int,
    ) -> list[OverLimitReason]:
        reasons: list[OverLimitReason] = []
        upload_limit = _safe_int(limits["document_uploads_monthly"])
        upload_used = max(0, _safe_int(snapshot.document_uploads_used_month))
        storage_limit = _safe_int(limits["document_storage_mb"])
        storage_used = max(0, _safe_int(snapshot.document_storage_mb_used))
        max_upload_mb = _safe_int(limits["max_upload_mb"])
        requested_storage = requested_units * requested_upload_size_mb

        reasons.extend(
            self._quota_reasons(
                metric="document_uploads",
                code="document_uploads_exhausted",
                message="Monthly document upload quota is exhausted.",
                limit=upload_limit,
                used=upload_used,
                requested=requested_units,
            )
        )
        if requested_upload_size_mb > max_upload_mb:
            reasons.append(
                OverLimitReason(
                    code="document_upload_too_large",
                    message="Document upload exceeds the per-file size limit.",
                    metric="max_upload_mb",
                    limit=max_upload_mb,
                    used=None,
                    requested=requested_upload_size_mb,
                    remaining=max(0, max_upload_mb),
                )
            )
        reasons.extend(
            self._quota_reasons(
                metric="document_storage_mb",
                code="document_storage_exhausted",
                message="Document storage quota is exhausted.",
                limit=storage_limit,
                used=storage_used,
                requested=requested_storage,
            )
        )
        return reasons

    def _premium_escalation_reasons(
        self,
        *,
        limits: Mapping[str, Any],
        snapshot: UsageSnapshot,
        requested_units: int,
        operator_approved: bool,
    ) -> list[OverLimitReason]:
        reasons: list[OverLimitReason] = []
        premium_allowed = bool(limits["premium_model_allowed"])
        premium_requires_approval = bool(limits["premium_requires_operator_approval"])
        premium_limit = _safe_int(limits["premium_escalations_monthly"])
        premium_used = max(0, _safe_int(snapshot.premium_escalations_used_month))

        if not premium_allowed:
            reasons.append(
                OverLimitReason(
                    code="premium_model_not_allowed",
                    message="The current plan does not include premium model escalations.",
                    metric="premium_model_allowed",
                    limit=False,
                    requested=True,
                )
            )
        if premium_requires_approval and not operator_approved:
            reasons.append(
                OverLimitReason(
                    code="premium_operator_approval_required",
                    message="Premium escalation requires explicit local operator approval.",
                    metric="operator_approved",
                    limit=True,
                    requested=False,
                )
            )
        reasons.extend(
            self._quota_reasons(
                metric="premium_escalations",
                code="premium_escalations_exhausted",
                message="Monthly premium model escalation quota is exhausted.",
                limit=premium_limit,
                used=premium_used,
                requested=requested_units,
            )
        )
        return reasons

    @staticmethod
    def _quota_reasons(
        *,
        metric: str,
        code: str,
        message: str,
        limit: int,
        used: int,
        requested: int,
    ) -> list[OverLimitReason]:
        if _is_unlimited(limit):
            return []
        remaining = max(0, limit - used)
        if requested <= remaining:
            return []
        return [
            OverLimitReason(
                code=code,
                message=message,
                metric=metric,
                limit=limit,
                used=used,
                requested=requested,
                remaining=remaining,
            )
        ]

    @staticmethod
    def _consumption_for(action: str, requested_units: int, requested_upload_size_mb: int) -> dict[str, int]:
        if action == ACTION_DOCUMENT_UPLOAD:
            return {
                "document_uploads": requested_units,
                "document_storage_mb": requested_units * requested_upload_size_mb,
            }
        if action == ACTION_REVIEW:
            return {"review_credits": requested_units}
        if action == ACTION_GENERATED_DOCUMENT:
            return {"generated_docs": requested_units}
        if action == ACTION_PREMIUM_MODEL_ESCALATION:
            return {"premium_escalations": requested_units}
        return {}

    @staticmethod
    def _recommended_model_tier(
        limits: Mapping[str, Any],
        requested_model_tier: str,
        action: str,
    ) -> str:
        if action == ACTION_PREMIUM_MODEL_ESCALATION and requested_model_tier == "premium":
            return "premium"
        if bool(limits.get("low_cost_model_first", True)):
            return "cheap"
        return requested_model_tier

    @staticmethod
    def _policy_notes(*, limits: Mapping[str, Any], action: str, allowed: bool) -> list[str]:
        notes = ["Quota decisions are local and deterministic; no payment gateway is called."]
        if limits.get("low_cost_model_first", True):
            notes.append("Default model route is cheap-first; premium use must be an explicit escalation.")
        if action == ACTION_PREMIUM_MODEL_ESCALATION and allowed:
            notes.append("Consume one premium escalation only after the premium model call succeeds.")
        elif allowed:
            notes.append("Consume quota only after the corresponding workflow completes successfully.")
        return notes

    @staticmethod
    def _decision(
        *,
        snapshot: UsageSnapshot,
        action: str,
        requested_units: int,
        requested_upload_size_mb: int,
        requested_model_tier: str,
        limits: dict[str, Any],
        effective_plan: str,
        reasons: list[OverLimitReason],
    ) -> UsageDecision:
        remaining = _remaining(snapshot, limits) if limits else {}
        return UsageDecision(
            status="blocked",
            allowed=False,
            action=action,
            plan_type=snapshot.plan_type,
            effective_plan_type=effective_plan,
            subscription_status=snapshot.subscription_status,
            requested_units=requested_units,
            requested_upload_size_mb=requested_upload_size_mb,
            requested_model_tier=requested_model_tier,
            recommended_model_tier="cheap",
            limits=dict(limits),
            remaining_before=remaining,
            remaining_after=remaining,
            consumption={},
            over_limit_reasons=tuple(reasons),
            policy_notes=("Quota decisions are local and deterministic; no payment gateway is called.",),
        )


def normalize_action(action: str | None) -> str:
    value = (action or "").strip().lower().replace(" ", "_")
    return ACTION_ALIASES.get(value, value or "unknown")


def _effective_plan(snapshot: UsageSnapshot) -> str:
    return "admin" if snapshot.user_role == "admin" else (snapshot.plan_type or "").strip().lower()


def _remaining(snapshot: UsageSnapshot, limits: Mapping[str, Any]) -> dict[str, int]:
    return {
        "document_uploads": _remaining_count(
            _safe_int(limits.get("document_uploads_monthly")),
            max(0, _safe_int(snapshot.document_uploads_used_month)),
        ),
        "document_storage_mb": _remaining_count(
            _safe_int(limits.get("document_storage_mb")),
            max(0, _safe_int(snapshot.document_storage_mb_used)),
        ),
        "review_credits": _remaining_count(
            _safe_int(limits.get("review_credits_monthly")),
            max(0, _safe_int(snapshot.review_credits_used_month)),
        ),
        "generated_docs": _remaining_count(
            _safe_int(limits.get("generated_docs_monthly")),
            max(0, _safe_int(snapshot.generated_docs_used_month)),
        ),
        "premium_escalations": _remaining_count(
            _safe_int(limits.get("premium_escalations_monthly")),
            max(0, _safe_int(snapshot.premium_escalations_used_month)),
        ),
    }


def _consume_remaining(remaining: Mapping[str, int], consumption: Mapping[str, int]) -> dict[str, int]:
    consumed = dict(remaining)
    for metric, units in consumption.items():
        current = consumed.get(metric, 0)
        if _is_unlimited(current):
            consumed[metric] = current
        else:
            consumed[metric] = max(0, current - max(0, _safe_int(units)))
    return consumed


def _remaining_count(limit: int, used: int) -> int:
    if _is_unlimited(limit):
        return UNLIMITED_QUOTA_THRESHOLD
    return max(0, limit - used)


def _is_unlimited(limit: int) -> bool:
    return limit >= UNLIMITED_QUOTA_THRESHOLD


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _model_tier(value: str | None) -> str:
    normalized = (value or "cheap").strip().lower()
    if normalized in {"lowest", "low", "cheap", "standard", "balanced", "premium"}:
        return "cheap" if normalized in {"lowest", "low", "standard"} else normalized
    return "cheap"


def _known_or_unknown_plan(plan_type: str) -> str:
    normalized = (plan_type or "unknown").strip().lower()
    return normalized if normalized in LOCAL_PLAN_LIMITS else "unknown"


def _event_mapping(event: PrivacySafeUsageEvent | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(event, PrivacySafeUsageEvent):
        return asdict(event)
    return event


def _increment_bucket(bucket: dict[str, dict[str, int]], key: str, metric: str, amount: int) -> None:
    item = bucket.setdefault(key, {})
    item[metric] = item.get(metric, 0) + amount


def _safe_codes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raw_codes: Iterable[Any] = (value,)
    else:
        try:
            raw_codes = tuple(value)
        except TypeError:
            raw_codes = (value,)
    return tuple(
        sorted(
            {
                str(code).strip().lower()
                for code in raw_codes
                if str(code).strip()
            }
        )
    )
