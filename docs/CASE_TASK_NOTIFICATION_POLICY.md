# Case Task Notification Policy

`CaseTaskNotificationPolicyService` defines the backend policy surface for case task reminders and escalation.
It is intentionally deterministic: callers pass task metadata such as `days_until_due`, `priority`, `status`,
`owner_id`, `owner_role`, and `task_type`; the service does not read the current date.

## Scope

- Task reminders for due-soon case work.
- Urgent escalation when `days_until_due <= 1` or task priority is urgent or critical.
- Blocking owner assignment checks before notification dispatch.
- Client material collection reminders through a controlled client portal path.
- Lawyer review reminders before client-facing delivery or deadline closure.
- Audit requirements for notification and escalation decisions.

## Service Contract

Suggested call:

```python
from services.case_task_notification_policy import CaseTaskNotificationPolicyService

policy = CaseTaskNotificationPolicyService().build_policy(
    [
        {
            "case_id": "case-1",
            "task_id": "task-1",
            "status": "open",
            "priority": "normal",
            "days_until_due": 1,
            "owner_role": "lawyer",
        }
    ]
)
```

The response contains:

- `notification_channels`: metadata for case workspace, client portal, review queue, and team escalation paths.
- `trigger_rules`: due-soon, urgent deadline, missing owner, client material, and lawyer review triggers.
- `escalation_rules`: urgent owner, missing owner, client material, and lawyer review escalation behavior.
- `owner_assignment_requirements`: rules that block notification when accountability is missing.
- `notification_queue`: active tasks with dispatchable reminder triggers.
- `blocking_urgent_tasks`: urgent or blocked tasks requiring assignment or escalation.
- `low_resource_validation_commands`: local checks that do not require model calls, network calls, or large fixtures.
- `privacy_notes`: payload minimization guidance for case task reminders.

## Deterministic Inputs

Use these task fields instead of wall-clock calculations:

- `days_until_due`: integer due window supplied by the caller.
- `priority`: `normal`, `high`, `urgent`, or `critical`.
- `status`: active statuses such as `open`, `in_progress`, `waiting_client`, and `review_needed`; done-like statuses are ignored.
- `owner_id` or `owner_role`: required before task reminders can be dispatched.
- `requires_client_materials` and `requires_lawyer_review`: explicit workflow gates.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_case_task_notification_policy.py -q
```

Repository whitespace check for this change:

```powershell
git diff --check -- app/backend/services/case_task_notification_policy.py app/backend/tests/test_case_task_notification_policy.py docs/CASE_TASK_NOTIFICATION_POLICY.md
```

## Privacy Notes

- Store case and task identifiers, roles, due-window metadata, and policy decisions.
- Do not include raw client narratives, full document text, or private message bodies in reminder payloads.
- Client material reminders should expose only requested material categories and assigned legal owner context.
- Escalation audit records should capture the policy decision and target role set.
