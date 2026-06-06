# Continuous Session Review Packet

This document defines the reviewer contract for the upcoming maintenance
review-packet endpoint:

```http
GET /api/v1/maintenance/continuous-session-review-packet
POST /api/v1/maintenance/continuous-session-review-packet
```

The endpoint builds a reviewer/support packet from existing maintenance
evidence surfaces. It is an evidence index and review aid, not a new source of
completion claims.

## Purpose

The review packet summarizes the continuous maintenance claim in one compact
surface by joining:

- the continuous update ledger,
- the continuous session timeline,
- git-history cadence evidence, and
- validation-event evidence for tests, credential scans, pushes, reviews, and
  low-resource legal fixture checks.

The packet should help a reviewer or support form owner answer:

- Which evidence sections are present, missing, blocked, or privacy-filtered.
- Whether the 100+ medium/large update target is reviewable through repository
  evidence.
- Whether timestamped events prove a real 24-hour continuous maintenance
  window.
- Which repository paths support each section.
- Which blockers and review questions remain before any public or support
  application claim can be made.

## Endpoint Shape

`GET` returns the current packet template, reviewer status, section statuses,
privacy boundary, and evidence paths that can be inspected in the repository.
It may include computed hashes for packet integrity and source-state drift
detection.

`POST` accepts only compact reviewer metadata for assembling or checking a
packet. Valid submitted metadata may include:

- `packet_id`: opaque reviewer or support packet label.
- `generated_at`: ISO-8601 timestamp with timezone.
- `source_sections`: section labels such as `continuous_update_ledger`,
  `continuous_session_timeline`, `git_history_cadence`, and
  `validation_event_evidence`.
- `section_statuses`: per-section `ready`, `collecting`, `blocked`,
  `missing`, or `privacy_filtered` states.
- `hash`: deterministic packet or section hash.
- `evidence_paths`: repository-safe paths to docs, tests, screenshots,
  summaries, or release notes.
- `blockers`: short reviewer-safe blockers.
- `review_questions`: short questions that a reviewer still needs answered.
- `privacy_boundary`: the active metadata-only boundary used for the packet.
- `low_resource_fixture_review`: optional payload with one or more local
  gateway fixture responses. The packet runs the same deterministic
  `/legal-review-benchmark/local-run-review` normalization and keeps only
  status, counts, check ids, sensitive/invalid/total rejection counts,
  release-decision labels, and
  safe evidence boundaries.

The endpoint may reference command labels such as `pytest`, `rg`, `npm run
typecheck`, `git diff --check`, `credential-scan`, or
`legal-fixture-quick-suite`, but it must not store the raw command output.

## Packet Sections

The packet should keep source sections separate:

- `continuous_update_ledger`: update volume, shipped evidence paths, and
  remaining update or release blockers.
- `continuous_session_timeline`: timestamped event stream, longest verified
  window, gap analysis, and source merge status.
- `git_history_cadence`: commit count, longest git-derived cadence window,
  maximum observed gap, and commit-cadence readiness.
- `validation_event_evidence`: metadata-only rows for non-git test,
  credential-scan, push, review/release-review, and legal-fixture events.
- `low_resource_fixture_review`: optional local-run-review status, observed
  fixture count, not-run count, warning/blocking counts, redaction count, and
  raw-output exclusion flags.
- `review_questions`: human-readable questions for support or reviewer follow
  up.
- `privacy_boundary`: explicit exclusions and the allowed metadata fields.

Section status must be conservative. A ready ledger section does not make the
timeline ready. A ready git-cadence section does not prove tests, pushes,
credential scans, legal fixtures, or release review. A ready validation-event
section does not prove the full 24-hour window without joined timestamped
repository-backed work.

## Metadata-Only Contract

The review packet outputs metadata only. Allowed packet fields include:

- section names and section statuses,
- packet or section hashes,
- repository `evidence_paths`,
- opaque ids,
- timestamps,
- event counts,
- cadence and gap metrics,
- blockers,
- review questions,
- reviewer-safe summaries, and
- the privacy boundary.

For `low_resource_fixture_review`, the packet may expose:

- `low_resource_fixture_review_status`,
- observed and not-run fixture counts,
- warning and blocking check counts,
- redacted response count,
- safe check ids and status counts, and
- flags proving that raw gateway responses, raw fixture payloads, and raw model
  outputs were not included.

The packet must not store or return:

- raw logs, raw stdout, raw stderr, terminal transcripts, command history, or
  CI log bodies,
- complete legal texts, raw client documents, copied public benchmark samples,
  or original legal-source passages,
- raw prompts, raw model requests, gateway payloads, raw model output, or
  original model responses,
- API keys, access tokens, passwords, service credentials, signing secrets, or
  scanner matches,
- emails, phone numbers, billing provider customer data, account credentials,
  or remote URLs containing credentials,
- raw patches, full diffs, copied hunks, or file contents, and
- private reviewer comments that identify a client, matter, account, attorney,
  reviewer, or vendor beyond repository-safe opaque ids.

If a source contains unsafe details, the packet should mark that section
`privacy_filtered` or `blocked` and expose only reviewer-safe metadata.

## Reviewer Gate

The review packet cannot independently claim that the 24-hour maintenance goal
is complete. It can only say whether the joined evidence appears ready for
review.

The packet may set a ready status only when all of these are true:

1. `completed_medium_large_update_count >= 100` is supported by repository
   evidence in the continuous update ledger.
2. Real timestamped events prove a continuous maintenance window of at least
   24 hours.
3. The window includes repository-backed work, not only empty heartbeat rows.
4. The window includes validation evidence for relevant non-commit activity,
   such as tests, credential scans, pushes, review/release-review actions, or
   legal fixture checks.
5. If `low_resource_fixture_review` is supplied, it has at least one normalized
   fixture observation and is not failed; one- or two-fixture runs may remain
   review evidence rather than release-ready evidence.
6. Privacy screening confirms that the packet contains metadata only.

Current reviewer stance: repository evidence supports the 100+ update volume,
but the 24-hour continuous session remains unproven unless real timestamped
events and the 100+ update evidence both satisfy the joined gate. The packet
must keep `ready_for_goal_claim=false` when either side is missing.

## Support Packet Language

Safe support language:

> The repository has a metadata-only reviewer packet that indexes the continuous
> update ledger, timeline, git cadence, and validation-event evidence. It shows
> which sections are ready or blocked and lists repository evidence paths for
> reviewer inspection.

Unsafe support language:

> The review packet proves that a 24-hour maintenance session is complete.

The unsafe statement is not allowed unless the underlying timestamped events
and the 100+ medium/large update evidence both pass the reviewer gate.

## Related Documents

- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/CONTINUOUS_SESSION_TIMELINE.md`
- `docs/GIT_HISTORY_EVIDENCE.md`
- `docs/VALIDATION_EVENT_EVIDENCE.md`
- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`

## Reviewer Checks

Run these repository-root checks after documentation or endpoint updates:

```powershell
rg -n "Continuous Session Review Packet|continuous-session-review-packet|metadata-only|section_statuses|evidence_paths|review questions|privacy boundary|raw stdout|raw stderr|raw model output|24-hour|100\\+" docs
git diff --check
```
