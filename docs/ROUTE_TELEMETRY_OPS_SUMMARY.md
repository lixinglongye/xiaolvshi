# Route Telemetry Operations Summary

The route telemetry operations summary turns the local, sanitized route
telemetry repository into release-review evidence for cheap-first model
routing.

## Purpose

`RouteTelemetryRepositoryService` stores allowed metadata fields and daily
aggregate buckets. `RouteTelemetryOpsSummaryService` reads those aggregates and
calculates operational checks for:

- route failure rate,
- over-budget pressure,
- operator-review load,
- premium model drift,
- unknown model usage,
- downgrade evidence for cheap-first routing,
- persisted estimated cost totals.

An empty repository returns `ready` so local development is not blocked, but it
is not production proof. Maintainers still need staging or production route
events before treating telemetry as routing health evidence.

## Endpoints

```http
GET /api/v1/maintenance/route-telemetry-ops-summary
```

Returns the standalone operations summary with thresholds, daily rows,
blocking checks, warning checks, recommended actions, privacy boundary, and
validation commands.

```http
GET /api/v1/aihub/models
```

The AIHub model-ops payload includes `route_telemetry_ops_summary`, and
`model_ops_readiness` now has a `route-telemetry-ops-summary` component.

The frontend `/model-ops` page renders the summary cards and daily table next
to the route telemetry repository panel.

## Release Checks

`route-telemetry-ops-summary` is a required `model_ops` release-readiness gate.
It fails when repository status is unavailable or when persisted aggregates
exceed failure, over-budget, operator-review, premium-model, or unknown-model
thresholds.

Run:

```powershell
cd D:\小律师\app\backend
python -m pytest tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_repository.py tests/test_model_route_telemetry.py -q
```

## Privacy Boundary

The summary consumes repository daily buckets and totals only. It must not read
or persist prompts, legal text, client details, gateway credentials, headers,
request bodies, response bodies, raw payloads, emails, or raw model outputs.

## Related Files

- `app/backend/services/route_telemetry_ops_summary.py`
- `app/backend/services/route_telemetry_repository.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/routers/maintenance.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_route_telemetry_ops_summary.py`
- `app/backend/tests/test_route_telemetry_repository.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
