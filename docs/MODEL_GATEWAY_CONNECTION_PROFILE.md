# Model Gateway Connection Profile

`model-gateway-connection-profile` is metadata-only evidence for OpenAI-compatible NewAPI/Gemini gateway setup.

It normalizes remote bare gateway hosts such as `https://yibuapi.com` to `https://yibuapi.com/v1` before the runtime OpenAI-compatible client is initialized. Existing OpenAI-compatible paths such as `/v1`, `/v1beta/openai`, and `/openai` are preserved.

## Scope

- Reports whether `APP_AI_BASE_URL` or a supplied channel URL is configured.
- Reports whether API key material is present using `{{APP_AI_KEY}}` only.
- Shows the normalized runtime base URL shape.
- Flags credential-bearing URLs and remote public HTTP URLs.
- Summarizes cheap-first role readiness for configured Gemini defaults.
- Feeds `/api/v1/aihub/models` and `/model-ops`.

## Safety Boundary

The profile never calls NewAPI, Gemini, OpenAI, Google, a gateway, app AI endpoints, or the network. It does not write `.env`, deployment configuration, default models, or traffic routing. It does not return API keys, Authorization headers, request bodies, response bodies, prompts, raw payloads, legal text, model outputs, gateway responses, emails, or user identifiers.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_gateway_connection_profile.py tests/test_model_gateway_health_plan.py tests/test_aihub_runtime_routing.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
