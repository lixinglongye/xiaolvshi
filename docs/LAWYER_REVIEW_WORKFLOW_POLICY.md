# Lawyer Review Workflow Policy

This policy records the product workflow required before AI generated legal work can reach a client-facing delivery surface.

## Service

`LawyerReviewWorkflowPolicyService.build_policy(payload=None)` returns a dictionary with:

- `state_enumeration`: `draft`, `lawyer_review`, `approved`, `rejected`, `revise_required`, and `client_deliverable`.
- `allowed_state_transitions`: the only valid transitions through the review workflow.
- `forbidden_state_transitions`: explicit guardrails, including the ban on `draft -> client_deliverable`.
- `blocking_conditions`: deterministic blockers for a proposed transition payload.
- `role_requirements`: roles allowed to submit, approve, reject, request revision, or release client-facing output.
- `audit_log_requirements`: fields required for transition and release audit events.
- `low_resource_validation_commands`: quick local checks that do not require a large model or heavy data.
- `privacy_notes`: rules for keeping review metadata separate from raw client facts and evidence text.

## Workflow

The expected path for AI generated output is:

1. `draft`
2. `lawyer_review`
3. `approved` or `rejected` or `revise_required`
4. `client_deliverable`, only from `approved`

`revise_required` returns the artifact to `draft` after a revision is created. `rejected` and `client_deliverable` are terminal states for the reviewed artifact version.

## Product Guardrails

- A draft cannot be delivered to a client directly.
- A reviewed artifact cannot be delivered until it is explicitly approved.
- Approval and client delivery require the `lawyer` or `owner` role.
- Rejection and revision requests must include a `reason` field.
- Every transition must record actor, role, artifact, source status, target status, and timestamp metadata in the audit layer.
- Client-facing release must record the release channel and the earlier approval time.

## Suggested Future API

- `GET /api/v1/maintenance/lawyer-review-workflow-policy`
- `POST /api/v1/review-workflow/transition-check`

The current implementation is intentionally a service-only policy so it can be tested and reviewed without modifying shared routers.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_lawyer_review_workflow_policy.py -q
python -m compileall services/lawyer_review_workflow_policy.py
```

## Related Files

- `app/backend/services/lawyer_review_workflow_policy.py`
- `app/backend/tests/test_lawyer_review_workflow_policy.py`
