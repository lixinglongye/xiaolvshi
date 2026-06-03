# Legal Fixture Model Matrix

The legal fixture model matrix shows fixture-level Gemini/NewAPI candidate ladders for cheap-first benchmark runs.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-model-matrix
```

The endpoint returns model metadata only. It does not call NewAPI, Gemini, OpenAI-compatible gateways, or the app AI hub.

## What It Contains

- `cheap_first`: the serial fixture-run-plan starting model.
- `task_recommended`: the capability-matrix model for the fixture task.
- `fallback` and `premium_exception`: task fallback-chain candidates.
- `capability_candidate`: additional catalog candidates for manual fixture experiments.
- per-fixture checks for cheap-first availability, local pricing, and premium review boundaries.

## Policy

- Every fixture starts from the cheap-first candidate.
- Premium models are fixture-scoped escalation candidates, not global defaults.
- Unknown gateway-specific model names are allowed but reported as warnings until pricing and capability are mapped locally.
- PDF fixtures can keep premium exception candidates because they are explicit long-document tasks.

## Related Files

- `app/backend/services/legal_fixture_model_matrix.py`
- `app/backend/services/model_capability_matrix.py`
- `app/backend/services/model_fallback_chains.py`
- `app/backend/tests/test_legal_fixture_model_matrix.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
