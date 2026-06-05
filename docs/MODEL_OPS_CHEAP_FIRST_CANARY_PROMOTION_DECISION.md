# ModelOps Cheap-First Canary Promotion Decision

`cheap_first_canary_promotion_decision` turns the cheap-first canary plan and
aggregate canary observation review into a maintainer-facing decision packet.
It answers whether each canary step is eligible for next-batch review, should be
held, should roll back or keep the previous default, or should only continue
monitoring the current default.

## Purpose

The packet gives reviewers a single place to inspect:

- source canary step status
- matched aggregate observation statuses
- advance, hold, rollback, monitor-only, and not-ready counts
- reason codes for each decision row
- no-write and no-traffic-shift boundaries
- recommended maintainer actions

It is intentionally metadata-only. It never writes `.env` files, updates runtime
configuration, calls a model gateway, persists rollout state, or shifts traffic.

## Endpoints

```http
GET /api/v1/aihub/models/cheap-first-canary-promotion-decision
```

The full `/api/v1/aihub/models` payload includes
`cheap_first_canary_promotion_decision`.

Posting sanitized observations to
`/api/v1/aihub/models/cheap-first-canary-observation` returns the observation
review plus `data.promotion_decision` so the `/model-ops` page can refresh the
decision immediately after a reviewer evaluates aggregate counts.

## Decision Statuses

- `advance_next_batch`: all matched rows for a ready step passed threshold
  checks. A maintainer may review the next batch manually.
- `hold_for_review`: observations are missing, warning-level, or otherwise need
  human review before movement.
- `rollback_required`: an observation failed rollback-trigger thresholds or the
  submitted observation payload was rejected.
- `monitor_only`: the step represents an already-aligned current default.
- `not_ready`: the source plan or canary step is blocked or still requires
  review.

Every item keeps `configuration_change_allowed` and `traffic_shift_allowed`
false. The packet also sets `requires_maintainer_approval` true.

## Non-Claims

This decision does not:

- approve automatic canary rollout
- write configuration
- call NewAPI, Gemini, OpenAI, Google, or another gateway
- shift production traffic
- persist canary state
- prove public benchmark scores
- prove production legal accuracy

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_canary_promotion_decision.py tests/test_model_ops_cheap_first_canary_observation.py tests/test_model_ops_cheap_first_canary_plan.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

Related files:

- `app/backend/services/model_ops_cheap_first_canary_promotion_decision.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_promotion_decision.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_OBSERVATION.md`
