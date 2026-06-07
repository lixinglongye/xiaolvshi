# Route Telemetry Triage Queue

The route telemetry triage queue converts persisted route telemetry operations
checks into maintainer actions for cheap-first Gemini/NewAPI routing.

## Purpose

`RouteTelemetryTriageQueueService` consumes `RouteTelemetryOpsSummaryService`
output only. It does not read raw route events. The queue prioritizes:

- route failure investigation,
- over-budget route pressure,
- operator-review route load,
- premium-model drift,
- unknown gateway model cataloging,
- unpriced catalog model pricing gaps,
- route reason-code hotspots,
- daily route telemetry hotspots,
- missing staging telemetry when no route events exist.

Empty telemetry returns `ready` with an informational staging-event action. That
keeps local development unblocked while making clear that production routing
health is still unproven.

## Official Price And Status Gate

Triage items for models with unconfirmed official provider or gateway pricing,
lifecycle status, or availability must keep those models `unpriced` and
`review-only`. The queue must not treat guessed costs as evidence, count those
models in savings claims, or recommend default promotion until source-backed
price, status, capability, and gateway evidence are refreshed.

## Reason-Code Hotspot Actions

The queue consumes `reason_code_hotspots` from the operations summary daily
rows. It creates `check_id: "reason-code-hotspot"` items with the bounded
`reason_code`, source day, hotspot ratio, and sanitized aggregate
`reason_code_counts`.

These actions cover cheap-first/Gemini routing labels such as
`over_task_budget`, `operator_review_required`,
`routed_to_recommended_model`, `unknown_catalog_model`,
`unverified_price_tier`, `unknown_gateway_routed_to_recommended`,
`non_stable_model_routed_to_recommended`, allow-gated
`gateway_passthrough`, and `unknown_reason_code`.
They do not include prompts, legal text, payload fragments, model output,
emails, credentials, or arbitrary free text.

## Endpoints

```http
GET /api/v1/maintenance/route-telemetry-triage
```

Returns the standalone triage queue, including status, counts, prioritized
items, recommended actions, privacy boundary, release guardrails, and validation
commands.

```http
GET /api/v1/aihub/models
```

The AIHub model-ops payload includes `route_telemetry_triage`, and
`model_ops_readiness` includes a `route-telemetry-triage` component.

The frontend `/model-ops` page renders the queue between the route telemetry
operations summary and route guardrails.

`RouteTelemetryRemediationPlanService` consumes the queue to create
operator-reviewed remediation steps and optional env suggestions.

## Item Shape

Each triage item includes:

- `id`
- `title`
- `severity`
- `priority`
- `check_id`
- `metric`
- `value`
- `threshold`
- `reason`
- `action`
- `owner`
- `release_gate_links`
- `evidence_paths`
- `validation_commands`

## Release Checks

`route-telemetry-triage-queue` is a required `model_ops` release-readiness
gate. Blocking queue items and reason-code hotspots should be reviewed before
changing Gemini/NewAPI defaults.

Run:

```powershell
cd D:\小律师\app\backend
python -m pytest tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_repository.py -q
```

## Privacy Boundary

The queue consumes operations summary checks and daily rows only. It must not
include prompts, legal text, client details, gateway credentials, headers,
request bodies, response bodies, raw payloads, emails, or raw model outputs.

## Related Files

- `app/backend/services/route_telemetry_triage_queue.py`
- `app/backend/services/route_telemetry_ops_summary.py`
- `app/backend/services/route_telemetry_repository.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/routers/maintenance.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_route_telemetry_triage_queue.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
