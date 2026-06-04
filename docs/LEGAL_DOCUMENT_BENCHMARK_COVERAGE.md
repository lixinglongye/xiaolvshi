# Legal Document Benchmark Coverage

This slice adds a metadata-only coverage matrix for the tiny local legal-document benchmark fixtures and fills the first matrix gaps with synthetic evidence-catalog, settlement-agreement, and legal-opinion fixtures. A follow-up claim policy now checks public wording against this matrix so local synthetic coverage is not overstated as public benchmark, real-client, or universal legal-document coverage.

## Implemented evidence

- Service: `app/backend/services/legal_document_benchmark_coverage.py`
- Route: `GET /api/v1/maintenance/legal-review-benchmark/document-coverage`
- Tests: `app/backend/tests/test_legal_document_benchmark_coverage.py`
- UI: `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- Claim policy: `POST /api/v1/maintenance/legal-review-benchmark/document-coverage/claims`

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

The current local benchmark suite covers all six target document types with synthetic, short, laptop-safe fixtures. This means the local target matrix is complete, but broad legal-document coverage claims remain blocked by `legal-document-coverage-claim-policy` until larger public-source review, real-world workflow testing, public benchmark runs, and lawyer review evidence exist.

## Validation

```bash
cd app/backend && python -m pytest tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_benchmark_suite.py -q
cd app/backend && python -m pytest tests/test_legal_document_coverage_claim_policy.py -q
cd app/frontend && npm run typecheck
```

## Boundaries

This is a laptop-safe planning and regression artifact. It does not claim public benchmark scores, external dataset execution, live model performance, real client-document testing, or full product coverage.
