# Model Catalog Source Audit

`model_catalog_source_audit.py` adds metadata-only release evidence for the local Gemini model catalog.

## Endpoint

```http
GET /api/v1/aihub/models/catalog-source-audit
```

The full ModelOps payload also includes `catalog_source_audit`, and `model_ops_readiness` treats it as a required configuration signal.

## What It Proves

- Each local Gemini catalog row links back to an official Google Gemini source URL.
- Fast, classification, and OCR defaults remain on stable Flash-Lite catalog models.
- Preview, Pro, premium, or unpriced models cannot silently become high-frequency defaults.
- Missing pricing metadata stays visible as a watchlist instead of being treated as production-ready cost evidence.
- The audit is local and does not call Gemini, NewAPI, OpenAI, Google, or any gateway.

## Source References

- Gemini pricing: `https://ai.google.dev/gemini-api/docs/pricing`
- Gemini models: `https://ai.google.dev/gemini-api/docs/models`

These links are source-review anchors. They do not prove the local catalog is current by themselves; maintainers still need to refresh catalog fields when provider or gateway metadata changes.

## What It Returns

- `summary`: catalog size, official source coverage, pricing coverage, stable/preview counts, cheap-first default alignment, and check counts.
- `source_references`: official pricing and model-list review anchors.
- `high_frequency_defaults`: fast/classification/OCR defaults and their canonical catalog IDs.
- `catalog_rows`: model ID, status, cost tier, pricing status, source URL status, configured roles, and review note.
- `checks`: source URL, cheap-first default, preview/default, pricing watchlist, and catalog-shape checks.
- `privacy_boundary`: confirms no network call, credentials, prompts, legal text, raw model output, or raw payload echo.

## Validation

```bash
python -m pytest tests/test_model_catalog_source_audit.py tests/test_model_catalog.py tests/test_model_ops_readiness.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_catalog_source_audit.py`
- `app/backend/tests/test_model_catalog_source_audit.py`
- `app/backend/services/model_catalog.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
