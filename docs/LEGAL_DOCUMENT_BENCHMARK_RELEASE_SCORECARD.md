# Legal Document Benchmark Release Scorecard

`legal-document-benchmark-release-scorecard` is a metadata-only reviewer
scorecard for local synthetic legal-document benchmark evidence.

It aggregates these repository-backed components:

- deterministic legal-document benchmark suite status
- legal-document coverage matrix status
- cheap-first route-plan status and cost metadata
- fact-consistency benchmark suite status
- document-output evaluation status when sanitized local outputs are supplied
- fact-output evaluation status when sanitized local outputs are supplied
- coverage claim policy status
- route-plan execution claim gate status

The endpoint is available at:

```http
GET /api/v1/maintenance/legal-review-benchmark/document-release-scorecard
POST /api/v1/maintenance/legal-review-benchmark/document-release-scorecard
```

The default `GET` response is intentionally `review_required`: the repository
has local fixture and policy evidence, but no document outputs, fact outputs, or
sanitized execution observations are supplied by default. A `POST` request may
provide sanitized `document_outputs`, `fact_outputs`, `observations`, and
metadata-only `execution_claims` to evaluate whether every component is ready.

This scorecard never executes benchmark runs, calls NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, models, public datasets, or the network. It
does not write release records, archive files, configuration, defaults, or
traffic shifts, and it does not record approval.

Allowed release wording is limited to local synthetic legal-document fixture
coverage and metadata-only route-plan evidence. The scorecard must not be used
to claim public benchmark scores, live provider execution, production legal
quality, release approval, default changes, traffic shifts, real
client-document coverage, or law-firm adoption.

The response must not include raw legal text, public benchmark text, fixture
snippets, generated document text, prompt text, request bodies, response
bodies, headers, model outputs, gateway responses, emails, identifiers, or
credentials.

Validation:

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_release_scorecard.py -q
cd app/backend && python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_fact_consistency_benchmark.py -q
cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan.py tests/test_legal_document_benchmark_route_plan_execution_claim_gate.py -q
```
