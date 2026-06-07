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
- Gemini 3 Flash Preview can be catalog-known and token-priced while still
  staying review-only because its lifecycle is preview.
- Gemini 3.5 Flash is tracked as an unpriced premium-posture Flash variant, not
  a cheap-first candidate.
- Missing pricing metadata stays visible as a watchlist instead of being treated as production-ready cost evidence.
- Official Gemini pricing/model-list source reviews must remain fresh before a default-promotion proposal is allowed.
- Stale source reviews create default-promotion source blocks until the official pricing/model source review is refreshed.
- The audit is local and does not call Gemini, NewAPI, OpenAI, Google, or any gateway.

## Source References

- Gemini pricing: `https://ai.google.dev/gemini-api/docs/pricing`
- Gemini models: `https://ai.google.dev/gemini-api/docs/models`

These links are source-review anchors. They do not prove the local catalog is current by themselves; maintainers still need to refresh catalog fields when provider or gateway metadata changes.

The audit also returns `source_review_records` with `last_reviewed_on`,
`review_age_days`, `max_review_age_days`, `freshness_status`,
`default_promotion_allowed`, and `review_scope`. The current snapshot anchors
the source review to `source_review_snapshot_as_of`; maintainers should refresh
that review whenever provider pricing, model lifecycle, or gateway availability
changes before moving a model into cheap-first defaults.

## Official Price And Status Gate

When official provider or gateway pricing, lifecycle status, or model
availability has not been confirmed, the catalog row must remain `unpriced` and
`review-only`. Maintainers must not hard-code a cost, count the model in
cheap-first savings, or promote it into default routes until source-backed
price, status, capability, and gateway evidence are refreshed.

## What It Returns

- `summary`: catalog size, official source coverage, pricing coverage, stable/preview counts, cheap-first default alignment, source freshness counts, default-promotion source blocks, and check counts.
- `source_references`: official pricing and model-list review anchors.
- `source_review_records`: official source freshness, review scope, and default-promotion allowance.
- `high_frequency_defaults`: fast/classification/OCR defaults and their canonical catalog IDs.
- `catalog_rows`: model ID, status, cost tier, pricing status, source URL status, configured roles, and review note.
- `checks`: source URL, source freshness, cheap-first default, preview/default, pricing watchlist, and catalog-shape checks.
- `privacy_boundary`: confirms no network call, credentials, prompts, legal text, raw model output, or raw payload echo.

## Validation

```bash
python -m pytest tests/test_model_catalog_source_audit.py tests/test_model_catalog.py tests/test_model_ops_readiness.py -q
python -m compileall services/model_catalog_source_audit.py tests/test_model_catalog_source_audit.py
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
