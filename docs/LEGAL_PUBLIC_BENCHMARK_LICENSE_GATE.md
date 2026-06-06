# Legal Public Benchmark License Gate

## Purpose

The license gate keeps public legal benchmark work in a maintainer-review state before any external samples enter local tests or release evidence. It joins three existing metadata sources:

- `LegalPublicBenchmarkSamplerService`: source ids, public URLs, resource profile, sample caps, and sampler state.
- `UserNeedBenchmarkCoverageService`: which user needs each public source could support.
- `ModelRouteLegalBenchmarkRiskQueueService`: which cheap-first legal route reviews reference the same public source ids.

The gate is designed for laptop-safe review. It does not download datasets, import public benchmark text, call models, call gateways, write configuration, or claim public benchmark scores.

## Endpoints

- `GET /api/v1/maintenance/legal-review-benchmark/public-license-gate`
- `POST /api/v1/maintenance/legal-review-benchmark/public-license-gate`

The optional POST body supports explicit source-level review states:

```json
{
  "license_reviews": {
    "legalbench": "approved",
    "cuad": "approved"
  }
}
```

Approved source rows can move from `block_public_sample_import` to `allow_capped_metadata_sampling` only when the sampler marks the source as `sampling_ready` and the configured review state is one of `approved`, `pass`, or `ok`.

## Review Policy

Every source row reports required checks for:

- License terms review.
- Attribution plan.
- Privacy review.
- Sample cap review.
- Storage policy review.
- Local fixture mapping.
- Route risk review.

Corpus-scale sources remain `catalog_only` until a separate resource-controlled and license-reviewed job exists.

## Boundaries

The service returns only source ids, titles, URLs, task labels, user-need ids, route task ids, review states, checklist states, and next actions.

It explicitly does not return:

- Public benchmark text or dataset samples.
- Raw legal text or fixture snippets.
- Prompts, model output, gateway payloads, or credentials.
- Public benchmark score or leaderboard claims.
- Legal/license compliance guarantees without maintainer review.

## Validation

Run the focused backend tests:

```bash
cd app/backend
python -m pytest tests/test_legal_public_benchmark_license_gate.py tests/test_legal_public_benchmark_sampler.py tests/test_user_need_benchmark_coverage.py tests/test_model_route_legal_benchmark_risk_queue.py tests/test_frontend_ui_regression_gate.py -q
```

Run the frontend contract checks:

```bash
cd app/frontend
npm run typecheck
npm run ui:regression
```

The release readiness entry `legal-public-benchmark-license-gate` records this validation set for maintainer review.
