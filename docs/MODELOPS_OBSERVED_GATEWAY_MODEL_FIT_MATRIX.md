# ModelOps Observed Gateway Model Fit Matrix

`modelops-observed-gateway-model-fit-matrix` is metadata-only evidence for matching sanitized OpenAI-compatible gateway model IDs to local Gemini/NewAPI task policy.

## Endpoint

```http
GET /api/v1/aihub/models/observed-gateway-model-fit-matrix
POST /api/v1/aihub/models/observed-gateway-model-fit-matrix
```

The matrix is also included in:

```http
GET /api/v1/aihub/models
```

as `observed_gateway_model_fit_matrix`.

## Scope

- Extracts sanitized model IDs from gateway-style `/models` payload shapes.
- Maps each observed model to canonical Gemini catalog metadata when known.
- Scores every task policy for `cheap_fit`, `balanced_fit`, `premium_exception_fit`, `media_fit`, `review_only`, or `missing`.
- Surfaces the cheapest observed default-eligible candidate per task.
- Marks Pro, preview, media, unknown, external, and unpriced candidates as explicit review unless policy allows them.
- Provides a UI bridge between Gemini route preflight, alias capability coverage, and AIHub endpoint route coverage.

## Boundary

This evidence never calls NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network. It does not validate real account inventory, write configuration, change defaults, shift traffic, or return API keys, Authorization headers, request bodies, response bodies, prompts, raw payloads, legal text, model outputs, gateway responses, emails, or user identifiers.

The matrix does not claim that a live gateway was queried. It only scores sanitized model IDs already provided by local metadata paths or by a maintainer-submitted payload.

## Validation

```bash
cd app/backend
python -m pytest tests/test_modelops_observed_gateway_model_fit_matrix.py tests/test_model_ops_readiness.py -q
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/modelops_observed_gateway_model_fit_matrix.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/maintenance_evidence.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_modelops_observed_gateway_model_fit_matrix.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
