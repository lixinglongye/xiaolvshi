# ModelOps Cheap-First Escalation Budget

`model_ops_cheap_first_escalation_budget.py` adds a metadata-only budget gate for
cheap-first Gemini/NewAPI cascades.

## Endpoint

```http
GET /api/v1/aihub/models/cheap-first-escalation-budget
POST /api/v1/aihub/models/cheap-first-escalation-budget
```

The full `/api/v1/aihub/models` payload also includes
`cheap_first_escalation_budget`. `model_ops_readiness` treats it as a required
cost signal, and `cheap_first_release_decision` consumes it before allowing
default promotion.

## What It Checks

- primary failure rate
- verification and escalation rates
- premium escalation rate
- premium escalation operator-review coverage
- wasted escalation cost ratio
- escalation success rate
- minimum aggregate observation volume

The default GET route uses tiny built-in aggregate observations. The POST route
accepts maintainer-supplied aggregate counts only.

## Accepted Aggregate Shape

```json
{
  "observations": [
    {
      "task": "fast",
      "phase": "local_fixture",
      "request_count": 100,
      "primary_failure_count": 2,
      "verification_count": 3,
      "escalation_count": 2,
      "successful_after_escalation_count": 2,
      "premium_escalation_count": 0,
      "operator_review_count": 0,
      "primary_cost_usd": 0.01,
      "verification_cost_usd": 0.003,
      "escalation_cost_usd": 0.004,
      "premium_cost_usd": 0
    }
  ]
}
```

## Non-Claims

This does not execute retries, call Gemini, NewAPI, OpenAI, Google, or any
gateway, shift traffic, write `.env`, or prove production legal accuracy. It is
release evidence for whether cheap-first cascades are staying within reviewable
cost and premium-exception boundaries.

## Privacy Boundary

The service rejects sensitive field names and secret-like values without echoing
them. It must not return prompts, messages, raw legal text, document text,
headers, request bodies, response bodies, raw model output, emails, phone
numbers, identity numbers, API keys, or credentials.

## Research Anchors

- FrugalGPT motivates using cheaper LLMs first and escalating only when a
  cascade justifies additional cost: <https://arxiv.org/abs/2305.05176>
- Recent routing/cascade surveys emphasize explicit quality estimators and
  cost-performance tradeoffs before sending work to larger models:
  <https://huggingface.co/papers/2410.10347>

## Validation

```bash
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_cheap_first_escalation_budget.py`
- `app/backend/tests/test_model_ops_cheap_first_escalation_budget.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/model_ops_cheap_first_release_decision.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
