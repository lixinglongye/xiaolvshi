# Legal Document Benchmark Coverage

This slice adds a metadata-only coverage matrix for the tiny local legal-document benchmark fixtures.

## Implemented evidence

- Service: `app/backend/services/legal_document_benchmark_coverage.py`
- Route: `GET /api/v1/maintenance/legal-review-benchmark/document-coverage`
- Tests: `app/backend/tests/test_legal_document_benchmark_coverage.py`
- UI: `app/frontend/src/pages/MaintenanceEvidencePage.tsx`

## What the matrix reports

- Covered and missing legal document types.
- Per-fixture coverage counts for required sections, citations, risk labels, and PII bans.
- A capped next-fixture queue for low-resource local validation.
- Privacy boundaries proving that the matrix does not return snippets, client identifiers, prompts, gateway responses, or raw model outputs.

## Current known gaps

The initial target matrix tracks:

- `civil_complaint`
- `lawyer_letter`
- `contract_review`
- `evidence_catalog`
- `settlement_agreement`
- `legal_opinion`

The current local benchmark suite covers the first three. The matrix therefore keeps broad legal-document coverage claims blocked until synthetic fixtures exist for evidence catalogs, settlement agreements, and legal opinions.

## Validation

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_benchmark_suite.py -q
cd app/frontend && npm run typecheck
```

## Boundaries

This is a laptop-safe planning and regression artifact. It does not claim public benchmark scores, external dataset execution, live model performance, real client-document testing, or full product coverage.
