# ModelOps NewAPI Channel Bootstrap

This packet is metadata-only setup evidence for a NewAPI-compatible Gemini channel.
It helps maintainers configure a gateway such as `https://yibuapi.com` while keeping
routine routes on cheap-first Gemini defaults.

## Scope

- Normalize a channel URL to an OpenAI-compatible base URL such as `/v1`.
- Represent channel key presence with the `APP_AI_KEY` placeholder only.
- Recommend cheap-first environment defaults for high-frequency legal workflows.
- Join observed Gemini model intake, coverage-gap, and premium exception review summaries.
- Keep Pro, preview, and premium variants explicit-only until maintainer and cost-owner review.
- Expose the same reviewer packet through AIHub ModelOps and maintenance evidence:
  `/api/v1/aihub/models/newapi-channel-bootstrap`,
  `/api/v1/maintenance/gemini/newapi-channel-bootstrap`, `/model-ops`, and `/maintenance`.

## Non-Goals

- No NewAPI, Gemini, OpenAI, Google, yibuapi, gateway, app-AI, model, or network calls.
- No configuration writes, default route changes, or traffic shifts.
- No API keys, Authorization headers, request bodies, response bodies, prompts, raw payloads,
  raw legal text, model outputs, gateway responses, emails, credentials, or user identifiers.
- No claims that the key is valid, the account inventory was read, or pricing/model quality was verified live.

## Local Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_newapi_channel_bootstrap.py -q
python -m pytest tests/test_model_ops_newapi_channel_bootstrap.py tests/test_model_gateway_connection_profile.py tests/test_model_gateway_runtime_configuration.py tests/test_model_ops_observed_gemini_premium_exception_review.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
