# Continuous Session Run Monitor

This document defines the reviewer contract for the implemented active-run
monitor endpoint:

```http
GET /api/v1/maintenance/continuous-session-run-monitor
POST /api/v1/maintenance/continuous-session-run-monitor
```

The monitor is metadata-only. It helps maintainers watch an active 24-hour
maintenance attempt by joining the continuous update ledger, continuous-session
timeline, and review-packet summaries. It is not standalone proof that a 24h
maintenance window has completed.

## Purpose

The endpoint answers operational questions during a claimed maintenance run:

- How many timestamped events have been submitted.
- Whether the 100+ medium/large update count is already reviewable.
- How many hours have elapsed since the submitted start timestamp.
- How large the current gap is since the latest timestamped event.
- When the next metadata-only checkpoint is due.
- Which required evidence types are still missing.
- Which blockers and next actions should remain visible to a reviewer.

The monitor can make a run easier to manage, but it cannot convert an empty
timer, an unstamped note, or a derived summary into 24h proof. The proof still
requires real timestamped events that are joined and reviewed through the
timeline and review packet.

## Metadata-Only Input

`GET` returns the current template and conservative default status.

`POST` accepts compact run metadata. Valid submitted fields may include:

- `current_timestamp`: ISO-8601 timestamp with timezone for the monitor check.
- `session_start_timestamp` or `start_timestamp`: ISO-8601 timestamp with
  timezone for the claimed run start.
- `checkpoint_interval_hours`: bounded checkpoint interval for expected
  active-run updates.
- `max_allowed_gap_hours`: bounded maximum adjacent event gap.
- `events`, `validation_events`, or `heartbeat_events`: metadata-only event
  rows that can be passed into the continuous-session timeline.
- `git_history` or `git_since`: git-cadence metadata inputs used by the
  timeline, without raw command output.

Allowed event rows are limited to event type, timestamp, source label,
repository evidence paths, validation labels, status labels, commit hashes, and
opaque run or review identifiers. Short reviewer-safe summaries are allowed
only when they contain no sensitive or case-specific content.

The endpoint must not store or echo raw payloads. It must not store raw logs,
raw legal text, raw model outputs, credentials, emails, raw prompts, gateway
payloads, terminal transcripts, raw stdout, or raw stderr.

## Output Shape

`ContinuousSessionRunMonitorService().build_monitor(payload)` returns:

- `status`: `not_started`, `running`, `at_risk`, `blocked`, or
  `ready_for_review`.
- `summary`: update-count readiness, submitted and valid event counts,
  verified continuous hours, remaining hours, current gap, next checkpoint,
  blocker count, and `completion_ready`.
- `run_window`: submitted start timestamp, latest event timestamp, current
  timestamp, and the best window reported by the timeline.
- `required_evidence`: readiness for commit, test, push, review,
  credential-scan, and low-resource legal fixture evidence.
- `blockers`: hard or review blockers copied only as reviewer-safe metadata.
- `next_actions`: checkpoint, validation, and missing-evidence actions.
- `checkpoint_policy`: interval and gap rules for the active run.
- `source_summaries`: compact ledger, timeline, and review-packet summaries.
- `privacy_boundary`: explicit flags showing that raw logs, legal text, model
  outputs, credentials, and emails are excluded.
- `validation_commands`: labels for focused checks that a maintainer can run
  outside the monitor.

`completion_ready` is a derived review flag, not a public completion claim. A
support application or release note must still cite the underlying timestamped
events and repository evidence paths.

## Reviewer Gate

The monitor must keep the 100+ update proof separate from the 24h time-window
proof. It may show that the update count is ready while the active run remains
blocked.

The monitor cannot prove 24h completion unless all of the following are true in
the underlying evidence:

1. Real timestamped events cover a continuous maintenance window of at least 24
   hours.
2. Adjacent valid events stay within the configured maximum gap.
3. The event stream includes repository-backed work, not only heartbeat or
   status rows.
4. Required evidence types are present: commit, test, push, review,
   credential-scan, and low-resource legal fixture evidence.
5. The continuous update ledger still supports at least 100 medium/large
   repository-backed updates.
6. The review packet marks the joined evidence ready without crossing the
   metadata-only privacy boundary.

Current reviewer stance: the run monitor is an active-session dashboard. It
does not prove the 24h target by itself and must remain conservative until real
timestamped events exist.

## Support Language

Safe support language:

> The repository includes a metadata-only active-run monitor for the continuous
> maintenance evidence workflow. It reports submitted timestamped event counts,
> current gaps, missing required evidence, blockers, next checkpoints, and
> repository evidence paths for reviewer inspection.

Unsafe support language:

> The run monitor proves the 24h maintenance session is complete.

That statement is not allowed unless the underlying real timestamped events,
ledger evidence, timeline, and review packet all pass the reviewer gate.

## Related Documents

- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/CONTINUOUS_SESSION_TIMELINE.md`
- `docs/CONTINUOUS_SESSION_REVIEW_PACKET.md`
- `docs/VALIDATION_EVENT_EVIDENCE.md`
- `docs/GIT_HISTORY_EVIDENCE.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/RELEASE_READINESS.md`

## Reviewer Checks

Run these repository-root checks after documentation or endpoint updates:

```powershell
rg -n "Continuous Session Run Monitor|continuous-session-run-monitor|metadata-only|timestamped events|raw logs|raw legal text|raw model outputs|credentials|emails|24h" docs
git diff --check -- docs
```
