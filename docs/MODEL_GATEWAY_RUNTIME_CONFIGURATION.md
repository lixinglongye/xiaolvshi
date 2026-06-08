# Model Gateway Runtime Configuration

`model-gateway-runtime-configuration` is metadata-only evidence for the
OpenAI-compatible runtime gateway setup used by AIHub model calls.

It verifies:

- `APP_AI_BASE_URL` is present and normalized through the same
  OpenAI-compatible URL rule used by the runtime boundary.
- Remote bare hosts such as `https://yibuapi.com` resolve to
  `https://yibuapi.com/v1`.
- `APP_AI_KEY` is represented only as `{{APP_AI_KEY}}` or `not_configured`.
- High-frequency roles stay on stable cheap-first Gemini defaults such as
  `gemini-2.5-flash-lite`.
- Live validation should run in order: list models, cheap JSON probe, then
  small legal fixture smoke tests.

The service does not call NewAPI, Gemini, OpenAI, Google, yibuapi, gateways,
app AI endpoints, models, or the network. It does not write `.env`, source
configuration, default routes, traffic weights, probe results, or account
state. It does not return API keys, Authorization headers, request bodies,
response bodies, prompts, raw legal text, model outputs, gateway responses,
credentials, emails, or user identifiers.

API:

```http
GET /api/v1/aihub/models/gateway-runtime-configuration
POST /api/v1/aihub/models/gateway-runtime-configuration
```

Validation:

```powershell
cd app/backend
python -m pytest tests/test_model_gateway_runtime_configuration.py tests/test_model_gateway_connection_profile.py tests/test_model_gateway_health_plan.py -q
```
