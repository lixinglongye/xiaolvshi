# ModelOps Legal Benchmark Default-Promotion Checklist

`modelops-legal-benchmark-default-promotion-checklist` is a metadata-only
maintainer checklist for cheap-first legal default promotion.

It consumes:

- `legal_benchmark_default_promotion_bridge`
- `cheap_first_release_decision`, when available
- `default_change_queue`, when available

The checklist is downstream of the release decision and default-change queue.
It does not feed back into either signal, so the release graph avoids circular
default-promotion dependencies.

## API

- `GET /api/v1/aihub/models/legal-benchmark-default-promotion-checklist`
- `POST /api/v1/aihub/models/legal-benchmark-default-promotion-checklist`
- Aggregate field: `legal_benchmark_default_promotion_checklist`

The aggregate `/api/v1/aihub/models` payload also feeds the checklist into:

- `model_ops_readiness`
- the `/model-ops` review page
- release-readiness evidence
- the continuous update ledger

## Review Policy

The checklist blocks when the bridge, release decision, or default-change queue
has blocking evidence. Missing release decision or queue evidence remains
`review_required` because those sources can be attached later.

Ready legal benchmark promotion rows still require maintainer signoff. The
service never approves or applies a default change.

Key decision flags:

- `default_change_allowed_by_checklist` is always `false`.
- `configuration_change_allowed` is always `false`.
- `gateway_call_allowed` is always `false`.
- `traffic_shift_allowed` is always `false`.
- `maintainer_review_required` is always `true`.

## Privacy Boundary

The checklist returns source statuses, fixture ids, model ids, queue ids,
checklist statuses, signoff roles, check ids, counts, and review actions only.

It does not return raw legal text, fixture snippets, document snippets, prompts,
generated document text, model outputs, gateway payloads, headers, credentials,
emails, or identifiers. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, public datasets, models, or the network.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_modelops_legal_benchmark_default_promotion_checklist.py tests/test_modelops_legal_benchmark_default_promotion_bridge.py tests/test_model_ops_readiness.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
