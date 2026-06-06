# Case Role Permission Matrix

## Purpose

`CaseRolePermissionMatrixService` defines a pure local matter/case permission matrix. The matrix itself is deterministic metadata only and does not inspect case files. It is now also consumed by the first runtime gate in `CaseAccessControlService`, which protects the `cases` API with ownership/team-role checks while keeping responses privacy-safe.

The matrix covers owner/lawyer/reviewer/assistant/client/admin roles across these operations:

- `read`
- `write`
- `export`
- `share`
- `billing`
- `audit`
- `review`

Each role-operation cell returns one of:

- `allow`
- `deny`
- `requires_approval`

## Privacy-Safe API Payload

Use `CaseRolePermissionMatrixService().build_privacy_safe_api_payload()` to return:

- `policy_id`, `status`, `roles`, `operations`, and `decision_values`.
- A compact `matrix` keyed by role and operation.
- Full `permissions` entries with role, operation, decision, scope, audit requirement, approval gate, and rationale.
- `role_summaries` derived from the matrix.
- `forbidden_combinations` for denied role-operation pairs.
- `approval_gates` for operations that need explicit approval.
- `validation_commands`.

The payload intentionally excludes case narratives, document text, direct contact details, payment card data, and secret tokens. Denials use policy reasons instead of private matter details.

## Role Summary

- `owner`: can read, write, bill, audit, and review the full case workspace; export and share require explicit confirmation.
- `lawyer`: can read, write, audit, and review assigned cases; export and share require approval; billing controls are denied.
- `reviewer`: can read review packets, inspect review-relevant audit metadata, and make review decisions; write, export, share, and billing are denied.
- `assistant`: can read assigned materials; write is draft-only until lawyer or owner approval; export, share, billing, audit, and review are denied.
- `client`: can read explicitly shared items; fact submissions require lawyer approval before becoming case records; export, share, billing, audit, and review are denied.
- `admin`: can access billing support metadata and privacy-safe audit metadata; case content read requires break-glass approval; write, export, share, and legal review are denied.

## Forbidden Combinations

`forbidden_combinations` is generated from every `deny` cell in the matrix. Important examples:

- `client + export`: no full workspace or internal work-product export.
- `client + audit`: audit logs can expose internal supervision and privileged workflow metadata.
- `assistant + share`: assistants cannot create client or external disclosure channels.
- `assistant + review`: assistants cannot approve legal review outcomes.
- `reviewer + share`: reviewers do not control disclosure boundaries.
- `lawyer + billing`: legal work assignment does not grant billing ownership.
- `admin + export`: administrative support must not become a path to case exports.
- `admin + review`: admins are not legal reviewers or case counsel.

Every forbidden entry includes a safe alternative such as requesting owner-approved export, lawyer-supervised write approval, a privacy-safe audit summary, or routing billing to the owner or billing admin.

## Validation

Run from `app/backend`:

```bash
python -m pytest tests/test_case_role_permission_matrix.py -q
python -m compileall services/case_role_permission_matrix.py tests/test_case_role_permission_matrix.py
```

The tests verify required role and operation coverage, the three allowed decision values, role summaries, forbidden combinations, approval gates, privacy-safe payload shape, and these validation commands.

## Runtime Binding

`CaseAccessControlService` uses this matrix to evaluate `read` and `write` access for `GET/PUT/DELETE /api/v1/entities/cases...` routes and to expose `GET /api/v1/entities/cases/{id}/permissions`. The CaseDetail UI consumes that endpoint to surface the current role and disable denied or approval-gated actions before the backend rejects them.

Run from `app/backend`:

```bash
python -m pytest tests/test_case_access_control.py tests/test_case_permission_runtime_router.py tests/test_case_role_permission_matrix.py tests/test_case_team_access_policy.py -q
cd ../frontend && npm run typecheck
```

The current runtime bridge reads existing `cases.user_id` and `cases.team_members` metadata. Durable membership rows, persisted approval workflow state, and access audit event storage remain follow-up work.

## Related Files

- `app/backend/services/case_role_permission_matrix.py`
- `app/backend/services/case_access_control.py`
- `app/backend/routers/cases.py`
- `app/backend/tests/test_case_access_control.py`
- `app/backend/tests/test_case_permission_runtime_router.py`
- `app/frontend/src/lib/caseApi.ts`
- `app/frontend/src/pages/CaseDetailPage.tsx`
- `app/backend/tests/test_case_role_permission_matrix.py`
- `docs/CASE_ROLE_PERMISSION_MATRIX.md`
- `docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md`
