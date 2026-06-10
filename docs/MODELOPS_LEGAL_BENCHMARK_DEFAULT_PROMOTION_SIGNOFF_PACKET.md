# ModelOps Legal Benchmark Default-Promotion Signoff Packet

`modelops-legal-benchmark-default-promotion-signoff-packet` is a
metadata-only signoff packet for cheap-first legal default promotion review.

It consumes:

- `legal_benchmark_default_promotion_checklist`

The signoff packet is downstream of the bridge, release decision,
default-change queue, and checklist. It does not feed back into those signals,
so the release graph avoids circular default-promotion dependencies.

## API

- `GET /api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet`
- `POST /api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet`
- Aggregate field: `legal_benchmark_default_promotion_signoff_packet`

The aggregate `/api/v1/aihub/models` payload also feeds the packet into:

- `model_ops_readiness`
- the `/model-ops` review page
- release-readiness evidence
- the continuous update ledger

## Review Policy

The packet blocks when the upstream checklist is missing or blocked. Ready
checklist rows become signoff items with required roles and pre-signoff checks.
The packet never records approval, collects approver identity, writes a signoff
record, or applies a default change.

Key decision flags:

- `default_change_allowed_by_signoff_packet` is always `false`.
- `configuration_change_allowed` is always `false`.
- `gateway_call_allowed` is always `false`.
- `traffic_shift_allowed` is always `false`.
- `signoff_record_written` is always `false`.
- `approver_identity_collected` is always `false`.

## Privacy Boundary

The packet returns checklist row ids, fixture ids, model ids, signoff roles,
pre-signoff checks, check ids, counts, and review actions only.

It does not return raw legal text, fixture snippets, document snippets, prompts,
generated document text, model outputs, gateway payloads, headers, credentials,
emails, approver identity, or identifiers. It does not call NewAPI, Gemini,
OpenAI, Google, gateways, app AI endpoints, public datasets, models, or the
network.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_modelops_legal_benchmark_default_promotion_signoff_packet.py tests/test_modelops_legal_benchmark_default_promotion_checklist.py tests/test_model_ops_readiness.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
