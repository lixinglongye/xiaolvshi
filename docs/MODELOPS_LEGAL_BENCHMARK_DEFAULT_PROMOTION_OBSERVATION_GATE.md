# ModelOps Legal Benchmark Default-Promotion Observation Gate

`modelops-legal-benchmark-default-promotion-observation-gate` is a
metadata-only post-execution observation gate for cheap-first legal default
promotion review.

It consumes:

- `legal_benchmark_default_promotion_execution_handoff`

The gate is downstream of the default-promotion bridge, checklist, signoff
packet, and execution handoff. It packages externally supplied post-change
observation evidence without making model calls or changing defaults.

## API

- `GET /api/v1/aihub/models/legal-benchmark-default-promotion-observation-gate`
- `POST /api/v1/aihub/models/legal-benchmark-default-promotion-observation-gate`
- Aggregate field: `legal_benchmark_default_promotion_observation_gate`

The aggregate `/api/v1/aihub/models` payload also feeds the gate into:

- `model_ops_readiness`
- the `/model-ops` review page
- release-readiness evidence
- the continuous update ledger

## Observation Policy

The gate blocks when the upstream execution handoff is missing or blocked. A row
can become `observation_ready` only when externally supplied route telemetry,
legal benchmark smoke, rollback-window, and incident-status metadata are
attached and clear.

Key decision flags:

- `default_change_allowed_by_observation_gate` is always `false`.
- `configuration_change_allowed` is always `false`.
- `gateway_call_allowed` is always `false`.
- `traffic_shift_allowed` is always `false`.
- `rollback_execution_allowed` is always `false`.
- `rollback_executed` is always `false`.

## Rollback Window

`rollback_window_rows` expose rollback-window status, incident status, rollback
owner role, rollback-window checks, and no-execution boundaries. Incident or
rollback-required metadata blocks the gate and keeps post-change quality claims
disabled.

## Privacy Boundary

The gate returns handoff row ids, fixture ids, model ids, observation status,
rollback-window status, incident status, counts, check ids, and review actions
only.

It does not return raw legal text, fixture snippets, document snippets, prompts,
generated document text, model outputs, gateway payloads, headers, credentials,
emails, approver identity, or identifiers. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, public datasets, models, or the
network.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_modelops_legal_benchmark_default_promotion_observation_gate.py tests/test_modelops_legal_benchmark_default_promotion_execution_handoff.py tests/test_model_ops_readiness.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
