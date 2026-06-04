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
- daily route telemetry hotspots,
- missing staging telemetry when no route events exist.

Empty telemetry returns `ready` with an informational staging-event action. That
keeps local development unblocked while making clear that production routing
health is still unproven.

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
gate. Blocking queue items should be reviewed before changing Gemini/NewAPI
defaults.

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
