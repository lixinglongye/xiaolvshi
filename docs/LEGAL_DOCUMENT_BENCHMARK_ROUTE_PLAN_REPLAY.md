# Legal Document Benchmark Route Plan Replay

This evidence slice adds a deterministic replay surface for the local synthetic
legal-document benchmark route plan.

Routes:

- `GET /api/v1/maintenance/legal-review-benchmark/document-route-plan/replay`
- `POST /api/v1/maintenance/legal-review-benchmark/document-route-plan/replay`

The replay runs small metadata-only scenarios against the route-plan service and
checks whether expected cheap-first behavior still holds:

- default contract-review routes stay on Flash after Flash-Lite prechecks;
- evidence-catalog classification stays on Flash-Lite;
- unapproved premium review overrides route back to the recommended Flash model;
- simulated approved premium primary routes remain blocked by
  `no-premium-primary-defaults`;
- grounded legal-opinion routes stay on the configured Flash-Lite grounded path.

`POST` accepts scenario metadata under `scenarios` with fields such as
`case_id`, `override_primary_task`, `override_primary_model`,
`override_approval`, expected status/model/cost/route band, and expected
blocking ids. Submitted ids and model ids are sanitized before evaluation.

The replay is intentionally inert. It does not call NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, public datasets, models, or the network. It
does not execute benchmark runs, change defaults, shift traffic, write
configuration, or record approvals.

The response returns only scenario ids, case ids, expected route metadata,
actual route metadata, checks, counts, privacy boundaries, claim boundaries, and
recommended actions. It must not return fixture snippets, prompts, generated
document text, model outputs, gateway responses, credentials, emails, client
identifiers, or submitted rationale text.

Validation:

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_replay.py -q
```

Full evidence gate:

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_replay.py tests/test_legal_document_benchmark_route_plan.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_model_runtime_router.py tests/test_model_default_candidate_selector.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py -q
```
