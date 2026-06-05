# Gemini Model Variant Matrix

`gemini_model_variant_matrix.py` builds a metadata-only review matrix for Gemini models behind NewAPI or another OpenAI-compatible gateway.

## Endpoints

```http
GET /api/v1/aihub/models/gemini-variant-matrix
POST /api/v1/aihub/models/gemini-variant-matrix
```

`GET` returns the catalog-based matrix. `POST` accepts optional sanitized `observed_models` so maintainers can review gateway model IDs without calling the gateway:

```json
{
  "observed_models": ["models/gemini-2.5-flash-lite", "google/gemini-3.2-flash-lite"]
}
```

## What It Proves

- Flash-Lite catalog models are the only high-frequency defaults.
- Flash text models are balanced retry or review models after cheap precheck.
- Pro and preview variants require explicit exception handling.
- Image variants stay on explicit media routes.
- Gateway-prefixed IDs such as `models/...`, `google/...`, and `google:...` normalize for review.
- Unknown Gemini-like IDs are explicit-only until catalog review confirms cost, family, stability, and default suitability.

## What It Returns

- `summary`: catalog model count, family count, high-frequency default count, explicit-only count, preview count, unpriced count, observed model review count, catalog-review count, and cheap-first default model.
- `family_rows`: Gemini family posture and allowed default use.
- `model_rows`: model ID, family, catalog status, cost tier, route role, pricing status, configured roles, supported request shapes, and review note.
- `observed_model_reviews`: sanitized model-ID review rows for optional submitted observed model names.
- `prefix_compatibility` and `unknown_model_policy`.
- `privacy_boundary` and `validation_commands`.

## Safety

The matrix does not call Gemini, NewAPI, OpenAI, or the gateway. It does not echo raw payloads, prompts, legal text, model output, credentials, emails, or client documents. It stores and returns model IDs, families, costs, route roles, and review statuses only.

## Validation

```bash
python -m pytest tests/test_gemini_model_variant_matrix.py -q
python -m pytest tests/test_model_catalog.py tests/test_gemini_newapi_cheap_first_policy.py tests/test_gemini_newapi_model_selector.py -q
npm run typecheck
```

## Related Files

- `app/backend/services/gemini_model_variant_matrix.py`
- `app/backend/tests/test_gemini_model_variant_matrix.py`
- `app/backend/routers/aihub.py`
- `app/backend/services/model_ops_readiness.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
