# Model Route Quality Budget

`model_route_quality_budget.py` adds a metadata-only quality budget for cheap-first Gemini/NewAPI routing.

## Endpoint

```http
GET /api/v1/aihub/models/route-quality-budget
```

The full ModelOps payload also includes `route_quality_budget`, and `model_ops_readiness` checks it as a required routing signal.

## What It Proves

- Every catalog-backed task has deterministic quality gates before escalation.
- Text tasks expose the catalog-derived, task-capable recommendation as the cheap-start model.
- A future stable, lower-cost Flash-Lite catalog row can become the cheap-start model in review metadata without editing runtime defaults or `.env` templates.
- Runtime defaults that do not expose a task's required capabilities are flagged for maintainer review.
- Premium and media routes remain explicit exceptions instead of silent cheap-first defaults.

## What It Returns

- `summary`: task counts, cheap-start counts, premium exception counts, runtime default gaps, quality gate counts, and check counts.
- `task_quality_budgets`: per-task recommended model, runtime default, cheap-start model, quality score, quality gates, and review action.
- `checks`: candidate presence, quality-gate presence, cheap-start-before-premium, runtime capability review, and quality score floor review.
- `privacy_boundary`: confirms credentials, prompts, raw legal text, raw model output, and emails are excluded.

## Non-Claims

This is not a live benchmark score and does not call Gemini, NewAPI, OpenAI, or any gateway. It does not claim production legal accuracy. It only makes the cheap-first routing assumptions reviewable before spending on model calls.

## Research Anchors

- LegalBench frames legal reasoning as multiple task types rather than one generic score, so this budget keeps task-specific quality gates instead of a single global threshold: <https://arxiv.org/abs/2308.11462>
- FrugalGPT motivates routing through cheaper models first and escalating only when a cascade or score justifies extra cost, which is the policy reflected by `cheap_start_model`, `quality_floor`, and `review_action`: <https://arxiv.org/abs/2305.05176>

## Validation

```bash
python -m pytest tests/test_model_route_quality_budget.py tests/test_model_ops_readiness.py tests/test_model_default_candidate_selector.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_route_quality_budget.py`
- `app/backend/tests/test_model_route_quality_budget.py`
- `app/backend/services/model_default_candidate_selector.py`
- `app/backend/tests/test_model_default_candidate_selector.py`
- `app/backend/services/model_capability_matrix.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
