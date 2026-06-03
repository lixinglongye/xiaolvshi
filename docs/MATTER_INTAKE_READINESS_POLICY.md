# Matter Intake Readiness Policy

This module defines a local product policy for deciding whether a matter can be
created from intake metadata. It is intended for the small lawyer product before
an internal matter file, drafting flow, or client delivery workflow is opened.

## Scope

The policy evaluates five gates:

- Basic matter profile: client identity reference, opposing party reference,
  matter type, jurisdiction, and requested objective.
- Facts and deadlines: fact summary, key dates, deadline assessment, and
  evidence inventory.
- Conflict screening: search completion, controlled conflict result, and
  waiver or reviewer metadata for potential conflicts.
- Engagement materials: identity material reference, authorization material
  reference, and engagement scope acknowledgement.
- Lawyer review gate: high-risk, urgent, delivery-requested, or conflict
  matters require reviewer assignment; pending review allows only restricted
  creation.

## Status Semantics

- `pass`: all creation gates are satisfied.
- `warn`: no blocking defect remains, but the matter should be opened only as
  restricted intake until lawyer review or deadline ownership is complete.
- `fail`: at least one blocking gate is missing or unresolved, so matter
  creation should remain blocked.

## Output Contract

`MatterIntakeReadinessPolicyService.evaluate()` returns:

- `status`
- `summary`
- `checks`
- `recommended_actions`
- `privacy_note`
- `validation_commands`

The method is pure local Python. It performs no network calls, reads no
environment variables, and uses no credentials.

## Privacy

The service only returns field-presence decisions, counts, controlled statuses,
and generic action labels. It does not echo party names, matter narratives,
document text, contact details, login credentials, API keys, or attachment
contents. Unknown input fields are ignored in the output.

## Low Resource Validation

Run from `app/backend`:

```bash
python -m pytest tests/test_matter_intake_readiness_policy.py -q
```
