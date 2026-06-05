# ModelOps Performance Budget

`model_ops_performance_budget.py` builds a metadata-only guard for the heavy ModelOps payload and frontend loading behavior.

## Endpoint

```http
GET /api/v1/aihub/models/performance-budget
POST /api/v1/aihub/models/performance-budget
```

The full ModelOps payload also includes `model_ops_performance_budget` and the aggregate `model_ops_readiness` checks it as a required signal.

## What It Proves

- The heavyweight `/api/v1/aihub/models` payload has a short backend cache.
- The frontend tries same-origin `fetch` before SDK fallback so local browser loads do not wait for SDK timeouts.
- The frontend ModelOps API helper has a single wall-clock timeout and abort path.
- A fetch timeout does not continue into a second SDK timeout window.
- The ModelOps page reuses the cheap-first calibration embedded in `/models` instead of fetching it twice on first load.
- Optional timing observations can be reviewed against first-load and cache-hit budgets without storing raw payloads.
- Repeated slow timing observations fail the performance budget instead of remaining a soft warning.

## What It Returns

- `summary`: first-load budget, cache-hit budget, frontend request timeout, total wall-clock timeout, backend cache TTL, same-origin fetch-first status, timeout-fallback status, duplicate-fetch status, observation counts, and check counts.
- `checks`: timeout, backend cache, same-origin fetch-first, single wall-clock timeout, duplicate calibration fetch, AbortController, and optional observed timing checks.
- `observations`: sanitized numeric timing rows only when explicitly supplied to the service.
- `privacy_boundary`: confirms raw payloads, credentials, prompts, legal text, raw model output, and URLs are excluded.
- `validation_commands`: backend and frontend checks that protect this signal.

## Frontend Guard

`modelOpsApi.ts` uses same-origin `fetch` first for local `/api/v1/aihub/*` calls, guarded by `MODEL_OPS_TOTAL_TIMEOUT_MS` and `AbortController`. If the fetch path times out, the helper raises that timeout directly instead of waiting for SDK fallback. The SDK path remains as a fallback for non-timeout environments and is wrapped in the same timeout race.

## Observation Review

`POST /api/v1/aihub/models/performance-budget` accepts:

```json
{
  "observations": [
    { "metric": "model-ops-first-load", "duration_ms": 1800, "budget_ms": 2500 },
    { "metric": "model-ops-cache-hit", "duration_ms": 420, "budget_ms": 750 }
  ]
}
```

Only numeric rows are retained. Metrics that look like secrets, emails, keys, headers, prompts, URLs, raw legal text, or raw model output are redacted or dropped. One or two slow rows warn; three or more slow rows fail the budget.

## Safety

This service does not call Gemini, NewAPI, OpenAI, or any gateway. It does not store prompts, documents, file names, users, emails, credentials, URLs, raw payloads, raw gateway responses, or model output.

## Validation

```bash
python -m pytest tests/test_model_ops_performance_budget.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_performance_budget.py`
- `app/backend/tests/test_model_ops_performance_budget.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
