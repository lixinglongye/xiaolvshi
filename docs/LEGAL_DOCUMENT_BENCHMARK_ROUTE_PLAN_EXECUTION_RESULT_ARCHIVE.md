# Legal Document Benchmark Route Plan Execution Result Archive

`legal-document-benchmark-route-plan-execution-result-archive` is a
metadata-only post-run evidence packet for the local synthetic legal-document
benchmark route plan.

It is available at:

- `GET /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-archive`
- `POST /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-archive`

The archive is designed for the step after execution readiness. Maintainers can
paste sanitized manual observation metadata for up to three route-plan cases and
compare it with the cheap-first route plan.

Accepted observation fields:

- `case_id`
- `phase`
- `observed_model`
- `observed_status`
- `observed_cost_usd`
- `observed_input_tokens`
- `observed_output_tokens`
- `latency_ms`
- `fallback_used`
- `error_category`

The service checks route-plan case matching, expected model alignment, the
`fixture_limit=3` envelope, `max_parallel_model_requests=1`, observed cost
metadata, latency metadata, fallback visibility, and forbidden raw payload
fields.

It does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints,
models, public datasets, or the network. It does not execute benchmark runs,
write archive files, record maintainer approval, change model defaults, shift
traffic, write configuration, claim public benchmark scores, or claim production
legal quality.

Do not submit or store prompts, raw legal text, fixture snippets, public
benchmark text, request bodies, response bodies, headers, gateway responses,
model outputs, generated document text, emails, identifiers, credentials, or
client material.

Validation:

```powershell
cd app/backend
python -m pytest tests/test_legal_document_benchmark_route_plan_execution_result_archive.py -q
```
