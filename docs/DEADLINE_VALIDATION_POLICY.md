# Deadline Validation Policy

This module adds a deterministic, low-resource policy for checking case and legal deadline metadata before reminders or lawyer review tasks are created.

## Scope

The service lives in `app/backend/services/deadline_validation_policy.py` and is intentionally local-only:

- no network calls
- no model calls
- no environment variable reads
- no secret handling
- fixed default reference date: `2026-06-04`
- fixed example dates for template output and tests

It evaluates metadata for common legal date families:

- case dates
- service and delivery dates
- evidence submission deadlines
- appeal deadlines
- contract performance deadlines
- filing deadlines
- limitation period deadlines

## Service Contract

Use `DeadlineValidationPolicyService().build_policy(deadlines, reference_date="2026-06-04")`.

The returned payload contains:

- `status`
- `summary`
- `checks`
- `risk_bands`
- `recommended_actions`
- `privacy_note`
- `validation_commands`

Accepted date fields include:

- `due_date`
- `deadline_date`
- `service_date`
- `served_at`
- `evidence_due_date`
- `appeal_due_date`
- `contract_performance_date`
- `case_date`
- `event_date`

Dates must be ISO date strings in `YYYY-MM-DD` form. Invalid or missing dates are treated as `missing_date` and require verification.

## Risk Bands

| Band | Days until due | Reminder | Lawyer review |
| --- | ---: | --- | --- |
| `overdue` | `< 0` | yes | yes |
| `urgent` | `0..3` | yes | yes |
| `near` | `4..7` | yes | no by default |
| `watch` | `8..14` | no | no by default |
| `clear` | `> 14` | no | no by default |
| `missing_date` | missing or invalid | no | yes |

Appeal deadlines and limitation period deadlines always require lawyer review because they are high-consequence date types.

## Recommended Actions

The policy emits action identifiers that downstream routes can map to case tasks:

- `collect-controlling-date`
- `lawyer-date-review`
- `same-day-escalation`
- `preservation-review`
- `case-team-reminder`
- `timeline-watch-checkpoint`
- `standard-calendar-monitoring`
- `derive-dependent-deadlines`

Service dates also emit `derive-dependent-deadlines` so answer, evidence, appeal, and review checkpoints can be computed only after the service date is verified.

## Privacy Rules

The service should receive identifiers, deadline types, and dates instead of case narratives. Output redacts common credential, email, password, and secret markers from identifiers and labels. Reminder payloads should avoid raw client narratives, full document text, private contact routes, credentials, and attorney work product.

## Low-Resource Validation

Run only the focused tests:

```bash
cd app/backend
python -m pytest tests/test_deadline_validation_policy.py -q
```

Optional whitespace check from the repository root:

```bash
git diff --check -- app/backend/services/deadline_validation_policy.py app/backend/tests/test_deadline_validation_policy.py docs/DEADLINE_VALIDATION_POLICY.md
```
