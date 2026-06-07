# Runtime Explicit Model Fit Gate

This gate reviews explicit model requests before they become release evidence.
It runs sanitized task/model scenarios through the local runtime router and
reports whether each route is ready, locally enforced, review-required, or
blocked.

## Purpose

- Surfaces unknown gateway model pass-through before maintainers rely on it.
- Shows explicit over-budget exceptions separately from default routing.
- Confirms high-frequency tasks either stay cheap-first or are locally
  downgraded to the task recommendation.
- Links runtime scenarios to the observed gateway model fit matrix when
  sanitized inventory evidence is available.
- Keeps the evidence low-resource and local-only.

## Endpoint

```http
GET /api/v1/aihub/models/runtime-explicit-model-fit-gate
POST /api/v1/aihub/models/runtime-explicit-model-fit-gate
```

`GET /api/v1/aihub/models` also includes the result as
`runtime_explicit_model_fit_gate`.

## Boundaries

The gate does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network. It does not write configuration, change
runtime behavior, change defaults, shift traffic, validate account inventory,
or return request bodies, response bodies, headers, messages, prompts, raw
payloads, legal text, model outputs, gateway responses, credentials, emails, or
user identifiers.

## Validation

```bash
python -m pytest tests/test_model_ops_runtime_explicit_model_fit_gate.py tests/test_model_runtime_router.py tests/test_aihub_runtime_routing.py tests/test_model_ops_readiness.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_runtime_explicit_model_fit_gate.py`
- `app/backend/tests/test_model_ops_runtime_explicit_model_fit_gate.py`
- `app/backend/services/model_runtime_router.py`
- `app/backend/services/model_budget.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
