# ModelOps Gemini Official Cheap-First Source Review

`model_ops_gemini_official_cheap_first_source_review.py` adds metadata-only
evidence for the cheapest Gemini text defaults. It compares local catalog
pricing for Gemini 2.5 Flash-Lite, Flash, and Pro, joins the existing Gemini
catalog source audit, and blocks default-promotion claims when source reviews
are stale or high-frequency tasks drift away from Flash-Lite.

## Endpoint

```http
GET /api/v1/aihub/models/gemini-official-cheap-first-source-review
```

The aggregate ModelOps payload also includes
`gemini_official_cheap_first_source_review`, and `model_ops_readiness` treats it
as a required configuration signal.

## Official Source Anchors

- Gemini models: `https://ai.google.dev/gemini-api/docs/models`
- Gemini pricing: `https://ai.google.dev/gemini-api/docs/pricing`

These links are review anchors only. The evidence does not scrape live prices or
claim that local catalog prices are current after the recorded review window.

## What It Tracks

- Local catalog rows for `gemini-2.5-flash-lite`, `gemini-2.5-flash`, and
  `gemini-2.5-pro`.
- Input and output price ratios against Flash-Lite so reviewers can see why
  Flash-Lite stays the cheapest high-frequency default.
- Task defaults for cheap, fast, classification, OCR, review, agentic, and
  grounded-research routes.
- Source freshness and default-promotion blockers from the catalog source audit.
- Explicit privacy and claim boundaries for no network calls, no gateway calls,
  no configuration writes, no pricing-accuracy claim, and no automatic default
  change claim.

## Non-Claims

This evidence does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network. It does not write configuration, change
defaults, shift traffic, validate account inventory, prove pricing accuracy, or
claim automatic default changes.

It also does not return API keys, Authorization headers, request bodies,
response bodies, prompts, raw payloads, raw legal text, model outputs, emails,
credentials, or user identifiers.

## Validation

```bash
python -m pytest tests/test_model_ops_gemini_official_cheap_first_source_review.py tests/test_model_catalog_source_audit.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_gemini_official_cheap_first_source_review.py`
- `app/backend/tests/test_model_ops_gemini_official_cheap_first_source_review.py`
- `app/backend/services/model_catalog_source_audit.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
