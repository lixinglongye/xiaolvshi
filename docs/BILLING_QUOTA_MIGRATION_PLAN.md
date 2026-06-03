# Billing Quota Migration Plan

This document defines a pure local migration planning contract for billing quota counters. It describes target tables, indexes, unique constraints, idempotent replay behavior, rollback, data minimization, forbidden fields, and dry-run sample checks. It does not connect to a real database, payment provider, network service, router, release workflow, or ledger.

## Scope

- Service: `app/backend/services/billing_quota_migration_plan.py`
- Tests: `app/backend/tests/test_billing_quota_migration_plan.py`
- Documentation: `docs/BILLING_QUOTA_MIGRATION_PLAN.md`

This slice is planning and validation only. Later migration code can use the service output as implementation input, but this service executes no database migration.

## Target Tables

The plan defines these target tables:

- `billing_quota_migration_batches`: batch metadata and rollback state.
- `billing_quota_usage_counters`: sanitized quota counter facts.
- `billing_quota_over_limit_reasons`: normalized blocked reason codes with numeric snapshots.
- `billing_quota_subject_monthly_rollups`: per-subject monthly counters keyed by `quota_subject_hash`.
- `billing_quota_plan_action_daily_rollups`: aggregate plan/action daily counters.
- `billing_quota_over_limit_reason_daily_rollups`: aggregate blocked reason counters.
- `billing_quota_idempotency_keys`: replay-control keys for no-double-count behavior.

The table contract stores opaque subject hashes, local batch keys, idempotency keys, quota windows, plan/action labels, numeric counters, canonical decision statuses, canonical reason codes, and opaque metadata references. It excludes raw payloads and payment artifacts.

## Indexes

The plan includes indexes for:

- Monthly subject quota reads: `quota_subject_hash`, `usage_metric`, `quota_window`.
- Aggregate reconciliation: `plan_type`, `usage_metric`, `quota_window`, `allowed`.
- Batch verification and rollback: `migration_batch_id`, `migrated_at`.
- Over-limit reason joins: `usage_counter_id`, `reason_code`.
- Subject rollup reads: `quota_subject_hash`, `quota_window`.
- Daily aggregate trend reads by date, plan, metric, and reason code.
- Idempotency key expiry by `quota_window`, `usage_metric`, and `last_seen_at`.

## Unique Constraints

Required unique constraints:

- `uq_bq_batches_batch_key`: resumes one local batch for a deterministic batch key.
- `uq_bq_usage_idempotency_key`: prevents applying the same quota counter event twice.
- `uq_bq_usage_source_event_hash`: migrates each sanitized source event once.
- `uq_bq_reason_per_counter`: prevents duplicated reason codes per counter row.
- `uq_bq_subject_monthly_metric`: keeps one monthly subject/metric/window rollup.
- `uq_bq_plan_action_daily`: keeps one aggregate daily plan/action/metric/status row.
- `uq_bq_reason_daily`: keeps one aggregate daily blocked reason row.
- `uq_bq_dedup_idempotency_key`: records one dedup row per idempotency key.

Conflict behavior must be deterministic: exact replays are no-ops; same key with different event hash quarantines the batch; same event hash with different key is rejected until reconciled.

## Idempotency And Replay

Replay uses the sanitized quota event `idempotency_key` where available and a canonical `source_event_hash` computed from approved fields only. Batch keys follow:

```text
bqmp:v1:{source_dataset_hash}:{plan_version}:{batch_started_day}
```

Replay phases:

1. Preflight sanitized exports and reject forbidden fields.
2. Create or resume one migration batch by deterministic `batch_key`.
3. Canonicalize each event, compute `source_event_hash`, and upsert the idempotency key.
4. Insert `billing_quota_usage_counters` only after dedup succeeds.
5. Apply additive deltas to subject, plan/action, and reason rollups.
6. Verify schema, uniqueness, replay, reconciliation, and rollback checks.

No replay key may embed user IDs, emails, file names, order IDs, payment provider IDs, prompts, or document text.

## Rollback Plan

Rollback is batch scoped:

- Mark the batch `rollback_requested` and stop replay attempts for that `batch_key`.
- Use `migration_batch_id` to identify counter rows and reason rows written by the batch.
- Subtract the batch deltas from monthly and daily rollups.
- Delete or tombstone idempotency keys only after rollup deltas balance to zero.
- Mark the batch `rolled_back` with count metadata and check time.
- Keep aggregate rollback evidence only.

Rollback does not refund payments, mutate invoices, change routers, alter release gates, or update the continuous ledger. This service does not execute rollback SQL.

## Data Minimization

Allowed categories:

- Opaque subject hashes.
- Quota windows.
- Plan and action categories.
- Numeric quota counters.
- Canonical decision statuses and reason codes.
- Opaque trace and entitlement references.
- Idempotency and migration batch keys.

Forbidden categories:

- Direct user, organization, client, or contact identifiers.
- Legal document text, generated document text, prompts, messages, request bodies, and response bodies.
- File names or upload metadata that can identify a matter.
- Payment provider objects, checkout sessions, invoices, receipts, cards, customer IDs, and subscription IDs.
- Credentials, tokens, headers, connection strings, and secrets.

The validator reports paths and finding types only. It does not echo sensitive sample values in its result.

## Forbidden Fields

Forbidden fields include `user_id`, `user_email`, `client_email`, `client_name`, `document_text`, `contract_text`, `legal_text`, `prompt`, `message`, `raw`, `request_body`, `response_body`, `file_name`, `payment`, `stripe`, `checkout_session`, `invoice`, `receipt`, `card`, `customer_id`, `subscription_id`, `order_id`, `api_key`, `authorization`, `headers`, `password`, `secret`, `session_token`, and `database_url`.

## Sample Migration Checks

Sample checks are dry-run evidence objects. Required fields:

- `check_id`
- `check_type`
- `target`
- `status`

Required check types before an actual migration implementation:

- `schema_contract`
- `forbidden_columns`
- `unique_constraints`
- `idempotency_replay`
- `rollup_reconciliation`
- `rollback_reversibility`

Allowed statuses are `pass`, `warn`, and `fail`. A blocking sample check that is not `pass` fails the plan. Missing required check coverage produces a warning. Forbidden fields or sensitive values fail the plan.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_billing_quota_migration_plan.py -q
python -m compileall services/billing_quota_migration_plan.py tests/test_billing_quota_migration_plan.py
```
