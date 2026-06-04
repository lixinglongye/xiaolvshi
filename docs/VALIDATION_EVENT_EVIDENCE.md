# Validation Event Evidence

This document defines the reviewer contract for the upcoming maintenance
validation-event evidence endpoint:

```http
GET /api/v1/maintenance/validation-event-evidence
POST /api/v1/maintenance/validation-event-evidence
```

The endpoint records metadata-only validation events that are not fully proven
by Git commit cadence. It fills the evidence gap for tests, credential scans,
pushes, reviewer actions, and low-resource legal fixture runs, but it is still
not enough by itself to prove a completed 24-hour maintenance session.

## Purpose

Git history can show that commits happened over time. It cannot prove that a
maintainer ran input validation tests, pushed work to a remote, completed a
credential scan, performed a release or safety review, or ran legal fixture
checks. Validation-event evidence gives reviewers a separate, compact record
for those non-commit activities.

The endpoint should support reviewer questions such as:

- Which metadata-only input validation checks ran during the claimed window.
- Whether a `credential_scan` event exists without exposing scan output.
- Whether a `push` event records remote-publication metadata without storing
  credentials or raw Git output.
- Whether a `review`/`release_review` event records release, safety, or
  OSS-claim review.
- Whether a `legal_fixture` event records synthetic fixture coverage without
  storing raw legal text or raw model output.
- Which validation events can be converted into continuous-session timeline
  events.

## Metadata-Only Contract

`GET` returns the accepted schema, examples, reviewer status, and current
privacy boundary. `POST` accepts only compact event metadata. Valid records may
include:

- `event_type`: `test`, `credential_scan`, `push`, `review`,
  `release_review`, or `legal_fixture`.
- `timestamp`: ISO-8601 timestamp with timezone.
- `check_id`, `run_id`, or `validation_id`: short opaque identifiers or labels
  such as `metadata-input-validation`, `credential-scan`, `git-push`,
  `release-review`, `oss-claim-review`, `legal-fixture-quick-suite`, or
  `local-run-review`.
- `source`: `validation_event_evidence`, `continuous_session_evidence`,
  `maintenance_heartbeat_evidence`, `legal_fixture`, `release_review`, or
  `oss_support_review`.
- `evidence_paths`: repository-safe paths for docs, tests, screenshots,
  summaries, or release notes.
- `commit_hash`: optional Git commit hash associated with the event.
- `status`: `passed`, `failed`, `blocked`, `not_run`, `reviewed`, or
  `collecting`.
- `labels`: short reviewer-safe tags such as `pytest`, `credential-scan`,
  `remote-push`, `release-review`, or `legal-fixture-quick-suite`.
- `summary`: short reviewer-safe description with no sensitive values.

The service should reject oversized payloads and strings that appear to contain
raw logs, legal documents, credentials, emails, or copied model outputs. Input
validation tests should assert that submitted records are metadata only and
that unsafe values are rejected or redacted before persistence.

## Event Semantics

`test` records prove only that a named validation command or metadata-only input
validation check was recorded. They do not preserve raw stdout or stderr.

`credential_scan` records prove only that a scan event occurred, which scanner
label was used, and whether the reviewer-safe result was pass, fail, or
blocked. They must not include matched secret values, surrounding lines, or raw
scanner output.

`push` records prove only that a remote-publication event was recorded. They may
include a remote label, branch label, commit hash, and timestamp, but not remote
URLs with embedded credentials, reflog dumps, or raw command output.

`review` and `release_review` records prove only that a reviewer action was
recorded, such as release readiness, OSS support wording, privacy review, or
public-claim review. They may include an opaque reviewer, check, run, or
validation id, but not private comments, emails, client identities, or vendor
account identifiers.

`legal_fixture` records prove only that a low-resource fixture workflow was
recorded. They may include fixture ids, route labels, coverage scores,
normalizer labels, and evidence paths. They must not include raw legal text,
copied public benchmark samples, raw prompts, raw gateway payloads, raw model
outputs, or private legal matter facts.

## Timeline Conversion

Each accepted validation event can be converted into a continuous-session
timeline event with:

- `event_type` preserved as `test`, `credential_scan`, `push`, `review`,
  `release_review`, or `legal_fixture`.
- `source` normalized to `validation_event_evidence`.
- `timestamp`, `check_id`, `run_id`, `validation_id`, `commit_hash`,
  `status`, `labels`, `evidence_paths`, `summary`, and opaque ids copied only
  after privacy screening.
- `timeline_claim_scope` set to `validation_event`, not `commit_cadence`.

The continuous-session timeline can place these rows beside git-history cadence
events. It must not infer validation events from commits, and it must not
convert one validation event into proof of the entire 24-hour window.

## Privacy Boundary

Validation-event evidence must not store or return:

- Raw stdout, raw stderr, terminal transcripts, command history, or CI log
  bodies.
- API keys, access tokens, passwords, service credentials, signing secrets, or
  secret-like scanner matches.
- Emails, phone numbers, account identifiers, billing provider customer data,
  or remote URLs containing credentials.
- Raw client documents, raw legal text, private legal matter facts, copied
  public benchmark samples, or original legal-source passages.
- Raw prompts, raw model requests, raw gateway payloads, raw model outputs, or
  response bodies from legal fixture runs.
- Raw patches, full diffs, copied hunks, or file contents.

Allowed evidence is limited to timestamps, event types, validation labels,
opaque ids, redacted result states, fixture ids, route labels, aggregate
coverage scores, repository evidence paths, and short reviewer-safe summaries.

## Reviewer Gate

Validation-event evidence supplements git-history evidence. It can prove that
non-commit activity was recorded inside a claimed window, but it still cannot
prove completion unless the joined continuous-session timeline also shows:

1. `completed_medium_large_update_count >= 100`.
2. A longest verified continuous maintenance window of at least 24 hours.
3. Repository-backed work records inside that window.
4. Validation records inside that window, including the relevant non-commit
   events.
5. Privacy screening that excludes raw logs, legal text, credentials, emails,
   and model outputs.

Current reviewer stance: this endpoint closes a major evidence gap left by Git
cadence, but it must keep `ready_for_goal_claim=false` when used alone.

## Related Documents

- `docs/CONTINUOUS_SESSION_TIMELINE.md`
- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/GIT_HISTORY_EVIDENCE.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`

## Reviewer Checks

Run these repository-root checks after documentation updates:

```powershell
rg -n "Validation Event Evidence|validation-event-evidence|credential_scan|legal_fixture|raw stdout|raw stderr|raw legal text|raw model outputs|24-hour" docs
git diff --check
```
