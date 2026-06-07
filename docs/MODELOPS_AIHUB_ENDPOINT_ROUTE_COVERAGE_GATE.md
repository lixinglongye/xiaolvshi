# ModelOps AIHub Endpoint Route Coverage Gate

This gate inventories AIHub endpoint route wiring without calling models or gateways.

## Endpoint

```http
GET /api/v1/aihub/models/aihub-endpoint-route-coverage-gate
POST /api/v1/aihub/models/aihub-endpoint-route-coverage-gate
```

The gate is also included in:

```http
GET /api/v1/aihub/models
```

as `aihub_endpoint_route_coverage_gate`.

## Scope

The gate covers:

- `POST /api/v1/aihub/gentxt`
- `POST /api/v1/aihub/gentxt` with `stream=true`
- `POST /api/v1/aihub/analyzepdf`
- `POST /api/v1/aihub/genimg`
- `POST /api/v1/aihub/genvideo`
- `POST /api/v1/aihub/genaudio`
- `POST /api/v1/aihub/transcribe`

Each row reports `uses_runtime_router`, `uses_budget_decision`, `records_route_telemetry`, `records_usage`, `returns_route_payloads`, `route_mode`, and `route_gap_reason_codes`.

## Current Findings

Text, streaming text, PDF analysis, and image generation already use runtime routing and route telemetry. Only non-streaming text currently returns full route payload metadata to callers.

Video generation, audio generation, and transcription are marked `legacy_media_unrouted`. They still record usage, but they do not yet use `resolve_runtime_model`, do not emit route telemetry, and do not have explicit media/speech budget tasks.

## Boundary

This is metadata-only evidence. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network. It does not write configuration, shift traffic, or return request bodies, response bodies, headers, prompts, raw payloads, legal text, model outputs, gateway responses, credentials, emails, or user identifiers.

The gate does not claim that legacy media routes are fixed or that default routes changed. It only exposes the route coverage status and the next migration actions.

## Validation

```bash
python -m pytest tests/test_model_ops_aihub_endpoint_route_coverage_gate.py tests/test_model_ops_readiness.py -q
python -m pytest tests/test_aihub_runtime_routing.py tests/test_model_ops_gemini_cheap_first_route_preflight.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
