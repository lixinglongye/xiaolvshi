# ModelOps Legal Benchmark Default-Promotion Bridge

`modelops-legal-benchmark-default-promotion-bridge` is a metadata-only
maintainer review packet for cheap-first legal default promotion.

It joins five existing signals:

- `legal_fixture_cheap_first_benchmark_gate`
- `legal_fixture_cheap_first_default_promotion_packet`
- `legal_fixture_cheap_first_regression_budget`
- `legal_fixture_evidence_handoff`
- `gemini_official_lifecycle_drift_gate`

The bridge exists because no single source should be enough to move a legal-task
default. Legal fixture benchmark status, document benchmark status, fact
consistency, regression budget, handoff/archive evidence, and Gemini lifecycle
drift all need to be visible together before maintainers review a change.

## API

- `GET /api/v1/aihub/models/legal-benchmark-default-promotion-bridge`
- `POST /api/v1/aihub/models/legal-benchmark-default-promotion-bridge`
- Aggregate field: `legal_benchmark_default_promotion_bridge`

The aggregate `/api/v1/aihub/models` payload also feeds the bridge into:

- `model_ops_readiness`
- `cheap_first_release_decision`
- the `/model-ops` review page

## Review Policy

The bridge blocks review when legal fixture evidence is blocked or when the
Gemini lifecycle drift gate reports blocked defaults. Ready source evidence
still requires maintainer review. The bridge never approves or applies a default
change.

Key decision flags:

- `default_change_allowed_by_bridge` is always `false`.
- `configuration_change_allowed` is always `false`.
- `gateway_call_allowed` is always `false`.
- `traffic_shift_allowed` is always `false`.
- `maintainer_review_required` is always `true`.

## Privacy Boundary

The bridge returns source statuses, fixture ids, model ids, check ids, counts,
reason codes, endpoints, and review actions only.

It does not return raw legal text, fixture snippets, document snippets, prompts,
generated document text, model outputs, gateway payloads, headers, credentials,
emails, or identifiers. It does not call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, public datasets, models, or the network.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_modelops_legal_benchmark_default_promotion_bridge.py tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
