import re

from services.billing_entitlement_gap import (
    ActivationAuditInput,
    BillingEntitlementGapService,
    UsageGuardInput,
)


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_paid_subscription_activation_is_ready_without_gateway_call():
    result = BillingEntitlementGapService().audit_payment_activation(
        ActivationAuditInput(
            sku="personal_plan",
            order_status="paid",
            payment_status="paid",
            stripe_session_id="demo_user_123456",
            requested_plan_type="personal",
        )
    )

    assert result["status"] == "ready"
    assert result["activation_type"] == "subscription"
    assert result["plan_type"] == "personal"
    assert result["grants_entitlement"] is True
    assert result["requires_real_gateway"] is False
    assert result["audit_events"] == [
        {
            "type": "payment-session-observed",
            "gateway_mode": "demo",
            "redacted_session_id": "demo...3456",
        }
    ]
    assert all(item["passed"] for item in result["guard_results"])
    assert not SECRET_PATTERN.search(str(result))


def test_report_unlock_requires_related_review_target():
    result = BillingEntitlementGapService().audit_payment_activation(
        ActivationAuditInput(
            sku="report_unlock",
            order_status="paid",
            payment_status="paid",
            stripe_session_id="cs_test_1234567890",
        )
    )

    failed = {item["id"] for item in result["guard_results"] if not item["passed"]}
    assert result["status"] == "blocked"
    assert result["activation_type"] == "report_unlock"
    assert result["grants_entitlement"] is False
    assert failed == {"report-unlock-target"}
    assert "Require related_review_id" in result["recommended_actions"][0]


def test_subscription_activation_blocks_mismatched_plan():
    result = BillingEntitlementGapService().audit_payment_activation(
        ActivationAuditInput(
            sku="lawyer_plan",
            order_status="paid",
            payment_status="paid",
            requested_plan_type="personal",
        )
    )

    failed = {item["id"] for item in result["guard_results"] if not item["passed"]}
    assert result["status"] == "blocked"
    assert result["plan_type"] == "lawyer"
    assert failed == {"sku-plan-match"}
    assert result["audit_events"][0]["type"] == "payment-session-missing"


def test_usage_guard_blocks_exhausted_free_plan():
    result = BillingEntitlementGapService().evaluate_usage_guard(
        UsageGuardInput(plan_type="free", subscription_status="active", reports_used_month=2)
    )

    failed = {item["id"] for item in result["guard_results"] if not item["passed"]}
    assert result["status"] == "blocked"
    assert result["report_quota_monthly"] == 2
    assert result["reports_remaining"] == 0
    assert result["can_create_report"] is False
    assert failed == {"quota-available"}


def test_usage_guard_allows_admin_role_unlimited_capacity():
    result = BillingEntitlementGapService().evaluate_usage_guard(
        UsageGuardInput(
            plan_type="free",
            subscription_status="active",
            reports_used_month=5000,
            user_role="admin",
        )
    )

    assert result["status"] == "ready"
    assert result["effective_plan_type"] == "admin"
    assert result["reports_remaining"] == 999999
    assert result["can_create_report"] is True


def test_gap_evidence_lists_billing_entitlement_next_steps():
    result = BillingEntitlementGapService().build_gap_evidence()

    assert result["status"] == "backend_evidence_ready"
    assert result["scope"] == "billing-entitlements"
    assert "payment-activation-audit" in result["implemented_controls"]
    assert "monthly-usage-plan-guard" in result["implemented_controls"]
    assert "stripe-webhook-signature-verification" in result["remaining_product_gaps"]
    assert result["validation_commands"] == [
        "python -m pytest tests/test_billing_entitlement_gap.py -q",
        "python -m py_compile services/billing_entitlement_gap.py",
    ]
    assert not SECRET_PATTERN.search(str(result))


def test_billing_entitlement_gap_route_returns_evidence():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/billing-entitlement-gap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["scope"] == "billing-entitlements"
