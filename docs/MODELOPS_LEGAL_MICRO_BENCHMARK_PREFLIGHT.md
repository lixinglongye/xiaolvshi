# ModelOps Legal Micro Benchmark Preflight

`modelops-legal-micro-benchmark-preflight` is a low-resource reviewer packet for the smallest cheap-first legal benchmark run.

It combines existing local fixture, document benchmark, fact consistency, and cheap-first gate metadata so a maintainer can run a tiny serial smoke benchmark before promoting or escalating Gemini defaults.

## Endpoints

```http
GET /api/v1/aihub/models/legal-micro-benchmark-preflight
GET /api/v1/maintenance/legal-review-benchmark/micro-benchmark-preflight
```

The maintenance endpoint accepts bounded query parameters:

- `fixture_limit`: 1-4, default 2.
- `document_case_limit`: 1-7, default 2.
- `fact_case_limit`: 1-4, default 1.

## Evidence Shape

The packet returns:

- selected fixture ids and cheap-first model/cost metadata,
- document case ids and expected section/citation/risk-label counts,
- fact-consistency case ids and amount/deadline/fact/conflict counts,
- a serial run sequence with `max_parallel_requests = 1`,
- follow-up maintenance endpoints for normalizing results and running the cheap-first benchmark gate,
- privacy and claim-boundary flags.

## Boundaries

This preflight does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or the network. It does not write configuration, shift traffic, or claim live model quality.

It must not return request bodies, messages, prompt text, fixture excerpts, legal text, generated document text, raw model output, gateway responses, credentials, emails, or client identifiers.

## Validation

```bash
cd app/backend
python -m pytest tests/test_modelops_legal_micro_benchmark_preflight.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/modelops_legal_micro_benchmark_preflight.py`
- `app/backend/tests/test_modelops_legal_micro_benchmark_preflight.py`
- `app/backend/routers/aihub.py`
- `app/backend/routers/maintenance.py`
- `app/backend/services/model_ops_readiness.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
