# Model Route Legal Benchmark Risk Queue

This slice adds a metadata-only maintainer queue for reviewing cheap-first
Gemini/NewAPI routing against legal benchmark and user-need evidence.

## Purpose

The queue joins three existing local evidence sources:

- cheap-first Gemini/NewAPI calibration rows
- legal benchmark research refresh mappings
- user-need benchmark coverage rows

It helps reviewers decide whether a model route can stay cheap-first, needs a
balanced precheck, or must remain an explicit premium/operator exception.

## Endpoint

- `GET /api/v1/maintenance/model-route-legal-benchmark-risk-queue`

The endpoint returns:

- `queue_rows`: task-level risk rows for route review
- `user_need_rows`: user-need aggregation across route rows
- `routing_policy`: cheap-first default and escalation boundaries
- `privacy_boundary`: metadata-only output constraints
- `claim_boundary`: claims that remain forbidden
- `validation_commands`: local pytest commands for review

## Boundaries

This evidence does not:

- call NewAPI, Gemini, or any gateway
- write model defaults or shift traffic
- download public benchmark datasets
- import public benchmark samples
- claim public benchmark scores or leaderboard rank
- store raw legal text, prompts, gateway payloads, model output, emails, or credentials

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_model_route_legal_benchmark_risk_queue.py tests/test_gemini_newapi_cheap_first_calibration.py tests/test_user_need_benchmark_coverage.py tests/test_legal_benchmark_research_refresh.py -q
```

Frontend evidence is covered by:

```powershell
npm run typecheck
npm run ui:regression
```
