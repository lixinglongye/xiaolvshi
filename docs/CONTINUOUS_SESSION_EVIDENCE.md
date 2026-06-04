# Continuous Session Evidence

This document defines the reviewer-facing product contract and backend metadata
validator for a continuous 24-hour maintenance window. It does not claim that
the 24-hour window has already been completed.

## Product Purpose

The project already has repository evidence for 100+ medium/large maintenance
updates. The remaining product gap is proving that the maintenance work also
covered a continuous 24-hour window with reviewable, timestamped records.

The intended capability is a maintenance reviewer view that can answer:

- Which timestamped commits, test runs, pushes, and review actions cover the
  claimed window.
- Whether the longest verified window reaches 24 hours.
- Whether every record points to repository-safe evidence paths.
- Whether small legal-document checks were run in a low-resource mode instead
  of relying on large external datasets or uncommitted model output.
- Whether the system is still blocking completion because the time window is
  incomplete.

## Validation Contract

The implemented validator is exposed at:

```http
GET /api/v1/maintenance/continuous-session-evidence
POST /api/v1/maintenance/continuous-session-evidence
```

`GET` returns a collecting template. `POST` accepts only metadata records:

- `event_type`: one of `commit`, `test`, `push`, `review`,
  `credential_scan`, `benchmark`, `legal_fixture`, `doc_update`, or
  `heartbeat`.
- `timestamp`: an ISO-8601 timestamp with timezone.
- `evidence_paths`: repository paths for code, tests, docs, screenshots, or
  release notes.
- `validation_id`: a short label such as `pytest`, `typecheck`, `build`,
  `credential-scan`, `legal-fixture-quick-suite`, or `release-review`.
- `commit_hash` or `run_id`: optional opaque identifiers.

It should reject or redact account credentials, API keys, email addresses, raw
client documents, raw prompts, raw model outputs, copied public benchmark
examples, and private legal matter text.

## Completion Gate

The reviewer-safe gate is:

1. `completed_medium_large_update_count >= 100`.
2. The longest verified continuous maintenance window is at least 24 hours.
3. The window includes at least one repository-backed work record and one
   validation record.
4. Legal fixture evidence, when included, comes from laptop-safe synthetic
   fixtures or reviewed public benchmark metadata, not large default downloads.

Current state: the 100+ update target is satisfied by repository evidence, and
the validator exists, but the actual 24-hour continuous window remains
unproven until real timestamped records are submitted. Any reviewer form or
support application should state that clearly.

## Low-Resource Legal Fixture Evidence

The low-resource legal-document path is part of the time-window evidence because
the user's machine may not be able to run large benchmarks. A valid record can
reference:

- `GET /api/v1/maintenance/legal-review-benchmark/quick-suite?fixture_limit=2`
- `POST /api/v1/maintenance/legal-review-benchmark/local-run-review`
- `POST /api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle`

The record should keep only fixture IDs, route labels, coverage scores,
validation commands, and evidence paths. It must not store raw gateway payloads,
private legal text, credentials, or full public benchmark samples.

## Product Gap

The current product evidence is still incomplete because reviewers cannot yet
see a persisted frontend timeline that joins:

- the 100+ update ledger,
- heartbeat records,
- push/test validation records,
- low-resource legal fixture evidence, and
- release-safe OSS support claims.

This gap should stay visible in the product feature radar until the validator is
wired into the reviewer-facing maintenance page and backed by real session
records.

## Reviewer Checklist

- Confirm the ledger still reports 100+ reviewable updates.
- Confirm the continuous window uses timestamped records and reaches 24 hours.
- Confirm every evidence path exists in the repository or published Git history.
- Confirm small legal-document checks use synthetic fixtures or reviewed
  metadata-only public benchmark mappings.
- Confirm completion is blocked when either the 24-hour window or validation
  evidence is missing.

## Related Documents

- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_continuous_session_evidence.py -q
```
