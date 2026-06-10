# Legal Document Benchmark Route Plan

This slice adds a metadata-only cheap-first route plan for the local synthetic
legal-document benchmark suite.

## Implemented Evidence

- Service: `app/backend/services/legal_document_benchmark_route_plan.py`
- Route: `GET /api/v1/maintenance/legal-review-benchmark/document-route-plan`
- Route: `POST /api/v1/maintenance/legal-review-benchmark/document-route-plan`
- Tests: `app/backend/tests/test_legal_document_benchmark_route_plan.py`
- Inputs: `legal_document_benchmark_suite`, `legal_document_benchmark_coverage`,
  `model_runtime_router`, and `model_default_candidate_selector`

## What It Reports

- A per-case route row for each synthetic legal-document benchmark case.
- Mandatory Flash-Lite precheck routing for classification, structure, PII, and
  risk-label checks.
- Budgeted primary routes for generation, review, grounded research, and
  evidence-catalog classification.
- Escalation ladders from the local Gemini catalog.
- Metadata-only request cost estimates from local catalog pricing.
- Blocking checks for premium primary defaults and missing cheap prechecks.

## Boundaries

The plan does not execute model calls, shift production defaults, download
public datasets, or claim public benchmark scores. It does not return raw fixture
snippets, prompts, generated document text, gateway payloads, raw model outputs,
credentials, emails, phone numbers, identity numbers, or client identifiers.

## Validation

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py -q
```
