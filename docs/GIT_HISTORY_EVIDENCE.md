# Git History Evidence

This document defines the reviewer contract for the implemented maintenance
evidence endpoint:

```http
GET /api/v1/maintenance/git-history-evidence
```

The endpoint derives a reviewer-safe maintenance cadence summary from
Git commit metadata. It is not a session validator, test report, push log,
credential scan, legal benchmark run, or model-output archive.

## Purpose

Reviewers need a way to inspect the real repository timeline without asking a
maintainer to paste private shell output or raw patches into a support form.
The endpoint extracts only commit-level metadata and computes cadence
signals that answer:

- How many commits are included in the reviewed range.
- Which commit timestamps form the longest continuous cadence window.
- What the maximum gap is between adjacent included commits.
- Whether the commit cadence supports a maintenance activity claim.
- Which repository-safe documentation explains the limits of the claim.

These signals prove commit cadence only. They do not automatically prove that
tests passed, code was pushed to a remote, credential scanning ran, or
low-resource legal fixtures were executed.

## Metadata Source

The endpoint reads from local Git metadata by default, using commit hash,
committer timestamp, and subject line. Submitted metadata can also be evaluated
through `POST /api/v1/maintenance/git-history-evidence`.

Allowed response fields include:

- `commit_hash`: short or full hash.
- `timestamp`: ISO-8601 committer timestamp with timezone.
- `title`: short commit subject after privacy screening.
- `commit_count`: count of commits included in the reviewed range.
- `longest_window_hours`: duration between the first and last commit in the
  longest cadence window that satisfies the configured gap threshold.
- `max_observed_gap_hours`: largest gap between adjacent commits in the longest
  window.
- `max_allowed_gap_hours`: configured threshold used for the cadence window.
- `commit_cadence_ready`: whether commit cadence reaches the 24-hour target.
- `ready_for_goal_claim`: always `false` for this endpoint alone.

The response may include repository evidence paths for reviewer documents, but
it does not include raw file diffs.

## Cadence Calculations

Cadence calculations are deterministic:

1. Collect commits in the configured branch or range.
2. Sort included commits by the selected timestamp.
3. Compute gaps between adjacent commits.
4. Split windows whenever a gap exceeds `max_allowed_gap_hours`.
5. Report the longest window by elapsed time.
6. Report `max_observed_gap_hours` across the longest cadence window.
7. Report `commit_count` separately from the longest-window commit
   count when those values differ.

The calculation can support a reviewer statement such as "the repository shows
frequent commits across this window." It must not support a stronger statement
such as "all commits were tested" unless separate test evidence exists.

## Claim Boundaries

The endpoint must keep these claims separate:

- Commit cadence: supported by Git commit metadata.
- Test execution: supported only by test logs, CI records, or explicit
  validation metadata from a separate evidence source.
- Push evidence: supported only by remote hosting metadata, reflog-compatible
  push records, or explicit reviewer metadata from a separate evidence source.
- Credential scan evidence: supported only by a scan command record or CI scan
  record from a separate evidence source.
- Low-resource legal fixture evidence: supported only by fixture IDs, route
  labels, coverage metadata, and validation command records from the legal
  fixture evidence flow.

When a reviewer surface joins git-history evidence with continuous-session
timeline evidence, it labels git-derived rows as commit cadence and does not
infer missing test, push, scan, or fixture rows from commits alone.

## Privacy Boundary

Git-history evidence must not store or return:

- API keys, access tokens, service credentials, passwords, or secret-like
  values.
- Account identifiers, account credentials, emails, phone numbers, or billing
  provider customer data.
- Raw legal text, raw client documents, copied benchmark samples, or original
  legal-source passages.
- Raw patches, full diffs, file contents, or copied hunks.
- Raw prompts, raw model requests, raw model responses, gateway payloads, or
  model original outputs.
- Private reviewer comments or author identity details beyond opaque local
  commit metadata that is already present in Git history.

If commit subjects contain sensitive values, the endpoint redacts them or
replace them with opaque labels before exposing them to reviewer surfaces.

## Reviewer Checks

Run these repository-root checks after documentation or endpoint updates:

```powershell
rg -n "Git History Evidence|git-history-evidence|commit cadence|longest_window|max_observed_gap|ready_for_goal_claim" docs
git diff --check
```

## Related Documents

- `docs/CONTINUOUS_SESSION_TIMELINE.md`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
