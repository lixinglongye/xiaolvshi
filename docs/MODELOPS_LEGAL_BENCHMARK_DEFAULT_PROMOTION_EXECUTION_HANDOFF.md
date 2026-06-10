# ModelOps Legal Benchmark Default-Promotion Execution Handoff

`modelops-legal-benchmark-default-promotion-execution-handoff` is a
metadata-only execution handoff and rollback gate for cheap-first legal default
promotion review.

It consumes:

- `legal_benchmark_default_promotion_signoff_packet`

The handoff is downstream of the default-promotion bridge, checklist, and
signoff packet. It packages external execution prerequisites after signoff
review without feeding back into upstream release decisions.

## API

- `GET /api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff`
- `POST /api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff`
- Aggregate field: `legal_benchmark_default_promotion_execution_handoff`

The aggregate `/api/v1/aihub/models` payload also feeds the handoff into:

- `model_ops_readiness`
- the `/model-ops` review page
- release-readiness evidence
- the continuous update ledger

## Execution Policy

The handoff blocks when the upstream signoff packet is missing or blocked. A row
can become `ready_for_external_execution` only when the row has external signoff
metadata, rollback plan metadata, config diff review metadata, and post-change
observation metadata. Even then, this service only produces evidence for
external maintainers; it never applies the default change.

Key decision flags:

- `default_change_allowed_by_execution_handoff` is always `false`.
- `configuration_change_allowed` is always `false`.
- `gateway_call_allowed` is always `false`.
- `traffic_shift_allowed` is always `false`.
- `rollback_execution_allowed` is always `false`.
- `rollback_executed` is always `false`.
- `signoff_record_written` is always `false`.

## Rollback Gate

`rollback_gate_items` expose the per-row rollback status, owner role, rollback
check ids, and no-execution boundaries. They are intentionally separate from
handoff rows so reviewers can see rollback readiness before any external config
change.

Required rollback checks include:

- previous default model recorded
- rollback owner assigned
- route telemetry watch ready
- legal benchmark smoke rerun ready

## Privacy Boundary

The handoff returns signoff item ids, fixture ids, model ids, execution roles,
rollback check ids, source statuses, counts, and review actions only.

It does not return raw legal text, fixture snippets, document snippets, prompts,
generated document text, model outputs, gateway payloads, headers, credentials,
emails, approver identity, or identifiers. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, public datasets, models, or the
network.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_modelops_legal_benchmark_default_promotion_execution_handoff.py tests/test_modelops_legal_benchmark_default_promotion_signoff_packet.py tests/test_model_ops_readiness.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
