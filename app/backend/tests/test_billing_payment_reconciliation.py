import re

from services.billing_payment_reconciliation import (
    BillingPaymentReconciliationService,
    InvoiceState,
    PlanChangeState,
    ProviderPaymentEvent,
    privacy_safe_model_field_names,
)


SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|cs_(test|live)_[A-Za-z0-9]+|"
    r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b|"
    r"\b(?:\d[ -]*?){13,19}\b)"
)
SENSITIVE_FIELD_FRAGMENTS = {"card", "account", "email", "password", "secret", "token", "session"}


def reason_codes(payload):
    return set(payload["reason_codes"])


def assert_privacy_safe(payload):
    rendered = str(payload)
    assert not SECRET_PATTERN.search(rendered)
    assert "customer@example.com" not in rendered
    assert "4111111111111111" not in rendered
    assert "acct_raw_123" not in rendered
    assert "cs_test_raw_session" not in rendered


def test_provider_paid_event_records_observation_without_claiming_settlement():
    result = BillingPaymentReconciliationService().reconcile_provider_event(
        ProviderPaymentEvent(
            provider_event_ref_hash="evt_hash_paid_001",
            invoice_ref_hash="inv_hash_001",
            plan_change_ref_hash="plan_hash_001",
            status="invoice.paid",
            amount_minor=9900,
            currency="cny",
        ),
        InvoiceState(
            invoice_ref_hash="inv_hash_001",
            plan_change_ref_hash="plan_hash_001",
            status="open",
            amount_minor=9900,
            currency="CNY",
        ),
    )

    assert result["status"] == "ready"
    assert result["provider_event_status"] == "provider_paid_observed"
    assert result["current_invoice_status"] == "open"
    assert result["next_invoice_status"] == "provider_paid_observed"
    assert result["reason_codes"] == []
    assert result["evidence_mode"] == "local_policy_only"
    assert result["real_payment_verified"] is False
    assert result["requires_network"] is False
    assert "settlement verification out of this policy slice" in result["recommended_actions"][0]
    assert result["next_invoice_status"] not in {"paid", "settled", "payment_completed"}
    assert_privacy_safe(result)


def test_amount_and_currency_mismatch_needs_review_without_state_change():
    result = BillingPaymentReconciliationService().reconcile_provider_event(
        {
            "provider_event_ref_hash": "evt_hash_mismatch_001",
            "invoice_ref_hash": "inv_hash_002",
            "status": "payment_succeeded",
            "amount_minor": 8800,
            "currency": "USD",
            "email": "customer@example.com",
            "card_number": "4111111111111111",
            "account_id": "acct_raw_123",
            "payment_session_id": "cs_test_raw_session",
        },
        {
            "invoice_ref_hash": "inv_hash_002",
            "status": "payment_pending",
            "amount_minor": 9900,
            "currency": "CNY",
            "user_email": "customer@example.com",
        },
    )

    assert result["status"] == "needs_review"
    assert result["next_invoice_status"] == "payment_pending"
    assert reason_codes(result) == {"amount_mismatch", "currency_mismatch"}
    assert "amount_minor and currency match" in result["recommended_actions"][0]
    assert_privacy_safe(result)


def test_duplicate_provider_event_is_idempotently_ignored():
    result = BillingPaymentReconciliationService().reconcile_provider_event(
        ProviderPaymentEvent(
            provider_event_ref_hash="evt_hash_seen_001",
            invoice_ref_hash="inv_hash_003",
            status="invoice.payment_failed",
            amount_minor=1200,
            currency="CNY",
        ),
        InvoiceState(
            invoice_ref_hash="inv_hash_003",
            status="open",
            amount_minor=1200,
            currency="CNY",
        ),
        seen_provider_event_ref_hashes={"evt_hash_seen_001"},
    )

    assert result["status"] == "ignored"
    assert result["next_invoice_status"] == "open"
    assert reason_codes(result) == {"duplicate_provider_event"}
    assert result["real_payment_verified"] is False
    assert_privacy_safe(result)


def test_provider_failure_void_refund_and_dispute_statuses_follow_local_state_machine():
    service = BillingPaymentReconciliationService()

    failed = service.reconcile_provider_event(
        ProviderPaymentEvent(
            provider_event_ref_hash="evt_hash_failed_001",
            invoice_ref_hash="inv_hash_004",
            status="invoice.payment_failed",
            amount_minor=2000,
            currency="CNY",
            reason_codes=("insufficient_funds",),
        ),
        InvoiceState(invoice_ref_hash="inv_hash_004", status="open", amount_minor=2000, currency="CNY"),
    )
    voided = service.reconcile_provider_event(
        ProviderPaymentEvent(
            provider_event_ref_hash="evt_hash_void_001",
            invoice_ref_hash="inv_hash_005",
            status="invoice.voided",
            amount_minor=2000,
            currency="CNY",
        ),
        InvoiceState(invoice_ref_hash="inv_hash_005", status="payment_failed", amount_minor=2000, currency="CNY"),
    )
    refunded = service.reconcile_provider_event(
        ProviderPaymentEvent(
            provider_event_ref_hash="evt_hash_refund_001",
            invoice_ref_hash="inv_hash_006",
            status="charge.refunded",
            amount_minor=2000,
            currency="CNY",
        ),
        InvoiceState(
            invoice_ref_hash="inv_hash_006",
            status="provider_paid_observed",
            amount_minor=2000,
            currency="CNY",
        ),
    )
    disputed = service.reconcile_provider_event(
        ProviderPaymentEvent(
            provider_event_ref_hash="evt_hash_dispute_001",
            invoice_ref_hash="inv_hash_007",
            status="charge.dispute.created",
            amount_minor=2000,
            currency="CNY",
        ),
        InvoiceState(
            invoice_ref_hash="inv_hash_007",
            status="provider_paid_observed",
            amount_minor=2000,
            currency="CNY",
        ),
    )

    assert failed["status"] == "ready"
    assert failed["next_invoice_status"] == "payment_failed"
    assert reason_codes(failed) == {"insufficient_funds"}
    assert voided["status"] == "ready"
    assert voided["next_invoice_status"] == "void"
    assert refunded["status"] == "ready"
    assert refunded["next_invoice_status"] == "refund_observed"
    assert disputed["status"] == "ready"
    assert disputed["next_invoice_status"] == "dispute_observed"
    assert_privacy_safe([failed, voided, refunded, disputed])


def test_invalid_invoice_transition_is_held_for_review():
    result = BillingPaymentReconciliationService().reconcile_provider_event(
        ProviderPaymentEvent(
            provider_event_ref_hash="evt_hash_late_paid_001",
            invoice_ref_hash="inv_hash_void_001",
            status="invoice.paid",
            amount_minor=5000,
            currency="CNY",
        ),
        InvoiceState(
            invoice_ref_hash="inv_hash_void_001",
            status="void",
            amount_minor=5000,
            currency="CNY",
        ),
    )

    assert result["status"] == "needs_review"
    assert result["next_invoice_status"] == "void"
    assert reason_codes(result) == {"invalid_invoice_transition"}


def test_plan_change_waits_for_provider_paid_observation_only():
    service = BillingPaymentReconciliationService()
    plan_change = PlanChangeState(
        plan_change_ref_hash="plan_hash_002",
        invoice_ref_hash="inv_hash_008",
        status="requested",
    )

    blocked = service.evaluate_plan_change(
        plan_change,
        InvoiceState(invoice_ref_hash="inv_hash_008", status="open", amount_minor=9900, currency="CNY"),
    )
    ready = service.evaluate_plan_change(
        plan_change,
        InvoiceState(
            invoice_ref_hash="inv_hash_008",
            status="provider_paid_observed",
            amount_minor=9900,
            currency="CNY",
            reason_codes=("provider_event_matched",),
        ),
    )

    assert blocked["status"] == "blocked"
    assert blocked["next_plan_change_status"] == "requested"
    assert reason_codes(blocked) == {"invoice_not_provider_paid_observed"}
    assert ready["status"] == "ready"
    assert ready["next_plan_change_status"] == "ready_for_entitlement_review"
    assert reason_codes(ready) == {"provider_event_matched"}
    assert ready["real_payment_verified"] is False
    assert_privacy_safe([blocked, ready])


def test_invoice_state_summary_is_aggregate_only_and_drops_sensitive_mapping_fields():
    result = BillingPaymentReconciliationService().summarize_invoice_states(
        [
            {
                "invoice_ref_hash": "inv_hash_009",
                "status": "provider_paid_observed",
                "amount_minor": 9900,
                "currency": "CNY",
                "reason_codes": ["provider_event_matched"],
                "email": "customer@example.com",
                "card_number": "4111111111111111",
            },
            {
                "invoice_ref_hash": "inv_hash_010",
                "status": "payment_failed",
                "amount_minor": 6600,
                "currency": "CNY",
                "reason_codes": ["insufficient_funds"],
                "account_id": "acct_raw_123",
                "payment_session_id": "cs_test_raw_session",
            },
        ]
    )

    assert result["status"] == "ready"
    assert result["privacy_mode"] == "aggregate-only"
    assert result["totals"]["invoices"] == 2
    assert result["totals"]["amount_minor"] == 16500
    assert result["totals"]["local_provider_paid_observed"] == 1
    assert result["totals"]["needs_attention"] == 1
    assert result["by_status"]["provider_paid_observed"]["amount_minor"] == 9900
    assert result["by_currency"]["CNY"]["invoices"] == 2
    assert result["reason_counts"] == {
        "insufficient_funds": 1,
        "provider_event_matched": 1,
    }
    assert result["invoice_refs_included"] is False
    assert result["provider_event_refs_included"] is False
    assert_privacy_safe(result)


def test_policy_evidence_documents_non_goals_and_validation_commands():
    result = BillingPaymentReconciliationService().build_policy_evidence()

    assert result["status"] == "backend_evidence_ready"
    assert result["scope"] == "billing-payment-reconciliation"
    assert "invoice-state-transition-policy" in result["implemented_controls"]
    assert "plan-change-gated-by-invoice-state" in result["implemented_controls"]
    assert "real-payment-processing" in result["non_goals"]
    assert "settlement-confirmation" in result["non_goals"]
    assert "card-account-email-or-password-storage" in result["non_goals"]
    assert result["validation_commands"] == [
        "python -m pytest tests/test_billing_payment_reconciliation.py -q",
        "python -m compileall services/billing_payment_reconciliation.py tests/test_billing_payment_reconciliation.py",
    ]
    assert result["real_payment_verified"] is False
    assert_privacy_safe(result)


def test_model_field_names_are_limited_to_privacy_safe_billing_state_fields():
    field_names = privacy_safe_model_field_names()

    for names in field_names.values():
        assert set(names).issubset(
            {
                "provider_event_ref_hash",
                "invoice_ref_hash",
                "plan_change_ref_hash",
                "status",
                "reason_codes",
                "amount_minor",
                "currency",
            }
        )
        assert not any(
            fragment in field_name
            for field_name in names
            for fragment in SENSITIVE_FIELD_FRAGMENTS
        )
