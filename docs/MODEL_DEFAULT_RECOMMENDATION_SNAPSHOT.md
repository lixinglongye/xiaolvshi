# Model Default Recommendation Snapshot

This service summarizes whether current Gemini/NewAPI defaults still follow the cheap-first policy.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `default_recommendation_snapshot` next to the existing model catalog, runtime router, default optimization, and cost guardrails.

## What It Checks

- High-volume defaults (`cheap`, `fast`, `classification`, and `ocr`) should use stable lowest-tier Gemini models.
- Review defaults should use a low-cost capable review model.
- PDF and final-review paths may use premium models, but they require operator review.
- Recommended models are derived through `model_default_candidate_selector.py`, so a future stable, lower-cost Flash-Lite catalog row can appear as a recommended change without editing runtime defaults.
- If the current default is allowed but no longer the cheapest capable recommendation, the row becomes `warn` rather than silently passing.
- Gateway-prefixed model IDs such as `models/gemini-2.5-flash-lite`, `google/gemini-2.5-flash-lite`, and `openrouter/google/gemini-2.5-flash-lite` map back to the local catalog.
- Unknown Gemini-like NewAPI model names are treated as catalog-review warnings until pricing, lifecycle, and capability metadata are added.

The snapshot must not treat the entire selector ladder as a default promotion
list. Only `default_eligible` candidates can be shown as recommended default
changes. Preview, unpriced, unknown/catalog-review, deprecated,
premium-over-budget, premium-exception-only, and operator-review-required rows
remain `review-only` even when they appear in fallback, verification, premium,
or context positions in the ladder.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_model_default_recommendation_snapshot.py tests/test_model_default_candidate_selector.py -q
python -m pytest tests/test_model_catalog.py tests/test_model_default_optimization.py -q
```

## Safety Policy

The snapshot stores model names, roles, cost tiers, and capability metadata only. It never stores API keys, prompts, uploaded documents, raw gateway responses, user identifiers, or contact details.

## Related Files

- `app/backend/services/model_default_recommendation_snapshot.py`
- `app/backend/services/model_default_candidate_selector.py`
- `app/backend/tests/test_model_default_recommendation_snapshot.py`
- `app/backend/tests/test_model_default_candidate_selector.py`
