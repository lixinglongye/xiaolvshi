# Gemini Model Variant Matrix

`gemini_model_variant_matrix.py` builds a metadata-only review matrix for Gemini models behind NewAPI or another OpenAI-compatible gateway.

## Endpoints

```http
GET /api/v1/aihub/models/gemini-variant-matrix
POST /api/v1/aihub/models/gemini-variant-matrix
```

`GET` returns the catalog-based matrix. `POST` accepts optional sanitized model IDs so maintainers can review gateway model IDs without calling the gateway. It supports the old compact list:

```json
{
  "observed_models": ["models/gemini-2.5-flash-lite", "google/gemini-3.2-flash-lite"]
}
```

It also accepts OpenAI-compatible `/v1/models` style responses copied from a NewAPI or Gemini gateway:

```json
{
  "models_response": {
    "object": "list",
    "data": [
      {"id": "models/gemini-2.5-flash-lite", "object": "model"},
      {"id": "google/gemini-3.2-flash-lite", "object": "model"}
    ]
  }
}
```

Other accepted metadata-only sources are `model_ids`, `gateway_models`, `models`, `gateway_models_response.data`, `model_list.data`, `availableModels`, `result.items`, gateway probe rows, intake queue rows, and top-level `data` arrays.

## What It Proves

- Flash-Lite catalog models are the only high-frequency defaults.
- Flash text models are balanced retry or review models after cheap precheck.
- Pro and preview variants require explicit exception handling.
- Image variants stay on explicit media routes.
- Gateway-prefixed IDs such as `models/...`, `google/...`, and `google:...` normalize for review.
- Unknown Gemini-like IDs are explicit-only until catalog review confirms cost, family, stability, and default suitability.

## What It Returns

- `summary`: catalog model count, family count, high-frequency default count, explicit-only count, preview count, unpriced count, observed model review count, catalog-review count, model-list extraction counts, and cheap-first default model.
- `source_summaries.observed_model_extraction`: shared extractor version, source field names, candidate count, accepted count, dropped count, `rejected_sensitive_count`, `rejected_invalid_count`, `rejected_model_count`, limits, supported model field names, and `raw_payload_echoed: false`.
- `family_rows`: Gemini family posture and allowed default use.
- `model_rows`: model ID, family, catalog status, cost tier, route role, pricing status, configured roles, supported request shapes, and review note.
- `observed_model_reviews`: sanitized model-ID review rows for optional submitted observed model names.
- `prefix_compatibility` and `unknown_model_policy`.
- `privacy_boundary` and `validation_commands`.

## ModelOps Review Form

The ModelOps page includes an observed-model review form for this endpoint. It accepts only a JSON object with model IDs or a model-list response, for example:

```json
{
  "models_response": {
    "data": [
      {"id": "models/gemini-2.5-flash-lite"},
      {"id": "google/gemini-3.2-flash-lite"}
    ]
  }
}
```

The frontend blocks obvious secrets, authorization headers, prompts, emails, raw model output fields, and password-like fields before calling the endpoint. The submitted values are not stored by the UI; the response replaces the current matrix panel so maintainers can inspect catalog-known, catalog-review, and external-model statuses plus extraction source names.

## Safety

The matrix uses the shared Gemini/NewAPI observed-model extractor that is also used by selector, alias capability, alias matrix, and catalog candidate patch-plan evidence. The extractor separates sensitive rejections from invalid/malformed model metadata, and downstream release gates use the total rejected count for blocking. The matrix does not call Gemini, NewAPI, OpenAI, or the gateway. It does not echo raw payloads, prompts, legal text, model output, credentials, emails, headers, or client documents. It stores and returns model IDs, source field names, counts, families, costs, route roles, and review statuses only.

## Validation

```bash
python -m pytest tests/test_gemini_model_variant_matrix.py -q
python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_gemini_model_variant_matrix.py tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_model_alias_matrix.py tests/test_gemini_newapi_alias_capability_coverage.py tests/test_model_catalog_candidate_patch_plan.py -q
python -m pytest tests/test_model_catalog.py tests/test_gemini_newapi_cheap_first_policy.py tests/test_gemini_newapi_model_selector.py -q
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/gemini_model_variant_matrix.py`
- `app/backend/services/gemini_newapi_observed_model_extraction.py`
- `app/backend/tests/test_gemini_model_variant_matrix.py`
- `app/backend/tests/test_gemini_newapi_observed_model_extraction.py`
- `app/backend/routers/aihub.py`
- `app/backend/services/model_ops_readiness.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
