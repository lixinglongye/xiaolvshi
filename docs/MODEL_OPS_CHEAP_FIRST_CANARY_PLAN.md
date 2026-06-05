# ModelOps Cheap-First Canary Plan

`cheap_first_canary_plan` turns the default-change queue into maintainer-reviewed
rollout steps for cheap-first model default changes.

## Purpose

The plan gives maintainers a staged rollout packet before any runtime default is
edited. It separates:

- queued changes that can enter a canary after validation
- queued changes that still need maintainer review
- queued changes blocked by route or cost guardrails
- already-aligned defaults that only need monitoring

The plan is intentionally metadata-only. It never writes `.env` files, changes
traffic routing, calls a gateway, or starts a canary by itself.

## Endpoint

```http
GET /api/v1/aihub/models/cheap-first-canary-plan
```

The full `/api/v1/aihub/models` payload also includes
`cheap_first_canary_plan`.

## Inputs

The service consumes existing ModelOps metadata only:

- `default_change_queue`
- `cheap_first_release_decision`
- `route_guardrails`
- `cost_guardrails`
- `route_telemetry_ops_summary`

It reads queue item ids, task names, env var names, model ids, status strings,
route/cost guardrail statuses, and reason codes. It does not read credentials,
headers, prompts, legal text, raw gateway responses, or raw model outputs.

## Rollout Shape

Ready queue items produce staged review rows:

- `canary_1_percent`: 1% batch, 99% holdout, 4-hour observation window.
- `canary_10_percent`: 10% batch, 90% holdout, 8-hour observation window.
- `canary_25_percent`: 25% batch, 75% holdout, 12-hour observation window.

Review-required items stay at 0% traffic until a maintainer attaches evidence.
Blocked items stay at 0% traffic until blocking checks pass. No-action items
produce monitor-only rows for the current default.

## Rollback Triggers

The default rollback packet covers:

- route failure rate above 2%
- over-budget route ratio above 1%
- premium or unknown-price route ratio above 5%
- operator-review route ratio above 10%

These are thresholds for reviewer evaluation; they are not proof that a canary
has run.

## Non-Claims

This plan does not:

- write `.env` or runtime configuration
- call NewAPI, Gemini, OpenAI, Google, or another gateway
- shift production traffic
- approve automatic canary rollout
- prove public benchmark scores
- prove production legal accuracy

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_canary_plan.py tests/test_model_ops_default_change_queue.py tests/test_model_ops_cheap_first_release_decision.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

Related files:

- `app/backend/services/model_ops_cheap_first_canary_plan.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_plan.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
