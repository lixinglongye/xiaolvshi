# Model Route Telemetry

The project now records aggregate runtime route telemetry for `POST /api/v1/aihub/gentxt`.

## Purpose

Cheap-first routing needs operational evidence. A single response can show why one request used a model, but maintainers also need aggregate counters to see whether the system is actually staying on low-cost routes over time.

Route telemetry records:

- request count by normalized task,
- auto-inferred vs explicit task usage,
- requests downgraded to the recommended model,
- over-budget and operator-review-gated requests,
- allowed over-budget requests,
- unknown-price gateway model usage,
- route success and failure counts.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `route_telemetry` next to:

- `runtime_router`
- `callsite_audit`
- `budget_policy`
- `cost_guardrails`
- `usage`

The frontend `/model-ops` page shows route telemetry summary cards and a per-task telemetry table.

## Safety

Route telemetry stores aggregate routing metadata only. It does not store prompts, uploaded documents, file names, API keys, passwords, emails, user identifiers, or raw model output.

## Related files

- `app/backend/services/model_route_telemetry.py`
- `app/backend/services/aihub.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_route_telemetry.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
