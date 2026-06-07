# Model Route Telemetry

The project now records aggregate runtime route telemetry for `POST /api/v1/aihub/gentxt`,
`POST /api/v1/aihub/analyzepdf`, and `POST /api/v1/aihub/genimg`, then writes sanitized
route-decision events to a local telemetry repository.

## Purpose

Cheap-first routing needs operational evidence. A single response can show why one request used a model, but maintainers also need aggregate counters to see whether the system is actually staying on low-cost routes over time.

Route telemetry records:

- request count by normalized task,
- auto-inferred vs explicit task usage,
- requests downgraded to the recommended model,
- over-budget and operator-review-gated requests,
- allowed over-budget requests,
- estimated route cost from local catalog token pricing,
- unknown gateway model usage,
- known catalog model usage without token pricing,
- allowlisted route reason-code counts,
- route success and failure counts.

Text, PDF, and image route decisions all use the same telemetry shape. PDF and
image responses stay unchanged; operators inspect their routing evidence through
model-ops snapshots and the local repository aggregates.

Image generation `model=auto` decisions are recorded after resolving to the
configured image task default, so telemetry can prove image calls stayed on the
Gemini image route instead of drifting to a text model.

For known Gemini/NewAPI catalog model routes, the repository estimates
`estimated_cost_usd` from recorded token counts and the local model catalog's
token pricing metadata. Unknown gateway model ids are not cost-estimated:
their `estimated_cost_usd` remains `0`, and they stay visible in the unknown
model review path. Known catalog models that are missing token pricing are
tracked separately through `unpriced_model_count` so pricing gaps do not look
like unknown gateway traffic.

The local `route_telemetry_repository` stores only allowed metadata fields after
the persistence plan passes. It rejects prompts, raw legal text, client contact
details, credentials, headers, request bodies, response bodies, and raw model
outputs, then rebuilds daily task/model aggregate counters.

Runtime route `reason_codes` are allowlisted policy labels such as
`task_default_selected`, `over_task_budget`, `operator_review_required`,
`routed_to_recommended_model`, `unknown_catalog_model`,
`unknown_gateway_routed_to_recommended`,
`non_stable_model_routed_to_recommended`, allow-gated
`gateway_passthrough`, and `unknown_reason_code`. They are aggregated as
`reason_code_counts` only and cannot carry free text, client identifiers,
prompts, payload fragments, model outputs, or credentials.

`route_telemetry_ops_summary` reads those sanitized daily counters and turns
them into release-review checks for route failures, over-budget pressure,
operator-review load, premium model drift, unknown models, reason-code
hotspots, and cheap-first downgrade evidence.

`route_telemetry_triage` converts the operations summary checks into prioritized
maintainer actions, including bounded reason-code hotspot actions for labels
such as `over_task_budget`, `operator_review_required`,
`unknown_catalog_model`, `unknown_gateway_routed_to_recommended`,
`non_stable_model_routed_to_recommended`, allow-gated
`gateway_passthrough`, and `unknown_reason_code`, so cheap-first drift is
visible as a queue rather than just aggregate ratios.

`route_telemetry_remediation` maps triage actions to reviewed cheap-first
repair steps and optional `.env` suggestions without writing configuration or
calling gateways.

## Official Price And Status Gate

Route telemetry must not infer cost for models whose official provider or
gateway pricing, lifecycle status, or availability is unconfirmed. Those models
remain `unpriced` and `review-only`, with no hard-coded cost, savings credit, or
default-promotion signal until source-backed price, status, capability, and
gateway evidence are refreshed.

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
stores prompts, uploaded documents, PDF bytes, uploaded images, generated image
URLs, revised prompts, file names, API keys, passwords, emails, user identifiers,
request bodies, response bodies, or raw model output.

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
