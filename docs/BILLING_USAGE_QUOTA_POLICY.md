# Billing Usage Quota Policy

This slice adds a deterministic local policy service for billing usage and quota decisions. It is designed for a low-cost model-first legal product and deliberately avoids real payment processing, network calls, secrets, router changes, release changes, and ledger changes.

## Scope

- Service: `app/backend/services/billing_usage_quota_policy.py`
- Tests: `app/backend/tests/test_billing_usage_quota_policy.py`
- Documentation: `docs/BILLING_USAGE_QUOTA_POLICY.md`

The service can be called by future routers or workflows, but this change does not wire it into any router.

## Covered Quotas

- Plan limits: extends the existing public product catalog report quotas into a local usage policy snapshot.
- Document uploads: guards monthly upload count, per-file upload size, and aggregate document storage.
- Review credits: guards monthly review credit consumption.
- Generated docs: guards monthly generated document quotas.
- Premium model escalations: keeps premium model use explicit, plan-limited, and approval-gated where required.
- Over-limit reasons: returns structured reason codes with metric, limit, used, requested, and remaining values.
- Privacy-safe aggregation: aggregates usage counters without prompts, document text, file names, user IDs, payment session IDs, API keys, or secrets.

## Low-Cost Model-First Behavior

Normal review and document-generation actions recommend the cheap tier by default. If a normal action requests a premium tier, the policy blocks the action with `premium_escalation_required`; callers should evaluate a separate `premium_model_escalation` request before running premium inference.

Premium escalation is local and deterministic:

- Free plans do not allow premium escalation.
- Personal and Lawyer plans allow limited premium escalations only with local operator approval.
- Enterprise plans allow higher premium escalation capacity without per-call operator approval.
- Admin usage is treated as an internal unlimited local policy path.

## Non-Goals

- No Stripe, checkout, webhook, refund, chargeback, or subscription renewal implementation.
- No network calls.
- No secrets or payment provider credentials.
- No router integration.
- No release readiness or ledger changes.
- No persistent usage storage.

## Validation

Run the slice from `app/backend`:

```powershell
python -m pytest tests/test_billing_usage_quota_policy.py -q
python -m compileall services/billing_usage_quota_policy.py tests/test_billing_usage_quota_policy.py
```

## Privacy Note

Usage aggregation is aggregate-only. It records counters, plan/action categories, model tier, token totals, and reason code counts. It excludes raw prompts, document text, file names, user IDs, email addresses, payment session IDs, API keys, and other secrets.
