# Model Route Telemetry

The project now records aggregate runtime route telemetry for `POST /api/v1/aihub/gentxt`
and writes sanitized route-decision events to a local telemetry repository.

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

The local `route_telemetry_repository` stores only allowed metadata fields after
the persistence plan passes. It rejects prompts, raw legal text, client contact
details, credentials, headers, request bodies, response bodies, and raw model
outputs, then rebuilds daily task/model aggregate counters.

`route_telemetry_ops_summary` reads those sanitized daily counters and turns
them into release-review checks for route failures, over-budget pressure,
operator-review load, premium model drift, unknown models, and cheap-first
downgrade evidence.

`route_telemetry_triage` converts the operations summary checks into prioritized
maintainer actions so cheap-first drift is visible as a queue rather than just
aggregate ratios.

`route_telemetry_remediation` maps triage actions to reviewed cheap-first
repair steps and optional `.env` suggestions without writing configuration or
calling gateways.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `route_telemetry`, `route_telemetry_repository`,
`route_telemetry_ops_summary`, `route_telemetry_triage`, and
`route_telemetry_remediation` next to:

- `runtime_router`
- `route_guardrails`
- `callsite_audit`
- `budget_policy`
- `cost_guardrails`
- `usage`

The frontend `/model-ops` page shows route telemetry summary cards, a per-task
telemetry table, local repository daily buckets, route telemetry operations
summary checks, route telemetry triage actions, and route guardrail
pass/warn/fail checks. The page also shows remediation steps and env
suggestions when telemetry drift needs operator review.

`route_guardrails` uses the same aggregate telemetry snapshot to evaluate route failure rate, over-budget ratio, downgrade ratio, operator-review ratio, unknown-price models, and allowed over-budget requests. Empty telemetry is treated as no data rather than a release blocker.

## Safety

Route telemetry stores aggregate routing metadata only. The local repository
stores sanitized event fields and aggregate counters only. Neither surface
stores prompts, uploaded documents, file names, API keys, passwords, emails,
user identifiers, request bodies, response bodies, or raw model output.

## Related files

- `app/backend/services/model_route_telemetry.py`
- `app/backend/services/route_telemetry_repository.py`
- `app/backend/services/route_telemetry_ops_summary.py`
- `app/backend/services/route_telemetry_triage_queue.py`
- `app/backend/services/route_telemetry_remediation_plan.py`
- `app/backend/services/model_route_guardrails.py`
- `app/backend/services/aihub.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_route_telemetry.py`
- `app/backend/tests/test_route_telemetry_repository.py`
- `app/backend/tests/test_route_telemetry_ops_summary.py`
- `app/backend/tests/test_route_telemetry_triage_queue.py`
- `app/backend/tests/test_route_telemetry_remediation_plan.py`
- `app/backend/tests/test_model_route_guardrails.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
