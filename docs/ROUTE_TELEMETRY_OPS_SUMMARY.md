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
- route reason-code hotspots,
- downgrade evidence for cheap-first routing,
- persisted estimated cost totals.

The persisted cost totals now come from catalog-priced runtime route events:
known Gemini/NewAPI-compatible catalog models use local token prices, while
unknown gateway model IDs stay unpriced and are surfaced through the unknown
model checks.

If official provider or gateway pricing, lifecycle status, or model availability
has not been confirmed, the route must stay `unpriced` and `review-only`.
Operations summaries must not hard-code a cost, include the route in
cheap-first savings claims, or support default promotion until source-backed
price, status, capability, and gateway evidence are refreshed.

## Reason-Code Hotspots

The summary now rolls repository `reason_code_counts` into both
`summary.reason_code_counts` and each `daily_rows[].reason_code_counts`. It
also returns `top_reason_codes` for quick inspection and
`reason_code_hotspots` for operational labels such as `over_task_budget`,
`operator_review_required`, `routed_to_recommended_model`,
`unknown_catalog_model`, `unverified_price_tier`,
`unknown_gateway_routed_to_recommended`,
`non_stable_model_routed_to_recommended`, allow-gated
`gateway_passthrough`, and `unknown_reason_code`.

Known healthy labels such as `known_catalog_model` and `within_task_budget`
remain visible in top counts but do not become hotspot actions. Unknown labels
are normalized upstream to `unknown_reason_code` and produce an
`unknown-reason-code-count` check so maintainers fix the producer or extend the
allowlist before relying on the label for release evidence.

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

`RouteTelemetryTriageQueueService` consumes this summary to create prioritized
maintainer actions for release review.

## Release Checks

`route-telemetry-ops-summary` is a required `model_ops` release-readiness gate.
It fails when repository status is unavailable or when persisted aggregates
exceed failure, over-budget, operator-review, premium-model, unknown-model,
unknown-reason-code, or reason-code-hotspot thresholds.

Run:

```powershell
cd D:\小律师\app\backend
python -m pytest tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_repository.py tests/test_model_route_telemetry.py -q
python -m pytest tests/test_route_telemetry_repository.py tests/test_aihub_runtime_routing.py tests/test_model_usage.py -q
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
