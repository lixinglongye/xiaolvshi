# Case Workbench Payload

`CaseWorkbenchPayloadService` assembles a frontend-ready case workbench skeleton from existing deterministic backend policy services.

Runtime payloads now also include `case-workbench-risk-refresh-plan`, which
derives metadata-only risk/evidence refresh instructions from sanitized section
state and recent event deltas. The plan is attached by
`CaseWorkbenchRuntimeBindingService`; it does not write live risk state, refresh
the evidence graph, or return raw event payloads.

The service is intentionally local-only:

- no router integration
- no database reads
- no release or ledger writes
- no network calls
- no model calls
- no environment variable reads
- no current-date reads

## Source Services

The workbench payload wraps these existing contracts:

- `MatterIntakeReadinessPolicyService`
- `DeadlineValidationPolicyService`
- `CaseTimelineDeadlineRiskService`
- `CaseTaskNotificationPolicyService`
- `CaseEvidenceGraphService`

## Output Shape

Call:

```python
from services.case_workbench_payload import CaseWorkbenchPayloadService

payload = CaseWorkbenchPayloadService().build_payload(
    intake=intake_metadata,
    deadlines=deadline_metadata,
    timeline_events=timeline_metadata,
    tasks=task_metadata,
    evidence_report=review_report_metadata,
    reference_date="2026-06-04",
)
```

The response contains:

- `dashboard`: overall status, section cards, blocker count, action count, and primary blocker/action.
- `sections`: normalized frontend sections for intake, deadline validation, timeline risk, task notifications, and evidence graph.
- `blockers`: blocking items consolidated from all evaluated source services.
- `next_actions`: deterministic reviewer or operator actions sorted by priority and section order.
- `source_contracts`: source service names, input state, status, and local validation commands.
- `validation_commands`: focused local tests and compile check for this payload service.

## Empty State Semantics

Arguments default to `None`. A `None` argument means the section was not supplied and should render as a frontend empty state.

Pass an empty list or empty dict explicitly when the caller wants the underlying source service to evaluate an empty dataset.

## Status Semantics

- `template`: no sections were evaluated.
- `blocked`: at least one blocking item exists.
- `needs_attention`: no blocking item exists, but at least one evaluated section has warnings, reminders, or review flags.
- `ready`: all evaluated sections are clear.

## Privacy Boundary

The service emits IDs, statuses, counts, controlled labels, and reviewer actions only. It sanitizes common credential markers and email-like strings from the final payload. Do not place raw case narratives, full document text, direct contact data, access tokens, or private message bodies into the workbench contract.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_case_workbench_payload.py -q
python -m compileall services/case_workbench_payload.py tests/test_case_workbench_payload.py
```
