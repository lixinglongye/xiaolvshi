# Model Gateway Request Compatibility Gate

## Purpose

The gateway request compatibility gate verifies OpenAI-compatible Gemini request shapes before maintainers promote cheap-first defaults. It combines:

- Task default models from the local catalog.
- Gateway model-name compatibility and canonical Gemini IDs.
- `temperature`, `max_tokens`, and `response_format` policy.
- Gemini `reasoning_effort` policy.
- Cheap-first cost-tier boundaries for high-volume routes.

This is metadata-only release evidence. It never sends a request to NewAPI, Gemini, OpenAI, Google, yibuapi, or any gateway.

## Endpoints

- `GET /api/v1/aihub/models/gateway-request-compatibility-gate`
- `POST /api/v1/aihub/models/gateway-request-compatibility-gate`

Example POST payload:

```json
{
  "tasks": [
    {
      "task": "fast",
      "model": "gemini-2.5-flash-lite",
      "response_format": { "type": "json_object" },
      "reasoning_effort": "auto"
    }
  ]
}
```

The POST endpoint accepts sanitized task/model metadata only. It rejects raw request fields such as headers, messages, prompts, payloads, raw legal text, generated text, model output, emails, or credentials.

## Gate Rules

High-frequency routes (`fast`, `ocr`, `classification`) must stay on Gemini-compatible low-cost defaults with bounded request parameters:

- Temperature must remain within the task policy ceiling.
- `max_tokens` must remain within the high-frequency ceiling.
- `reasoning_effort` must avoid elevated thinking modes.
- Unknown or unpriced Gemini-like gateway IDs stay blocked until catalog metadata exists.
- JSON response format must keep a low deterministic temperature.

Review and PDF routes can use larger budgets, but the gate still reports the request shape and claim boundary.

## Boundaries

The gate returns only task IDs, sanitized model IDs, canonical model IDs, cost tiers, parameter caps, reasoning policy decisions, status labels, and release actions.

It explicitly does not return:

- Headers, request bodies, prompts, messages, payloads, or credentials.
- Raw legal text, user documents, emails, or phone numbers.
- Raw model output or generated text.
- Live gateway execution, model quality, pricing accuracy, production compatibility, or automatic default-change claims.

## Validation

Run the focused backend gate:

```bash
cd app/backend
python -m pytest tests/test_model_gateway_request_compatibility_gate.py tests/test_model_request_policy.py tests/test_model_reasoning_policy.py tests/test_model_gateway_compatibility.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q
```

Run the frontend contract checks:

```bash
cd app/frontend
npm run typecheck
npm run ui:regression
```

The release readiness check is `model-gateway-request-compatibility-gate`.
