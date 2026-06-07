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

Each row reports `uses_runtime_router`, `uses_budget_decision`,
`records_route_telemetry`, `records_usage`, `returns_route_payloads`,
`returns_task_inference`, `returns_usage_units`, `route_mode`, and
`route_gap_reason_codes`.

## Current Findings

Text, streaming text, PDF analysis, image generation, video generation, audio
generation, and transcription use runtime routing and route telemetry.
Non-streaming text, PDF analysis, image generation, video generation, audio
generation, and transcription currently return route payload metadata to
callers. Image, video, audio, and transcription responses also expose sanitized
usage units for cost review without returning prompts, PDF bytes, image bytes,
audio, transcripts, output URLs, request bodies, response bodies, headers,
model outputs, or credentials.

Video generation, audio generation, and transcription now use explicit media/speech budget tasks. Their default gateway model ids remain `model_not_in_local_catalog` review items until pricing, lifecycle, and gateway behavior are documented.

## Boundary

This is metadata-only evidence. It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network. It does not write configuration, shift traffic, or return request bodies, response bodies, headers, prompts, raw payloads, legal text, model outputs, gateway responses, credentials, emails, or user identifiers.

The gate does not claim that default routes changed or that media/speech
defaults are price-benchmarked. It exposes route coverage status, remaining
stream metadata gaps, usage-unit coverage, and local catalog review items.

## Validation

```bash
python -m pytest tests/test_model_ops_aihub_endpoint_route_coverage_gate.py tests/test_model_ops_readiness.py -q
python -m pytest tests/test_aihub_runtime_routing.py tests/test_model_ops_gemini_cheap_first_route_preflight.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
