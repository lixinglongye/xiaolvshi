# Billing Entitlement Gap Evidence

This slice adds deterministic backend evidence for the billing-entitlements product gap without integrating a live payment gateway.

## Implemented evidence

- `payment-activation-audit`: verifies that an entitlement grant only follows a paid order.
- `sku-plan-match-guard`: blocks subscription activation when the requested plan does not match the SKU mapping.
- `report-unlock-target-guard`: blocks single-report unlocks unless `related_review_id` is present.
- `monthly-usage-plan-guard`: checks plan status, quota, remaining usage, and admin bypass behavior.

The implementation is intentionally local and deterministic:

- Service: `app/backend/services/billing_entitlement_gap.py`
- Tests: `app/backend/tests/test_billing_entitlement_gap.py`

## Remaining product gaps

- Stripe webhook signature verification.
- Refund and chargeback state machine.
- Subscription renewal and billing-period rollover audit.
- Frontend entitlement state messaging.
- Persistent audit table for payment and entitlement grant events.

## Validation

Run the small backend slice locally:

```powershell
cd app/backend
python -m pytest tests/test_billing_entitlement_gap.py -q
python -m py_compile services/billing_entitlement_gap.py
```

## Privacy note

The audit payload redacts payment session identifiers and does not include API keys, raw card data, or payment provider secrets.
