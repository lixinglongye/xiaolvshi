# Route Telemetry Persistence Plan

This plan defines a local, privacy-minimized contract for persisting model route telemetry. It does not require a database migration, network access, or credentials. Integration code can call `RouteTelemetryPersistencePlanService.build_plan(events)` before enabling any durable route telemetry sink.

`RouteTelemetryRepositoryService` now implements the first local sink: it writes
only sanitized allowed fields to `local_storage/model_ops/route_telemetry/events.jsonl`,
rejects duplicates or sensitive payloads, and rebuilds daily aggregate counters
in `daily_aggregates.json`.

## Event Schema

The only supported event type is `model_route_decision`.

Required fields:

- `event_id`
- `event_type`
- `timestamp`
- `task`
- `resolved_model`
- `success`

Recommended fields:

- `route_id`
- `requested_model`
- `inference_source`
- `routed_to_recommended_model`
- `is_over_budget`
- `requires_operator_review`
- `is_known_model`

Allowed metrics and metadata include route IDs, task labels, model IDs, gateway/provider labels, budget flags, success/error category, estimated token counts, estimated cost, latency, stream flag, cache flag, and coarse HTTP status.

Forbidden fields include prompt text, raw messages, raw legal documents, client names or contact details, headers, request bodies, response bodies, raw model output, passwords, secrets, and API key or bearer-token fields.

## Retention

Raw sanitized events are optional and short-lived:

- Rejected events: delete immediately.
- Passing sanitized samples: keep for up to 30 days when debug sampling is needed.
- Daily aggregate counters by task/model/budget status: keep for 400 days.
- Daily error-category counters: keep for 180 days.

Durable reporting should prefer aggregate counters:

- request count
- success and failure count
- downgrade count
- over-budget count
- operator-review count
- unknown-model count
- estimated cost sum
- latency p50 and p95

## Local Repository

The maintenance API exposes the local repository:

```http
GET /api/v1/maintenance/route-telemetry-repository
POST /api/v1/maintenance/route-telemetry-repository
```

`GET` returns current local JSONL storage metadata, aggregate totals, daily
buckets, privacy boundary, and validation commands.

`POST` accepts a list of sanitized telemetry candidate events. The repository
first runs the persistence plan. Failing events are rejected without echoing raw
secret, prompt, legal text, email, request body, response body, or model output
values. Passing and warning events are normalized to allowed fields only.

The AIHub model-ops payload also includes `route_telemetry_repository`, and the
ModelOps page renders the persisted request count, daily bucket count, rejected
latest event count, storage mode, and daily aggregate table.

`RouteTelemetryOpsSummaryService` consumes the repository daily buckets and
totals to expose release-review operations checks. It does not read raw event
payloads and uses the same privacy boundary as the repository.

`RouteTelemetryTriageQueueService` consumes that summary to prioritize
maintainer actions for cheap-first route drift, daily hotspots, and missing
staging telemetry.

```http
GET /api/v1/maintenance/route-telemetry-ops-summary
GET /api/v1/maintenance/route-telemetry-triage
```

## Pre-Persistence Checks

Before writing route telemetry to a durable sink:

- Reject events missing required fields.
- Warn on missing recommended fields because aggregate analysis becomes weaker.
- Reject any event with forbidden field names.
- Reject any event with nested forbidden fields.
- Reject any event with credential-like or contact-like values.
- Do not persist request bodies, response bodies, prompt text, document text, headers, stack traces, or raw model output.

## Privacy Boundary

Route telemetry is metadata-only. It is meant to answer operational questions such as whether cheap-first routing worked, how often requests were downgraded, and where budget gates were triggered. It must not be used as a storage layer for legal text, client identity, user contact details, credentials, or model responses.

## Validation

Run:

```powershell
cd D:\小律师\app\backend
python -m pytest tests/test_route_telemetry_persistence_plan.py -q
python -m pytest tests/test_route_telemetry_repository.py tests/test_route_telemetry_persistence_plan.py tests/test_model_route_telemetry.py -q
python -m pytest tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_repository.py tests/test_model_route_telemetry.py -q
python -m pytest tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_repository.py -q
python -m compileall services/route_telemetry_persistence_plan.py
python -m compileall services/route_telemetry_repository.py
python -m compileall services/route_telemetry_ops_summary.py
python -m compileall services/route_telemetry_triage_queue.py
```
