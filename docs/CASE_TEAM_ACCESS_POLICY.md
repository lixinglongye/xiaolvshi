# Case Team Access Policy

## Purpose

The case collaboration surface needs clear backend rules before adding richer team workflows. `CaseTeamAccessPolicyService.build_policy()` returns a deterministic policy payload that can be exposed by a maintenance route or reused by case authorization checks.

The policy covers:

- Role matrix for `owner`, `lawyer`, `paralegal`, `reviewer`, and `client`.
- Sensitive operations that require audit records and, where needed, explicit approval.
- Least-privilege defaults for new team members and client-facing access.
- Privacy and law-firm compliance notes for privilege boundaries, retention, and review history.
- Low-resource validation commands that run without model calls or case data.

## Runtime API Status

```http
GET /api/v1/maintenance/case-team-access-policy
GET /api/v1/entities/cases/{case_id}/permissions
```

The maintenance endpoint returns `CaseTeamAccessPolicyService().build_policy()`. The first runtime binding is `GET /api/v1/entities/cases/{case_id}/permissions`, backed by `CaseAccessControlService` and the role permission matrix. The CaseDetail UI consumes this summary to show the actor role and disable write/review/export controls that are denied or approval-gated.

Future endpoints should add persisted membership records, approval workflow state, and audit event storage:

```http
POST /api/v1/cases/{case_id}/team/access/evaluate
GET /api/v1/cases/{case_id}/team/access/audit
```

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
python -m pytest tests/test_case_access_control.py tests/test_case_permission_runtime_router.py tests/test_case_role_permission_matrix.py tests/test_case_team_access_policy.py -q
cd ../frontend && npm run typecheck
```

Before exposing the policy through a public route, also run the repository's standard credential scanner.

## Related Files

- `app/backend/services/case_team_access_policy.py`
- `app/backend/services/case_access_control.py`
- `app/backend/routers/cases.py`
- `app/backend/tests/test_case_access_control.py`
- `app/backend/tests/test_case_permission_runtime_router.py`
- `app/frontend/src/lib/caseApi.ts`
- `app/frontend/src/pages/CaseDetailPage.tsx`
- `app/backend/tests/test_case_team_access_policy.py`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
- `docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md`
