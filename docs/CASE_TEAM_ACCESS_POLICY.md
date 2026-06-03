# Case Team Access Policy

## Purpose

The case collaboration surface needs clear backend rules before adding richer team workflows. `CaseTeamAccessPolicyService.build_policy()` returns a deterministic policy payload that can be exposed by a maintenance route or reused by future case authorization checks.

The policy covers:

- Role matrix for `owner`, `lawyer`, `paralegal`, `reviewer`, and `client`.
- Sensitive operations that require audit records and, where needed, explicit approval.
- Least-privilege defaults for new team members and client-facing access.
- Privacy and law-firm compliance notes for privilege boundaries, retention, and review history.
- Low-resource validation commands that run without model calls or case data.

## Future API Suggestions

```http
GET /api/v1/maintenance/case-team-access-policy
POST /api/v1/cases/{case_id}/team/access/evaluate
GET /api/v1/cases/{case_id}/team/access/audit
```

The first endpoint can directly return `CaseTeamAccessPolicyService().build_policy()`. The later case endpoints should evaluate a concrete actor, role, case scope, and operation against persisted membership records.

## Product Rules

- Default posture is deny-by-default until a member is assigned to a case and role.
- Client access is limited to explicitly shared deliverables and fact requests.
- Internal notes, draft work product, model prompts, and review traces stay internal unless a lawyer or owner deliberately shares a final deliverable.
- External sharing, full exports, destructive material changes, and role changes must produce audit records.
- Denied sensitive-operation attempts should also be retained for supervision and incident review.

## Validation

Run from `app/backend`:

```bash
python -m pytest tests/test_case_team_access_policy.py -q
```

Before exposing the policy through a public route, also run the repository's standard credential scanner.

## Related Files

- `app/backend/services/case_team_access_policy.py`
- `app/backend/tests/test_case_team_access_policy.py`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
