# Route Telemetry Result Archive

The route telemetry result archive is a metadata-only ModelOps evidence packet
for cheap-first routing review. It joins the persisted route telemetry
repository, operations summary, triage queue, and remediation plan into two
reviewable tables:

- daily `archive_rows` for status, counts, cost totals, and reason-code pressure
- task/model `cost_ledger_rows` for priced, unpriced, unknown, and review-only
  cost evidence

It also includes `release_review_rows` that link blocking or warning telemetry
back to maintainer remediation steps.

## Endpoints

```http
GET /api/v1/maintenance/route-telemetry-result-archive
GET /api/v1/aihub/models/route-telemetry-result-archive
GET /api/v1/aihub/models
```

The aggregate AIHub ModelOps payload exposes the result as
`route_telemetry_result_archive`, and `model_ops_readiness` includes the
`route-telemetry-result-archive` component.

The `/model-ops` page renders the archive immediately after the route telemetry
repository panel. It shows archive days, cost ledger rows, release-review rows,
manual-review count, metadata-only status, config-write boundary, gateway-call
boundary, daily archive rows, and task/model cost ledger rows.

## Status Rules

The archive inherits status from the upstream evidence chain:

- `fail` if repository, ops summary, triage, or remediation has blocking items
- `warn` if any upstream component has warnings or review-required status
- `ready` for an empty local repository that is valid but not production proof
- `pass` when route telemetry evidence is within cheap-first review guardrails

Daily rows can still show `cheap_first_review`, `cost_review_required`, or
`review_required` even when the aggregate status is not blocking.

## Privacy Boundary

The archive stores and returns metadata only. It must not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, models, or the network. It must not
write configuration, change default routes, shift traffic, claim production
health, or claim public benchmark scores.

Forbidden fields include raw route events, prompts, messages, legal text,
document text, client contact details, emails, user identifiers, file names,
headers, request bodies, response bodies, raw payloads, gateway responses, raw
model outputs, API keys, bearer tokens, passwords, secrets, and credentials.

Unknown or unpriced gateway models remain review-only and unpriced until source
backed catalog and pricing evidence is refreshed.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_route_telemetry_result_archive.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/route_telemetry_result_archive.py`
- `app/backend/tests/test_route_telemetry_result_archive.py`
- `app/backend/routers/maintenance.py`
- `app/backend/routers/aihub.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
