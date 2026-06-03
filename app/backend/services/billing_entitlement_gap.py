from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from services.product_catalog import PLAN_LIMITS, get_sku, plan_from_sku


PAID_ORDER_STATUSES = {"paid"}
ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
UNLIMITED_QUOTA_THRESHOLD = 999999


@dataclass(frozen=True)
class ActivationAuditInput:
    sku: str
    order_status: str
    payment_status: Optional[str] = None
    stripe_session_id: Optional[str] = None
    related_review_id: Optional[int] = None
    requested_plan_type: Optional[str] = None


@dataclass(frozen=True)
class UsageGuardInput:
    plan_type: str
    subscription_status: str = "active"
    reports_used_month: int = 0
    user_role: str = "user"


class BillingEntitlementGapService:
    """Deterministic billing evidence without calling a real payment gateway."""

    def audit_payment_activation(self, audit_input: ActivationAuditInput) -> dict[str, Any]:
        sku_info = get_sku(audit_input.sku)
        guard_results: list[dict[str, Any]] = []
        audit_events: list[dict[str, Any]] = []

        if not sku_info:
            return self._activation_payload(
                audit_input=audit_input,
                status="blocked",
                activation_type="unknown",
                plan_type=None,
                grants_entitlement=False,
                guard_results=[
                    {
                        "id": "known-sku",
                        "passed": False,
                        "message": "SKU is not in the public product catalog.",
                    }
                ],
                audit_events=[],
                recommended_actions=["Map the SKU before creating orders or entitlement grants."],
            )

        plan_type = plan_from_sku(audit_input.sku)
        activation_type = "subscription" if plan_type else "report_unlock"
        is_paid = audit_input.order_status in PAID_ORDER_STATUSES

        guard_results.append(
            {
                "id": "known-sku",
                "passed": True,
                "message": "SKU is in the public product catalog.",
            }
        )
        guard_results.append(
            {
                "id": "paid-order-required",
                "passed": is_paid,
                "message": "Entitlements are granted only after the order is paid.",
            }
        )

        if plan_type:
            requested_matches = audit_input.requested_plan_type in {None, plan_type}
            guard_results.append(
                {
                    "id": "sku-plan-match",
                    "passed": requested_matches,
                    "message": "The requested plan must match the SKU plan mapping.",
                }
            )
        else:
            has_review_target = bool(audit_input.related_review_id)
            guard_results.append(
                {
                    "id": "report-unlock-target",
                    "passed": has_review_target,
                    "message": "Report unlock orders must identify the review report to unlock.",
                }
            )

        if audit_input.stripe_session_id:
            gateway_mode = "demo" if audit_input.stripe_session_id.startswith("demo_") else "stripe"
            audit_events.append(
                {
                    "type": "payment-session-observed",
                    "gateway_mode": gateway_mode,
                    "redacted_session_id": self._redact_session_id(audit_input.stripe_session_id),
                }
            )
        else:
            audit_events.append(
                {
                    "type": "payment-session-missing",
                    "gateway_mode": "local_audit",
                    "redacted_session_id": None,
                }
            )

        grants_entitlement = all(item["passed"] for item in guard_results)
        status = "ready" if grants_entitlement else "blocked"
        recommended_actions = self._activation_actions(
            guard_results=guard_results,
            activation_type=activation_type,
        )

        return self._activation_payload(
            audit_input=audit_input,
            status=status,
            activation_type=activation_type,
            plan_type=plan_type,
            grants_entitlement=grants_entitlement,
            guard_results=guard_results,
            audit_events=audit_events,
            recommended_actions=recommended_actions,
        )

    def evaluate_usage_guard(self, usage_input: UsageGuardInput) -> dict[str, Any]:
        effective_plan = "admin" if usage_input.user_role == "admin" else usage_input.plan_type
        limits = PLAN_LIMITS.get(effective_plan)
        guard_results: list[dict[str, Any]] = []

        if not limits:
            return {
                "status": "blocked",
                "plan_type": usage_input.plan_type,
                "effective_plan_type": effective_plan,
                "subscription_status": usage_input.subscription_status,
                "report_quota_monthly": 0,
                "reports_used_month": max(0, usage_input.reports_used_month),
                "reports_remaining": 0,
                "can_create_report": False,
                "guard_results": [
                    {
                        "id": "known-plan",
                        "passed": False,
                        "message": "Plan type is not configured in PLAN_LIMITS.",
                    }
                ],
                "recommended_actions": ["Add the plan to PLAN_LIMITS before granting usage."],
            }

        quota = int(limits["report_quota_monthly"])
        used = max(0, int(usage_input.reports_used_month))
        unlimited = quota >= UNLIMITED_QUOTA_THRESHOLD
        remaining = UNLIMITED_QUOTA_THRESHOLD if unlimited else max(0, quota - used)
        active = usage_input.subscription_status in ACTIVE_SUBSCRIPTION_STATUSES

        guard_results.append(
            {
                "id": "known-plan",
                "passed": True,
                "message": "Plan type is configured in PLAN_LIMITS.",
            }
        )
        guard_results.append(
            {
                "id": "active-subscription",
                "passed": active,
                "message": "Subscription must be active or trialing to create reports.",
            }
        )
        guard_results.append(
            {
                "id": "quota-available",
                "passed": unlimited or remaining > 0,
                "message": "Monthly report quota must have remaining capacity.",
            }
        )

        can_create_report = all(item["passed"] for item in guard_results)
        return {
            "status": "ready" if can_create_report else "blocked",
            "plan_type": usage_input.plan_type,
            "effective_plan_type": effective_plan,
            "subscription_status": usage_input.subscription_status,
            "report_quota_monthly": quota,
            "reports_used_month": used,
            "reports_remaining": remaining,
            "can_create_report": can_create_report,
            "guard_results": guard_results,
            "recommended_actions": self._usage_actions(guard_results),
        }

    def build_gap_evidence(self) -> dict[str, Any]:
        return {
            "status": "backend_evidence_ready",
            "scope": "billing-entitlements",
            "implemented_controls": [
                "payment-activation-audit",
                "sku-plan-match-guard",
                "report-unlock-target-guard",
                "monthly-usage-plan-guard",
            ],
            "remaining_product_gaps": [
                "stripe-webhook-signature-verification",
                "refund-and-chargeback-state-machine",
                "subscription-renewal-period-rollover-audit",
                "frontend-entitlement-state-messaging",
            ],
            "validation_commands": [
                "python -m pytest tests/test_billing_entitlement_gap.py -q",
                "python -m py_compile services/billing_entitlement_gap.py",
            ],
            "privacy_note": "Audit payloads redact payment session identifiers and do not include secrets or raw card data.",
        }

    @staticmethod
    def _redact_session_id(session_id: str) -> str:
        if len(session_id) <= 8:
            return "***"
        return f"{session_id[:4]}...{session_id[-4:]}"

    @staticmethod
    def _activation_payload(
        *,
        audit_input: ActivationAuditInput,
        status: str,
        activation_type: str,
        plan_type: Optional[str],
        grants_entitlement: bool,
        guard_results: list[dict[str, Any]],
        audit_events: list[dict[str, Any]],
        recommended_actions: list[str],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "sku": audit_input.sku,
            "activation_type": activation_type,
            "plan_type": plan_type,
            "order_status": audit_input.order_status,
            "payment_status": audit_input.payment_status,
            "grants_entitlement": grants_entitlement,
            "guard_results": guard_results,
            "audit_events": audit_events,
            "recommended_actions": recommended_actions,
            "requires_real_gateway": False,
        }

    @staticmethod
    def _activation_actions(*, guard_results: list[dict[str, Any]], activation_type: str) -> list[str]:
        failed = {item["id"] for item in guard_results if not item["passed"]}
        actions: list[str] = []
        if "paid-order-required" in failed:
            actions.append("Wait for a paid order before granting entitlements.")
        if "sku-plan-match" in failed:
            actions.append("Reject mismatched SKU and plan activation requests.")
        if "report-unlock-target" in failed:
            actions.append("Require related_review_id before unlocking a single report.")
        if not actions:
            actions.append(f"Record a {activation_type} entitlement activation audit event.")
        return actions

    @staticmethod
    def _usage_actions(guard_results: list[dict[str, Any]]) -> list[str]:
        failed = {item["id"] for item in guard_results if not item["passed"]}
        actions: list[str] = []
        if "known-plan" in failed:
            actions.append("Add the plan to PLAN_LIMITS before granting usage.")
        if "active-subscription" in failed:
            actions.append("Block report creation until the subscription is active.")
        if "quota-available" in failed:
            actions.append("Prompt the user to upgrade or wait for the next billing period.")
        if not actions:
            actions.append("Allow report creation and consume one report after successful generation.")
        return actions
