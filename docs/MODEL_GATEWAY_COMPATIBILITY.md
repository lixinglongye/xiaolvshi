# Model Gateway Compatibility

`model_gateway_compatibility.py` checks whether NewAPI/OpenAI-compatible model names still resolve to local Gemini cost and capability metadata.

## Why It Exists

Gateways may expose the same Gemini model under different names, for example:

- `gemini-2.5-flash-lite`
- `models/gemini-2.5-flash-lite`
- `google/gemini-2.5-flash-lite`
- `openrouter/google/gemini-2.5-flash-lite`

The runtime still sends the requested gateway model name to the gateway, but local budgeting needs a canonical model id so cost tiers, capabilities, and configured roles remain accurate.

## What It Reports

`GET /api/v1/aihub/models` returns `gateway_compatibility` with:

- configured model roles and their env vars,
- canonical Gemini model ids when recognized,
- whether a name is gateway-prefixed,
- whether the model is known, Gemini-like, or non-Gemini,
- blocking checks for non-Gemini defaults or over-budget known models,
- warnings for unknown Gemini names that need catalog pricing.

The frontend `/model-ops` page shows the same report with role rows and gateway prefix examples.

Use [MODEL_GATEWAY_HEALTH_PLAN.md](MODEL_GATEWAY_HEALTH_PLAN.md) before live gateway probes. It checks base URL shape, secret presence, placeholder dry-run contracts, and cheap-first probe models without calling the gateway.

## Release Check

Run:

```bash
cd app/backend
python -m pytest tests/test_model_gateway_compatibility.py tests/test_model_catalog.py -q
```

A `fail` status means a configured default is not Gemini-compatible or exceeds its role cost ceiling. A `warn` status means the model can pass through the gateway but needs catalog metadata before it should become a default.

## Safety

This check never calls the gateway and never reads API keys, prompts, documents, file names, users, emails, or raw model output. It only evaluates configured model names and public catalog metadata.
