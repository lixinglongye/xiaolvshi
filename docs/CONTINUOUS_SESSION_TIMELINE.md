# Continuous Session Timeline

This document defines the reviewer contract for the implemented maintenance
timeline endpoint:

```http
GET /api/v1/maintenance/continuous-session-timeline
POST /api/v1/maintenance/continuous-session-timeline
GET /api/v1/maintenance/git-history-evidence
GET /api/v1/maintenance/validation-event-evidence
POST /api/v1/maintenance/validation-event-evidence
```

The timeline is a reviewer-facing evidence join. It must not be treated as a
new source of completion claims. The repository already has reviewable evidence
for 100+ medium/large maintenance updates, but the continuous 24-hour window is
still unproven until timestamped metadata records demonstrate it. Git-history
evidence can help prove commit cadence, but commit cadence alone does not prove
tests, pushes, credential scans, legal fixture runs, or release readiness.
Validation-event evidence fills those non-commit rows with metadata-only
records, but it still cannot prove a 24-hour window by itself.

## Purpose

The endpoint merges maintenance evidence that currently lives across separate
reviewer surfaces:

- the continuous update ledger,
- the continuous session validator,
- heartbeat records,
- git commit metadata,
- validation-event evidence for metadata-only tests, credential scans, pushes,
  reviews, and legal fixture checks,
- low-resource legal fixture events, and
- release review or OSS support evidence.

The output should let a reviewer inspect the claimed maintenance window in time
order, see which records are backed by repository evidence, and understand why
the 24-hour gate remains blocked when the records do not prove a full window.

## Metadata-Only Input

`GET` returns a metadata collection template and current reviewer status.
`POST` accepts only compact metadata records. Valid event records may
include:

- `event_type`: `commit`, `test`, `push`, `review`, `credential_scan`,
  `benchmark`, `legal_fixture`, `doc_update`, `heartbeat`, or
  `commit_cadence`.
- `timestamp`: ISO-8601 timestamp with timezone.
- `source`: `continuous_update_ledger`, `continuous_session_evidence`,
  `maintenance_heartbeat_evidence`, `git_history_evidence`,
  `validation_event_evidence`, `legal_fixture`, or `release_review`.
- `evidence_paths`: repository paths for code, tests, docs, screenshots, or
  release notes.
- `validation_id`: short command or review label, such as `pytest`,
  `typecheck`, `credential-scan`, `legal-fixture-quick-suite`,
  `local-run-review`, or `release-review`.
- `commit_hash`, `run_id`, or `review_id`: optional opaque identifiers.
- `summary`: short reviewer-safe summary with no sensitive values.

The timeline derives aggregate fields such as `completed_update_count`,
`longest_verified_window_hours`, `has_validation_record`,
`has_repository_backed_work`, and `completion_ready`. These fields are computed
from metadata and must keep the 100+ update count separate from the 24-hour
time-window proof.

`GET /api/v1/maintenance/git-history-evidence` contributes only git-derived
cadence fields such as `commit_count`, `longest_window_hours`,
`max_observed_gap_hours`, `max_allowed_gap_hours`, `commit_cadence_ready`, and
`ready_for_goal_claim=false`. The timeline displays these beside validator
records, but it must not convert a commit cadence row into a test, push, scan,
or fixture claim.

`GET`/`POST` `/api/v1/maintenance/validation-event-evidence` contributes
metadata-only validation rows for `test`, `credential_scan`, `push`,
`review`/`release_review`, and `legal_fixture` events. These rows can be
converted into timeline events when they include a timestamp, event type,
validation label, reviewer-safe summary, opaque ids, and repository evidence
paths. They must not include raw stdout, raw stderr, credentials, emails, raw
legal text, raw prompts, raw model requests, raw gateway payloads, raw model
outputs, or copied benchmark text.

## Evidence Merge Rules

The timeline normalizes records into one ordered event stream:

- Ledger events prove update volume and shipped evidence. They do not prove
  continuous time coverage by themselves.
- Session validator events prove whether the submitted timestamps can form a
  valid 24-hour maintenance window.
- Heartbeat events provide raw timestamp markers for commits, tests, pushes,
  and reviews.
- Git-history events compute real commit cadence from commit metadata,
  including longest window, maximum adjacent-commit gap, and included commit
  count.
- Validation-event records fill non-git rows for input validation tests,
  credential scans, pushes, reviewer/release-review actions, and low-resource
  legal fixture checks using timestamps, opaque check/run/validation IDs,
  commit hashes, status labels, tags, and repository evidence paths only.
- Low-resource legal fixture events provide laptop-safe legal quality checks
  using fixture IDs, route labels, coverage scores, and validation command
  labels.
- Release review evidence records release readiness, OSS support wording, and
  public-claim guardrails.

When sources disagree, reviewer status stays restrictive, so an unproven
24-hour window remains blocked even when the 100+ update target or git cadence
evidence is satisfied.

## Privacy Boundary

Timeline storage and responses must not contain:

- API keys, access tokens, service credentials, or secret-like values.
- Account identifiers, account credentials, emails, phone numbers, or billing
  provider customer data.
- Raw client documents, raw legal matter text, copied public benchmark samples,
  or original legal-source passages.
- Raw patches, full diffs, copied hunks, or file contents.
- Raw stdout, raw stderr, terminal transcripts, command history, CI log bodies,
  scanner matches, or remote URLs containing credentials.
- Raw prompts, raw model requests, raw gateway responses, or model original
  outputs.
- Private comments that identify a client, matter, account, attorney, reviewer,
  or vendor beyond repository-safe opaque ids.

Allowed evidence is limited to timestamps, event types, opaque ids, commit
hashes, aggregate path counts, cadence metrics, route labels, fixture ids,
coverage scores, command labels, reviewer status, and repository evidence
paths.

## Reviewer Gate

The reviewer-safe completion gate remains:

1. `completed_medium_large_update_count >= 100`.
2. The longest verified continuous maintenance window is at least 24 hours.
3. The window includes repository-backed work and validation evidence.
4. Legal fixture records are metadata-only and low-resource by default.
5. Release review evidence does not claim completion before the timeline proves
   both update volume and continuous time coverage.
6. Git-history evidence is labeled as commit cadence only and does not fill in
   missing test, push, credential-scan, or legal-fixture evidence.
7. Validation-event evidence may fill those missing non-commit event rows, but
   it still must be joined with timestamped repository-backed work across the
   full window before any 24-hour completion claim is allowed.

Current state: the 100+ update target is satisfied by repository evidence, but
the 24-hour continuous session is still not proven. The timeline should make
that distinction explicit in `summary`, `gap_analysis`, and any reviewer text.

## Related Documents

- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/GIT_HISTORY_EVIDENCE.md`
- `docs/VALIDATION_EVENT_EVIDENCE.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`

## Reviewer Checks

Run these repository-root checks after documentation or endpoint updates:

```powershell
rg -n "Continuous Session Timeline|continuous-session-timeline|validation-event-evidence|git-history-evidence|commit cadence|credential_scan|legal_fixture|100\\+|24-hour|metadata-only|raw stdout|raw stderr|raw model outputs|raw legal" docs
git diff --check
```
