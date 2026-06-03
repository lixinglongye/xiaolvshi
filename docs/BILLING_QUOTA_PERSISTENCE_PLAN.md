# Billing Quota Persistence Plan

This plan defines a pure local contract for future billing quota counter persistence. It is intentionally limited to schema, validation, aggregation, retention, idempotency, and privacy controls. It does not connect to a database, payment provider, network service, router, release workflow, or ledger.

## Scope

- Service: `app/backend/services/billing_quota_persistence_plan.py`
- Tests: `app/backend/tests/test_billing_quota_persistence_plan.py`
- Documentation: `docs/BILLING_QUOTA_PERSISTENCE_PLAN.md`

The service can be called by later integration code, but this slice only adds a local planning and validation module.

## Privacy-Safe Usage Counter Schema

The supported event type is `billing_quota_usage_counter`.

Required fields:

- `event_id`
- `event_type`
- `timestamp`
- `idempotency_key`
- `quota_subject_hash`
- `plan_type`
- `action`
- `usage_metric`
- `units`
- `quota_window`
- `counter_bucket`
- `allowed`
- `decision_status`

Recommended fields:

- `policy_version`
- `entitlement_snapshot_id`
- `source_component`
- `request_units`
- `limit`
- `used_before`
- `remaining_before`
- `remaining_after`
- `over_limit_reason_codes`

The schema permits only opaque subject hashes, plan/action categories, quota windows, numeric counter snapshots, canonical reason codes, and local metadata references. It forbids direct user IDs, client details, legal content, prompts, raw request or response bodies, file names, payment objects, provider IDs, credentials, and free-text reason messages.

## Aggregation Buckets

The plan defines four local buckets:

- `subject_metric_monthly`: monthly per-subject counter by opaque `quota_subject_hash`, plan, metric, and quota window.
- `plan_action_daily`: daily aggregate reporting by plan, action, metric, and allowed/blocked status.
- `over_limit_reason_daily`: daily blocked counters by canonical reason code.
- `idempotency_key_dedup`: replay-control bucket that prevents duplicate counting for the same deterministic key.

All buckets are counter or metadata buckets. None store prompt text, document text, client identity, payment provider objects, or raw payloads.

## Retention Policy

- Rejected events: delete immediately.
- Passing sanitized debug samples: keep for up to 7 days only if needed.
- Monthly subject counters: keep for 400 days after bucket end.
- Daily plan/action counters: keep for 400 days.
- Daily over-limit reason counters: keep for 400 days.
- Idempotency dedup keys: keep for 45 days after bucket end.

This is not a matter audit log or payment ledger. It must not be used to retain legal content or provider billing records.

## Idempotency Keys

Every persisted counter event requires an idempotency key:

```text
bqp:v1:{quota_subject_hash_or_hash}:{quota_window}:{action}:{usage_metric}:{source_event_hash}
```

Collision behavior is `same_key_same_counter_delta_no_double_count`. Keys must be deterministic and opaque. They must not embed user IDs, emails, file names, order IDs, payment IDs, or provider subscription IDs.

## Over-Limit Reason Persistence

Blocked decisions must persist canonical reason data:

- `code`
- `metric`
- `limit`
- `used`
- `requested`
- `remaining`
- `quota_window`
- `policy_version`
- `blocked_at`
- `source_component`

Free-text reason messages are intentionally excluded. API or UI layers should render messages from canonical codes.

## Forbidden Fields

Forbidden fields include:

- Prompt, message, raw, request body, response body, document text, legal text, and full document fields.
- File names and client contact fields.
- User IDs, user emails, payment session IDs, Stripe or payment provider IDs, invoice and receipt fields.
- API keys, bearer tokens, authorization headers, passwords, secrets, and session tokens.

The validator reports field names, paths, and finding types only; it does not echo sensitive values back in its result.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_billing_quota_persistence_plan.py -q
python -m compileall services/billing_quota_persistence_plan.py tests/test_billing_quota_persistence_plan.py
```
