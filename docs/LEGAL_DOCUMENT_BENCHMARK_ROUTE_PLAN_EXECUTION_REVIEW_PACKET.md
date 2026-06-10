# Legal Document Benchmark Route Plan Execution Review Packet

`legal-document-benchmark-route-plan-execution-review-packet` is a
metadata-only reviewer packet for the legal-document route-plan execution
evidence chain.

Endpoints:

- `GET /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-review-packet`
- `POST /api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-review-packet`

The packet joins:

- execution readiness
- sanitized execution-result archive
- execution-result handoff

It gives reviewers one attach/review/hold packet before sanitized observation
metadata is used as release evidence.

## What It Checks

- Execution readiness is ready.
- The sanitized result archive is ready.
- The release-evidence handoff is ready.
- Observed models remain aligned with the cheap-first route plan.
- Observations remain inside `fixture_limit=3`.
- `max_parallel_model_requests` remains `1`.
- Blocked source rows expose blocker ids.
- Local validation commands are present.

## Allowed Claim

Only this narrow claim can become allowed when the packet is ready:

> Sanitized manual legal-document route-plan result metadata is ready for
> release evidence.

The packet never allows public benchmark score claims, live provider execution
claims, release approval claims, or maintainer approval claims.

## Boundaries

This service does not:

- Execute benchmark runs.
- Call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or
  the network.
- Write release records, archive files, configuration, defaults, or traffic
  shifts.
- Record maintainer approval.
- Claim public benchmark scores, production quality, real client-document
  coverage, release approval, or live provider execution.
- Return public benchmark text, raw legal text, fixture snippets, prompts,
  request bodies, response bodies, headers, generated text, model outputs,
  gateway responses, emails, identifiers, or credentials.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_document_benchmark_route_plan_execution_review_packet.py -q
```
