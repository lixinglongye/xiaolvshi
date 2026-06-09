# ModelOps Legal Fixture Default Promotion Packet

This packet turns the legal fixture cheap-first benchmark gate into a maintainer-review artifact for default model promotion decisions.
It is exposed through the maintenance endpoints, the AIHub ModelOps aggregate
payload, `/api/v1/aihub/models/legal-fixture-cheap-first-default-promotion-packet`,
and the ModelOps main page so maintainers can review fixture promotion evidence
next to cheap-first calibration and release queues.

It is intentionally non-mutating:

- It does not write configuration.
- It does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network.
- It does not shift traffic.
- It does not claim maintainer approval or automatic default changes.
- It does not return raw legal text, fixture snippets, prompts, generated document text, model outputs, credentials, or emails.

## Evidence Sources

- `ModelOpsLegalFixtureCheapFirstBenchmarkGateService`
- Legal fixture smoke observations, when supplied by local tests
- Legal document benchmark status and coverage metadata
- Legal document fact-consistency status and blocker metadata
- Legal document local rule baseline status and match-count metadata
- Gemini/NewAPI cheap-first calibration status, linked task IDs, release gates,
  and decisions
- Privacy and claim-boundary flags from the source gate

The packet accepts a prebuilt source gate through `source_gate`, `gate`, `cheap_first_benchmark_gate`, or `legal_fixture_cheap_first_benchmark_gate`. When no source gate is provided, it builds one from the submitted metadata payload.

## Status Rules

- `ready_for_maintainer_review`: every promotion item has passing fixture evidence, document benchmark pass evidence, fact-consistency pass evidence, local rule baseline pass evidence, cheap-first calibration pass evidence, ready coverage, and metadata-only privacy boundaries.
- `review_required`: evidence exists but has watchlist or incomplete promotion readiness.
- `blocked`: fixture evidence, document benchmark evidence, coverage, or privacy checks block default-promotion review.
- `not_ready`: no usable fixture or document benchmark evidence has been supplied.

`ready_for_maintainer_review` is not approval. It means a maintainer can review the packet and decide whether to apply a configuration change outside this service. The packet returns calibration task IDs, release gates, local rule baseline status, and match counts only; it never returns local rule predictions, extracted field values, calibration payloads, prompts, gateway responses, or model output.

## API

- `GET /api/v1/maintenance/legal-review-benchmark/cheap-first-default-promotion-packet`
- `POST /api/v1/maintenance/legal-review-benchmark/cheap-first-default-promotion-packet`
- Backward-compatible alias: `/api/v1/maintenance/legal-review-benchmark/default-promotion-packet`
- `GET /api/v1/aihub/models/legal-fixture-cheap-first-default-promotion-packet`

## Validation

```bash
python -m pytest tests/test_modelops_legal_fixture_default_promotion_packet.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_gemini_newapi_cheap_first_calibration.py tests/test_legal_document_benchmark_fixtures.py tests/test_legal_document_fact_consistency_benchmark.py -q
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```
