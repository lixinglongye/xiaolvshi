# Model Cost Guardrails

The project now has deterministic model cost guardrails for Gemini/OpenAI-compatible routing.

## Purpose

Forecasts are useful, but maintainers also need live operational checks. Cost guardrails combine:

- in-process aggregate model usage,
- model cost forecast,
- budget thresholds,
- premium request ratio,
- model failure rate,
- unknown-price model count.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `cost_guardrails` next to:

- `usage`
- `cost_forecast`
- `budget_policy`
- `capability_matrix`
- `escalation_policy`
- `fallback_chains`
- `routing_replay`

## Checks

- `actual-cost-budget`: estimated usage cost compared with monthly budget.
- `model-failure-rate`: high failures can cause retries, escalation, and unpredictable cost.
- `premium-request-ratio`: premium models should remain exceptions.
- `unpriced-models`: unknown-price gateway models should not become defaults.
- `cheap-first-savings`: cheap-first forecast should preserve material savings versus premium-only baseline.

## Default Thresholds

- Monthly budget: `$100`
- Budget warning: `70%`
- Budget failure: `100%`
- Failure warning: `8%`
- Failure failure: `20%`
- Premium request warning: `20%`
- Premium request failure: `40%`
- Unknown-price model warning: `1`
- Unknown-price model failure: `3`

## Safety

Guardrails use only aggregate metadata. They do not store prompts, document text, file names, API keys, emails, or user identifiers.

## Related files

- `app/backend/services/model_cost_guardrails.py`
- `app/backend/tests/test_model_cost_guardrails.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/pages/ModelOpsPage.tsx`
