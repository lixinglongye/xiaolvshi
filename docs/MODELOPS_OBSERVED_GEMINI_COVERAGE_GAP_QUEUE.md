# ModelOps Observed Gemini Coverage Gap Queue

## Purpose

`modelops-observed-gemini-coverage-gap-queue` turns sanitized observed Gemini
model ids into maintainer review work before any default model change. It joins
the observed Gemini model intake queue with the local Gemini variant matrix so
reviewers can see:

- Gemini family coverage gaps.
- High-frequency cheap-first task coverage gaps for cheap, fast, OCR, and classification routes.
- Unknown, unpriced, preview, media, and premium/non-cheap routing risk.
- Default-promotion actions that stay review-only until maintainers approve them.

## Endpoint

```http
GET /api/v1/aihub/models/observed-gemini-coverage-gap-queue
POST /api/v1/aihub/models/observed-gemini-coverage-gap-queue
```

The queue is also embedded in the main ModelOps payload as
`observed_gemini_coverage_gap_queue`.

## Safety Boundary

The service is metadata-only. It uses local catalog rows, variant-matrix output,
and sanitized observed model ids. It does not call NewAPI, Gemini, OpenAI,
Google, gateways, or the network; does not write configuration; does not shift
traffic; and does not include raw prompts, payloads, legal text, model outputs,
credentials, or emails.

## Review Semantics

- `blocked`: unknown or unpriced observed Gemini-like models must stay out of
  default promotion until catalog metadata is complete.
- `review_required`: preview, media-only, premium, non-cheap, or missing family
  and task coverage evidence needs maintainer review.
- `ready`: observed family and cheap-first task coverage is ready for release
  review, but still does not change runtime defaults by itself.

## Validation

```bash
cd app/backend
python -m pytest tests/test_model_ops_observed_gemini_coverage_gap_queue.py tests/test_model_ops_observed_gemini_model_intake_queue.py tests/test_gemini_model_variant_matrix.py -q
python -m pytest tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
