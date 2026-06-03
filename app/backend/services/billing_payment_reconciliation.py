"""Privacy-safe local billing payment reconciliation policy.

This module records only hashed provider/invoice/plan-change references and
local state decisions. It does not call a payment provider and must not be used
as proof that real settlement completed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Iterable, Mapping


SAFE_MODEL_FIELDS = {
    "provider_event_ref_hash",
    "invoice_ref_hash",
    "plan_change_ref_hash",
    "status",
    "reason_codes",
    "amount_minor",
    "currency",
}

SENSITIVE_FIELD_FRAGMENTS = (
    "account",
    "card",
    "customer",
    "email",
    "password",
    "secret",
    "session",
    "token",
    "user",
)

PROVIDER_STATUS_ALIASES = {
    "invoice.paid": "provider_paid_observed",
    "paid": "provider_paid_observed",
    "payment_succeeded": "provider_paid_observed",
    "succeeded": "provider_paid_observed",
    "invoice.payment_failed": "payment_failed",
    "payment_failed": "payment_failed",
    "failed": "payment_failed",
    "invoice.payment_action_required": "payment_action_required",
    "payment_action_required": "payment_action_required",
    "invoice.voided": "void",
    "voided": "void",
    "void": "void",
    "charge.refunded": "refund_observed",
    "invoice.refunded": "refund_observed",
    "refunded": "refund_observed",
    "refund_observed": "refund_observed",
    "charge.dispute.created": "dispute_observed",
    "invoice.disputed": "dispute_observed",
    "disputed": "dispute_observed",
    "dispute_observed": "dispute_observed",
}

KNOWN_INVOICE_STATUSES = {
    "draft",
    "open",
    "payment_pending",
    "payment_action_required",
    "payment_failed",
    "provider_paid_observed",
    "refund_observed",
    "dispute_observed",
    "void",
}

INVOICE_TRANSITIONS = {
    "draft": {"open", "void"},
    "open": {
        "payment_pending",
        "payment_action_required",
        "payment_failed",
        "provider_paid_observed",
        "void",
    },
    "payment_pending": {
        "payment_action_required",
        "payment_failed",
        "provider_paid_observed",
        "void",
    },
    "payment_action_required": {"payment_pending", "payment_failed", "provider_paid_observed", "void"},
    "payment_failed": {"payment_pending", "payment_action_required", "provider_paid_observed", "void"},
    "provider_paid_observed": {"refund_observed", "dispute_observed"},
    "refund_observed": {"dispute_observed"},
    "dispute_observed": {"refund_observed"},
    "void": set(),
}

PLAN_CHANGE_READY_INVOICE_STATUSES = {"provider_paid_observed"}
PLAN_CHANGE_BLOCKING_INVOICE_STATUSES = {"payment_failed", "payment_action_required", "refund_observed", "dispute_observed", "void"}


@dataclass(frozen=True)
class ProviderPaymentEvent:
    provider_event_ref_hash: str
    invoice_ref_hash: str
    status: str
    amount_minor: int = 0
    currency: str = "CNY"
    reason_codes: tuple[str, ...] = ()
    plan_change_ref_hash: str | None = None

    def to_safe_record(self) -> dict[str, Any]:
        return _safe_record(asdict(self))


@dataclass(frozen=True)
class InvoiceState:
    invoice_ref_hash: str
    status: str
    amount_minor: int = 0
    currency: str = "CNY"
    reason_codes: tuple[str, ...] = ()
    provider_event_ref_hash: str | None = None
    plan_change_ref_hash: str | None = None

    def to_safe_record(self) -> dict[str, Any]:
        return _safe_record(asdict(self))


@dataclass(frozen=True)
class PlanChangeState:
    plan_change_ref_hash: str
    status: str
    reason_codes: tuple[str, ...] = ()
    invoice_ref_hash: str | None = None
    provider_event_ref_hash: str | None = None
    amount_minor: int = 0
    currency: str = "CNY"

    def to_safe_record(self) -> dict[str, Any]:
        return _safe_record(asdict(self))


class BillingPaymentReconciliationService:
    """Local-only invoice and plan-change state policy for provider events."""

    def reconcile_provider_event(
        self,
        provider_event: ProviderPaymentEvent | Mapping[str, Any],
        invoice: InvoiceState | Mapping[str, Any],
        *,
        seen_provider_event_ref_hashes: Iterable[str] = (),
    ) -> dict[str, Any]:
        event = _provider_event(provider_event)
        current_invoice = _invoice_state(invoice)
        event_status = _provider_status(event.status)
        invoice_status = _invoice_status(current_invoice.status)
        observed_reason_codes = list(_merge_reason_codes(event.reason_codes, current_invoice.reason_codes))
        blocking_reason_codes: list[str] = []
        seen_event_hashes = set(seen_provider_event_ref_hashes)

        next_invoice_status = invoice_status
        decision_status = "ready"
        recommended_actions: list[str] = []

        if event.provider_event_ref_hash in seen_event_hashes:
            return self._reconciliation_payload(
                status="ignored",
                provider_event=event,
                invoice=current_invoice,
                provider_event_status=event_status,
                current_invoice_status=invoice_status,
                next_invoice_status=invoice_status,
                reason_codes=_append_reason(observed_reason_codes, "duplicate_provider_event"),
                recommended_actions=[
                    "Ignore duplicate provider event hash and keep the existing local invoice state."
                ],
            )

        blocking_reason_codes.extend(self._reference_reasons(event, current_invoice))
        blocking_reason_codes.extend(self._amount_reasons(event, current_invoice))

        if event_status == "unknown":
            blocking_reason_codes.append("unknown_provider_status")
        elif invoice_status == "unknown":
            blocking_reason_codes.append("unknown_invoice_status")
        elif not blocking_reason_codes:
            next_invoice_status = event_status
            if next_invoice_status not in INVOICE_TRANSITIONS.get(invoice_status, set()) and next_invoice_status != invoice_status:
                blocking_reason_codes.append("invalid_invoice_transition")

        if blocking_reason_codes:
            decision_status = "needs_review"
            next_invoice_status = invoice_status
            recommended_actions = self._review_actions(blocking_reason_codes)
        else:
            recommended_actions = self._ready_actions(next_invoice_status)

        return self._reconciliation_payload(
            status=decision_status,
            provider_event=event,
            invoice=current_invoice,
            provider_event_status=event_status,
            current_invoice_status=invoice_status,
            next_invoice_status=next_invoice_status,
            reason_codes=tuple([*observed_reason_codes, *blocking_reason_codes]),
            recommended_actions=recommended_actions,
        )

    def evaluate_plan_change(
        self,
        plan_change: PlanChangeState | Mapping[str, Any],
        invoice: InvoiceState | Mapping[str, Any],
    ) -> dict[str, Any]:
        change = _plan_change_state(plan_change)
        current_invoice = _invoice_state(invoice)
        plan_status = _normalize_status(change.status)
        invoice_status = _invoice_status(current_invoice.status)
        observed_reason_codes = list(_merge_reason_codes(change.reason_codes, current_invoice.reason_codes))
        blocking_reason_codes: list[str] = []

        if change.invoice_ref_hash and current_invoice.invoice_ref_hash != change.invoice_ref_hash:
            blocking_reason_codes.append("invoice_ref_hash_mismatch")
        if not change.plan_change_ref_hash:
            blocking_reason_codes.append("missing_plan_change_ref_hash")

        if invoice_status in PLAN_CHANGE_READY_INVOICE_STATUSES and not blocking_reason_codes:
            status = "ready"
            next_plan_change_status = "ready_for_entitlement_review"
            recommended_actions = [
                "Queue the plan change for entitlement review from local provider-paid observation evidence."
            ]
        elif invoice_status in PLAN_CHANGE_BLOCKING_INVOICE_STATUSES:
            status = "blocked"
            next_plan_change_status = plan_status
            blocking_reason_codes.append(f"invoice_{invoice_status}")
            recommended_actions = [
                "Do not apply the plan change while the invoice is failed, disputed, refunded, action-required, or void."
            ]
        else:
            status = "blocked"
            next_plan_change_status = plan_status
            blocking_reason_codes.append("invoice_not_provider_paid_observed")
            recommended_actions = [
                "Wait for local reconciliation to reach provider_paid_observed before applying plan changes."
            ]

        return {
            "status": status,
            "scope": "billing-plan-change-gate",
            "plan_change_ref_hash": change.plan_change_ref_hash,
            "invoice_ref_hash": current_invoice.invoice_ref_hash,
            "current_plan_change_status": plan_status,
            "next_plan_change_status": next_plan_change_status,
            "invoice_status": invoice_status,
            "reason_codes": _dedupe([*observed_reason_codes, *blocking_reason_codes]),
            "recommended_actions": recommended_actions,
            "evidence_mode": "local_policy_only",
            "real_payment_verified": False,
            "requires_network": False,
        }

    def summarize_invoice_states(
        self,
        invoices: Iterable[InvoiceState | Mapping[str, Any]],
    ) -> dict[str, Any]:
        totals = {
            "invoices": 0,
            "amount_minor": 0,
            "local_provider_paid_observed": 0,
            "needs_attention": 0,
        }
        by_status: dict[str, dict[str, int]] = {}
        by_currency: dict[str, dict[str, int]] = {}
        reason_counts: dict[str, int] = {}

        for raw_invoice in invoices:
            invoice = _invoice_state(raw_invoice)
            status = _invoice_status(invoice.status)
            currency = _currency(invoice.currency)
            amount = max(0, _safe_int(invoice.amount_minor))

            totals["invoices"] += 1
            totals["amount_minor"] += amount
            if status == "provider_paid_observed":
                totals["local_provider_paid_observed"] += 1
            if status in {"payment_failed", "payment_action_required", "refund_observed", "dispute_observed"}:
                totals["needs_attention"] += 1

            _increment(by_status, status, "invoices", 1)
            _increment(by_status, status, "amount_minor", amount)
            _increment(by_currency, currency, "invoices", 1)
            _increment(by_currency, currency, "amount_minor", amount)

            for code in _safe_reason_codes(invoice.reason_codes):
                reason_counts[code] = reason_counts.get(code, 0) + 1

        return {
            "status": "ready",
            "scope": "billing-invoice-state-summary",
            "privacy_mode": "aggregate-only",
            "totals": totals,
            "by_status": dict(sorted(by_status.items())),
            "by_currency": dict(sorted(by_currency.items())),
            "reason_counts": dict(sorted(reason_counts.items())),
            "included_fields": sorted(SAFE_MODEL_FIELDS),
            "excluded_sensitive_field_fragments": list(SENSITIVE_FIELD_FRAGMENTS),
            "invoice_refs_included": False,
            "provider_event_refs_included": False,
            "evidence_mode": "local_policy_only",
            "real_payment_verified": False,
            "requires_network": False,
        }

    def build_policy_evidence(self) -> dict[str, Any]:
        return {
            "status": "backend_evidence_ready",
            "scope": "billing-payment-reconciliation",
            "implemented_controls": [
                "hashed-provider-event-reference-only",
                "hashed-invoice-reference-only",
                "invoice-state-transition-policy",
                "amount-and-currency-match-guard",
                "duplicate-provider-event-idempotency-guard",
                "plan-change-gated-by-invoice-state",
                "privacy-safe-invoice-state-summary",
            ],
            "invoice_statuses": sorted(KNOWN_INVOICE_STATUSES),
            "non_goals": [
                "real-payment-processing",
                "provider-webhook-signature-verification",
                "settlement-confirmation",
                "card-account-email-or-password-storage",
                "router-integration",
                "release-or-ledger-changes",
            ],
            "validation_commands": [
                "python -m pytest tests/test_billing_payment_reconciliation.py -q",
                "python -m compileall services/billing_payment_reconciliation.py tests/test_billing_payment_reconciliation.py",
            ],
            "privacy_note": (
                "Inputs and outputs use hashed provider/invoice/plan-change references, statuses, "
                "reason codes, amount_minor, and currency only; raw payment identifiers and user "
                "contact fields are intentionally excluded."
            ),
            "evidence_mode": "local_policy_only",
            "real_payment_verified": False,
            "requires_network": False,
        }

    @staticmethod
    def _reference_reasons(event: ProviderPaymentEvent, invoice: InvoiceState) -> list[str]:
        reasons: list[str] = []
        if not event.provider_event_ref_hash:
            reasons.append("missing_provider_event_ref_hash")
        if not event.invoice_ref_hash or not invoice.invoice_ref_hash:
            reasons.append("missing_invoice_ref_hash")
        elif event.invoice_ref_hash != invoice.invoice_ref_hash:
            reasons.append("invoice_ref_hash_mismatch")
        if event.plan_change_ref_hash and invoice.plan_change_ref_hash:
            if event.plan_change_ref_hash != invoice.plan_change_ref_hash:
                reasons.append("plan_change_ref_hash_mismatch")
        return reasons

    @staticmethod
    def _amount_reasons(event: ProviderPaymentEvent, invoice: InvoiceState) -> list[str]:
        reasons: list[str] = []
        if max(0, _safe_int(event.amount_minor)) != max(0, _safe_int(invoice.amount_minor)):
            reasons.append("amount_mismatch")
        if _currency(event.currency) != _currency(invoice.currency):
            reasons.append("currency_mismatch")
        return reasons

    @staticmethod
    def _review_actions(reason_codes: Iterable[str]) -> list[str]:
        reasons = set(reason_codes)
        actions: list[str] = []
        if "duplicate_provider_event" in reasons:
            actions.append("Ignore duplicate provider event hash and keep the existing local invoice state.")
        if {"amount_mismatch", "currency_mismatch"} & reasons:
            actions.append("Hold invoice state change until amount_minor and currency match local invoice expectations.")
        if "invoice_ref_hash_mismatch" in reasons or "plan_change_ref_hash_mismatch" in reasons:
            actions.append("Route the event to manual reconciliation because hashed references do not match.")
        if "invalid_invoice_transition" in reasons:
            actions.append("Reject invoice state transition that is not allowed by the local state machine.")
        if "unknown_provider_status" in reasons or "unknown_invoice_status" in reasons:
            actions.append("Map the provider and invoice statuses before updating local billing state.")
        if not actions:
            actions.append("Review reconciliation reasons before changing invoice or plan-change state.")
        return actions

    @staticmethod
    def _ready_actions(next_invoice_status: str) -> list[str]:
        if next_invoice_status == "provider_paid_observed":
            return [
                "Record provider_paid_observed locally and keep settlement verification out of this policy slice."
            ]
        if next_invoice_status == "payment_failed":
            return ["Record payment_failed locally and keep the plan change blocked."]
        if next_invoice_status == "payment_action_required":
            return ["Record payment_action_required locally and keep the invoice open for user action."]
        if next_invoice_status == "void":
            return ["Record void locally and prevent entitlement or plan-change activation."]
        if next_invoice_status in {"refund_observed", "dispute_observed"}:
            return ["Record the post-payment provider state locally and route entitlement review separately."]
        return ["Record the local invoice state transition."]

    @staticmethod
    def _reconciliation_payload(
        *,
        status: str,
        provider_event: ProviderPaymentEvent,
        invoice: InvoiceState,
        provider_event_status: str,
        current_invoice_status: str,
        next_invoice_status: str,
        reason_codes: Iterable[str],
        recommended_actions: list[str],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "scope": "billing-provider-reconciliation",
            "provider_event_ref_hash": provider_event.provider_event_ref_hash,
            "invoice_ref_hash": invoice.invoice_ref_hash,
            "plan_change_ref_hash": provider_event.plan_change_ref_hash or invoice.plan_change_ref_hash,
            "provider_event_status": provider_event_status,
            "current_invoice_status": current_invoice_status,
            "next_invoice_status": next_invoice_status,
            "amount_minor": max(0, _safe_int(invoice.amount_minor)),
            "currency": _currency(invoice.currency),
            "reason_codes": _dedupe(reason_codes),
            "recommended_actions": recommended_actions,
            "evidence_mode": "local_policy_only",
            "real_payment_verified": False,
            "requires_network": False,
        }


def _provider_event(value: ProviderPaymentEvent | Mapping[str, Any]) -> ProviderPaymentEvent:
    if isinstance(value, ProviderPaymentEvent):
        return value
    return ProviderPaymentEvent(
        provider_event_ref_hash=str(value.get("provider_event_ref_hash") or ""),
        invoice_ref_hash=str(value.get("invoice_ref_hash") or ""),
        plan_change_ref_hash=_optional_str(value.get("plan_change_ref_hash")),
        status=str(value.get("status") or "unknown"),
        amount_minor=max(0, _safe_int(value.get("amount_minor"))),
        currency=_currency(value.get("currency")),
        reason_codes=_safe_reason_codes(value.get("reason_codes")),
    )


def _invoice_state(value: InvoiceState | Mapping[str, Any]) -> InvoiceState:
    if isinstance(value, InvoiceState):
        return value
    return InvoiceState(
        invoice_ref_hash=str(value.get("invoice_ref_hash") or ""),
        provider_event_ref_hash=_optional_str(value.get("provider_event_ref_hash")),
        plan_change_ref_hash=_optional_str(value.get("plan_change_ref_hash")),
        status=str(value.get("status") or "unknown"),
        amount_minor=max(0, _safe_int(value.get("amount_minor"))),
        currency=_currency(value.get("currency")),
        reason_codes=_safe_reason_codes(value.get("reason_codes")),
    )


def _plan_change_state(value: PlanChangeState | Mapping[str, Any]) -> PlanChangeState:
    if isinstance(value, PlanChangeState):
        return value
    return PlanChangeState(
        plan_change_ref_hash=str(value.get("plan_change_ref_hash") or ""),
        invoice_ref_hash=_optional_str(value.get("invoice_ref_hash")),
        provider_event_ref_hash=_optional_str(value.get("provider_event_ref_hash")),
        status=str(value.get("status") or "unknown"),
        amount_minor=max(0, _safe_int(value.get("amount_minor"))),
        currency=_currency(value.get("currency")),
        reason_codes=_safe_reason_codes(value.get("reason_codes")),
    )


def _safe_record(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: values[key] for key in SAFE_MODEL_FIELDS if key in values}


def _provider_status(status: str) -> str:
    return PROVIDER_STATUS_ALIASES.get(_normalize_status(status), "unknown")


def _invoice_status(status: str) -> str:
    normalized = _normalize_status(status)
    if normalized == "paid":
        return "provider_paid_observed"
    return normalized if normalized in KNOWN_INVOICE_STATUSES else "unknown"


def _normalize_status(status: str) -> str:
    return str(status or "unknown").strip().lower().replace("-", "_")


def _currency(currency: Any) -> str:
    value = str(currency or "CNY").strip().upper()
    return value if value else "CNY"


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value)
    return result or None


def _safe_reason_codes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        candidates = [value]
    else:
        try:
            candidates = list(value)
        except TypeError:
            candidates = [value]
    return tuple(_dedupe(_normalize_status(str(item)) for item in candidates if str(item or "").strip()))


def _merge_reason_codes(*groups: Iterable[str]) -> tuple[str, ...]:
    merged: list[str] = []
    for group in groups:
        merged.extend(_safe_reason_codes(group))
    return tuple(_dedupe(merged))


def _append_reason(reason_codes: Iterable[str], reason_code: str) -> tuple[str, ...]:
    return tuple(_dedupe([*reason_codes, reason_code]))


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw_value in values:
        value = _normalize_status(str(raw_value))
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _increment(bucket: dict[str, dict[str, int]], key: str, metric: str, amount: int) -> None:
    bucket.setdefault(key, {})
    bucket[key][metric] = bucket[key].get(metric, 0) + amount


def privacy_safe_model_field_names() -> dict[str, list[str]]:
    return {
        "ProviderPaymentEvent": [field.name for field in fields(ProviderPaymentEvent)],
        "InvoiceState": [field.name for field in fields(InvoiceState)],
        "PlanChangeState": [field.name for field in fields(PlanChangeState)],
    }
