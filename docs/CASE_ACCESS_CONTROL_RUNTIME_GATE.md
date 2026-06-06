# Case Access Control Runtime Gate

## Purpose

`CaseAccessControlService` turns the existing case role permission matrix into a runtime gate for the `cases` API. The first runtime binding is intentionally narrow and low-risk: it uses existing `cases.user_id` ownership and `cases.team_members` metadata to resolve a privacy-safe actor role, then evaluates `read` and `write` operations through `CaseRolePermissionMatrixService`.

## Runtime Endpoints

```http
GET /api/v1/entities/cases
GET /api/v1/entities/cases/all
GET /api/v1/entities/cases/{id}
GET /api/v1/entities/cases/{id}/permissions
PUT /api/v1/entities/cases/{id}
PUT /api/v1/entities/cases/batch
DELETE /api/v1/entities/cases/{id}
DELETE /api/v1/entities/cases/batch
```

The list routes now filter records through the runtime `read` decision. The previous `/all` route no longer bypasses case access checks. Single-case reads require `read`; update and delete operations require `write`. The permissions endpoint returns a metadata-only summary that frontends can use to disable write, export, review, or share controls.

`CaseDetailPage` now consumes the permissions endpoint, renders the current actor role and operation counts, and disables the primary write, review, and export controls when the runtime decision is denied or approval-gated. Backend enforcement remains authoritative.

## Role Resolution

- `cases.user_id == current_user.id` resolves to `owner`.
- `cases.team_members` may be a JSON array/object or a comma/semicolon/newline string.
- Team member entries can match by user id, email, or display name.
- `paralegal` and `member` normalize to `assistant`; `attorney` and `counsel` normalize to `lawyer`.
- Unknown actors are denied by default.
- Platform `admin` resolves to the matrix `admin` role, which still requires approval for case-content reads.

This is a runtime bridge, not a replacement for a future case membership table. Durable membership records, approval workflow storage, and audit event persistence remain follow-up work.

## Privacy Boundary

Runtime permission responses expose role, operation, decision, approval gate, status, and reason codes only. They must not include raw `team_members`, actor emails, client names, case narratives, document text, prompts, model output, or credentials.

## Validation

Run from `app/backend`:

```bash
python -m pytest tests/test_case_access_control.py tests/test_case_permission_runtime_router.py tests/test_case_role_permission_matrix.py tests/test_case_team_access_policy.py -q
cd ../frontend && npm run typecheck
```

The tests cover owner, lawyer, reviewer, assistant/paralegal, client, platform admin, unknown actors, the `/permissions` endpoint, write denials, approval gates, list filtering, and the `/all` no-bypass behavior.

## Related Files

- `app/backend/services/case_access_control.py`
- `app/backend/routers/cases.py`
- `app/backend/tests/test_case_access_control.py`
- `app/backend/tests/test_case_permission_runtime_router.py`
- `app/frontend/src/lib/caseApi.ts`
- `app/frontend/src/pages/CaseDetailPage.tsx`
- `app/backend/services/case_role_permission_matrix.py`
- `docs/CASE_ROLE_PERMISSION_MATRIX.md`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
