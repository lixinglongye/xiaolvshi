# Model Callsite Audit

The project now has a static audit for service-layer `GenTxtRequest` call sites.

## Purpose

Runtime task inference is useful, but critical legal workflows should still declare their intended task explicitly. This audit prevents future backend changes from adding AIHub text calls that rely only on automatic inference.

## What It Checks

The audit scans `app/backend/services` with Python AST and records:

- file and line number of every `GenTxtRequest(...)`
- enclosing function name
- whether `task=...` is present
- whether `model=...` is present
- pass/fail status and recommended action

The current policy requires every service-layer `GenTxtRequest` to include explicit `task` metadata.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `callsite_audit` next to:

- `runtime_router`
- `budget_policy`
- `capability_matrix`
- `fallback_chains`
- `routing_replay`
- `usage`

The frontend `/model-ops` page shows callsite coverage, missing task count, explicit model count, failures, and the audited callsite table.

## Safety

The audit reads source structure only. It does not read runtime prompts, uploaded documents, API keys, passwords, environment variables, model responses, user emails, or identifiers.

## Related files

- `app/backend/services/model_callsite_audit.py`
- `app/backend/tests/test_model_callsite_audit.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
