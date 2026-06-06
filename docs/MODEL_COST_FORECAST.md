# Model Cost Forecast

The project now has a deterministic model cost forecast for Gemini/OpenAI-compatible routing.

## Purpose

Cheap-first routing needs visible budget evidence. The forecast estimates monthly model spend for representative legal workflow stages and compares:

- cheap-first cascade cost,
- premium-only baseline cost,
- estimated savings ratio,
- estimated savings amount.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `cost_forecast` next to `budget_policy`, `capability_matrix`, `escalation_policy`, `models`, and `usage`.

## Forecast Profiles

Current profiles cover:

- preflight, routing, and light extraction,
- material classification,
- OCR and extraction assist,
- balanced legal review,
- large PDF and final review.

Each profile defines:

- monthly units,
- prompt tokens per unit,
- completion tokens per unit,
- expected escalation rate,
- initial model,
- escalation model,
- premium baseline model.

## Method

```text
cheap_first_monthly =
  monthly_units * initial_unit_cost
  + monthly_units * expected_escalation_rate * escalation_unit_cost

premium_baseline_monthly =
  monthly_units * premium_baseline_unit_cost
```

Token prices come from `model_catalog.py`. These values follow Google Gemini paid-tier pricing where available, but actual gateway billing can differ.

## Official Price And Status Gate

If official provider or gateway pricing, lifecycle status, or model availability
has not been confirmed, the forecast must keep the model `unpriced` and
`review-only`. Do not hard-code guessed costs, include the model in
cheap-first savings claims, or use it as default-promotion evidence until
source-backed price, status, capability, and gateway evidence are refreshed.

## Safety

The forecast stores only planning assumptions and model metadata. It never stores prompts, user documents, file names, API keys, or user identifiers.

## Related files

- `app/backend/services/model_cost_forecast.py`
- `app/backend/tests/test_model_cost_forecast.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/pages/ModelOpsPage.tsx`
