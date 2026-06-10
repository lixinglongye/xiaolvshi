# ModelOps Gemini Official Lifecycle Drift Gate

`model_ops_gemini_official_lifecycle_drift_gate.py` adds metadata-only evidence
for checking Gemini lifecycle drift before any cheap-first default promotion.
It sits between the official cheap-first source review and the official model
family roadmap.

## Endpoint

```http
GET /api/v1/aihub/models/gemini-official-lifecycle-drift-gate
POST /api/v1/aihub/models/gemini-official-lifecycle-drift-gate
```

The aggregate ModelOps payload also includes
`gemini_official_lifecycle_drift_gate`, and `model_ops_readiness` treats it as
a required configuration signal.

## Official Source Anchors

- Gemini models: `https://ai.google.dev/gemini-api/docs/models`
- Gemini pricing: `https://ai.google.dev/gemini-api/docs/pricing`
- Gemini OpenAI compatibility: `https://ai.google.dev/gemini-api/docs/openai`

These links are review anchors only. The gate does not claim live source
refresh, live gateway execution, or full Gemini coverage.

## What It Tracks

- High-frequency text defaults: `cheap`, `fast`, `classification`, and `ocr`
  must remain on stable `gemini-2.5-flash-lite`.
- Newer agentic and grounded-research defaults can remain visible as
  review-only Gemini/NewAPI candidates until lifecycle, pricing, and gateway
  support are refreshed.
- Preview, deprecated, shutdown, and retired lifecycle labels block default
  use.
- Gateway-observed Gemini aliases are treated as review-only until
  canonicalized against official model and pricing sources.
- Local catalog lifecycle drift is visible when a catalog row marks a
  review-only or preview model as stable.

## What It Returns

- `official_source_rows`: official source anchors and tracked signals.
- `default_task_rows`: task default, canonical model, lifecycle, default
  policy, Flash-Lite alignment, review flag, blocked flag, and action.
- `lifecycle_rows`: tracked model id, local catalog status, configured roles,
  lifecycle label, default policy, drift status, and required action.
- `checks`: source link, high-frequency default, blocked lifecycle default,
  review default, catalog drift, catalog coverage, and gateway-boundary checks.
- `privacy_boundary` and `claim_boundary`: explicit no-call, no-write,
  no-secret, no-payload, no-live-execution, and no-all-supported boundaries.

## Non-Claims

This evidence does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network. It does not write configuration, change
defaults, shift traffic, prove pricing accuracy, prove production quality,
claim live gateway execution, or claim that all Gemini models are supported.

It also does not return API keys, Authorization headers, request bodies,
response bodies, prompts, raw payloads, raw legal text, model outputs, emails,
identifiers, or credentials.

## Validation

```bash
python -m pytest tests/test_model_ops_gemini_official_lifecycle_drift_gate.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_gemini_official_lifecycle_drift_gate.py`
- `app/backend/tests/test_model_ops_gemini_official_lifecycle_drift_gate.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
