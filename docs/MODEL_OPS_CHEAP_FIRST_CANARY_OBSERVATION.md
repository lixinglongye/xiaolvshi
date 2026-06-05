# ModelOps Cheap-First Canary Observation Review

`cheap_first_canary_observation` evaluates aggregate canary metrics against the
cheap-first canary plan. It is a reviewer-facing packet for deciding whether a
staged rollout can continue, must pause, or should roll back.

## Purpose

The review accepts sanitized counts only:

- request count
- failure count
- over-budget route count
- premium or unknown-price route count
- operator-review route count
- canary step id, task, and phase

It compares those counts with the canary thresholds from the plan and returns
pass, review-required, fail, or not-supplied. It does not need prompts, headers,
gateway responses, legal text, model output, or user data.

`cheap_first_canary_promotion_decision` consumes this review downstream. The
POST response includes `data.promotion_decision` so reviewers can see whether
the submitted aggregate observations produce advance, hold, rollback, or
monitor-only decisions without changing configuration or traffic.

## Endpoints

```http
GET /api/v1/aihub/models/cheap-first-canary-observation
POST /api/v1/aihub/models/cheap-first-canary-observation
```

The full `/api/v1/aihub/models` payload also includes the default
`cheap_first_canary_observation` packet with status `not_supplied`.

## Example Payload

```json
{
  "observations": [
    {
      "step_id": "monitor_existing_default-fast",
      "task": "fast",
      "phase": "monitor_existing_default",
      "request_count": 25,
      "failure_count": 0,
      "over_budget_count": 0,
      "premium_request_count": 0,
      "unknown_price_model_count": 0,
      "operator_review_count": 1
    }
  ]
}
```

The evaluator rejects forbidden field names and secret-like values without
echoing them back. Forbidden examples include API keys, authorization headers,
prompts, raw model output, raw gateway responses, legal text, and emails.

## Thresholds

- failure rate must be at most 2%
- over-budget route ratio must be at most 1%
- premium or unknown-price route ratio must be at most 5%
- operator-review route ratio must be at most 10%
- each observation should include at least 20 requests before it is treated as
  strong evidence

## Non-Claims

This review does not:

- write `.env` or runtime configuration
- call NewAPI, Gemini, OpenAI, Google, or another gateway
- shift production traffic
- persist canary observations
- approve automatic canary rollout
- prove public benchmark scores
- prove production legal accuracy

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_canary_observation.py tests/test_model_ops_cheap_first_canary_plan.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

Related files:

- `app/backend/services/model_ops_cheap_first_canary_observation.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_observation.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_PROMOTION_DECISION.md`
