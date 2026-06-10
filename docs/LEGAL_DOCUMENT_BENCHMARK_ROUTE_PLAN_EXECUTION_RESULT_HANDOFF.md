# Legal Document Benchmark Route Plan Execution Result Handoff

`legal-document-benchmark-route-plan-execution-result-handoff` is a
metadata-only release-evidence decision layer for sanitized manual
legal-document route-plan observations.

Endpoints:

- `GET /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-handoff`
- `POST /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-handoff`

The handoff joins the execution-readiness packet and execution-result archive.
It marks result rows as attachable, review-required, or blocked before the
archive is used as release evidence.

## What It Checks

- Execution readiness is ready.
- The sanitized result archive is ready.
- At least one manual observation row is present before evidence attachment.
- Every archive row is attachable or explicitly reviewed.
- Observed models remain aligned with the cheap-first route plan.
- Observations remain inside `fixture_limit=3`.
- `max_parallel_model_requests` remains `1`.
- Submitted payloads stay metadata-only.

## Boundaries

This service does not:

- Execute benchmark runs.
- Call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network.
- Write release records, archive files, configuration, or defaults.
- Record maintainer approval.
- Claim public benchmark scores, production quality, real client-document
  coverage, or release approval.
- Return public benchmark text, raw legal text, fixture snippets, prompts,
  request bodies, response bodies, headers, generated text, model outputs,
  gateway responses, emails, identifiers, or credentials.

Allowed evidence is limited to sanitized case id, phase, observed model,
status, token, cost, latency, fallback, and coarse error metadata after all
handoff checks pass.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_document_benchmark_route_plan_execution_result_handoff.py -q
```
