# Model Gateway Health Plan

`model_gateway_health_plan.py` builds a safe preflight plan for NewAPI, Gemini OpenAI-compatible endpoints, and similar gateways. It does not call the gateway.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `gateway_health_plan` next to gateway compatibility, lifecycle policy, model-ops readiness, cost guardrails, and route telemetry.

## What It Checks

- `APP_AI_BASE_URL` is configured.
- `APP_AI_KEY` is present without returning the value, hash, or fingerprint.
- Remote gateway URLs use HTTPS.
- The base URL includes an OpenAI-compatible `/v1` path.
- Cheap, fast, OCR, and classification roles stay on known low-cost Gemini models.
- Dry-run contracts use `{{APP_AI_BASE_URL}}` and `{{APP_AI_KEY}}` placeholders only.

## Dry-Run Contracts

The plan returns two maintainer-run probes:

- `GET {{APP_AI_BASE_URL}}/models`
- `POST {{APP_AI_BASE_URL}}/chat/completions` with the cheapest configured model and a tiny JSON response budget.

These requests are examples only. The backend does not send them automatically.

## Validation

```bash
python -m pytest tests/test_model_gateway_health_plan.py tests/test_model_gateway_compatibility.py tests/test_model_ops_readiness.py -q
```

## Safety

The service reads configuration presence, base URL shape, model IDs, cost tiers, and public documentation links. It never emits API keys, key fingerprints, user prompts, uploaded documents, emails, passwords, or raw model output.

## Related Files

- `app/backend/services/model_gateway_health_plan.py`
- `app/backend/tests/test_model_gateway_health_plan.py`
- `app/backend/routers/aihub.py`
- `app/backend/services/model_ops_readiness.py`
- `docs/MODEL_GATEWAY_COMPATIBILITY.md`
- `docs/MODEL_LIFECYCLE_POLICY.md`
