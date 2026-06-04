# Legal Document Coverage Claim Policy

This slice adds a metadata-only claim policy for legal-document coverage wording. It keeps the local 6/6 synthetic fixture matrix useful for regression planning while blocking public claims that would overstate benchmark, real-client, or universal document coverage.

## Implemented evidence

- Service: `app/backend/services/legal_document_coverage_claim_policy.py`
- Route: `POST /api/v1/maintenance/legal-review-benchmark/document-coverage/claims`
- Tests: `app/backend/tests/test_legal_document_coverage_claim_policy.py`
- UI aggregation: `app/frontend/src/lib/maintenanceApi.ts`
- Source matrix: `GET /api/v1/maintenance/legal-review-benchmark/document-coverage`

## What It Allows

Allowed wording must stay scoped to repository-backed local fixtures. Example:

```text
Repository tests include synthetic local fixtures covering civil complaints, lawyer letters, contract review, evidence catalogs, settlement agreements, and legal opinions.
```

## What It Blocks

The policy blocks or flags claims that mention:

- Full, all, any, complete, universal, or broad legal-document coverage.
- Real client documents, production cases, customer documents, or law-firm adoption.
- LegalBench, LexGLUE, COLIEE, leaderboard, or public benchmark score claims.
- Unsupported document types such as appeal briefs, arbitration applications, and bankruptcy filings.
- Email addresses or `sk-` style secrets, which are dropped from output and represented only by reason codes.

## Research Calibration

The policy stores source URLs and scope notes only; it does not download external datasets or include external dataset content.

- LegalBench: https://arxiv.org/abs/2308.11462
- LexGLUE: https://arxiv.org/abs/2110.00976
- COLIEE: https://sites.ualberta.ca/~rabelo/COLIEE2024/
- CUAD: https://arxiv.org/abs/2103.06268

These sources calibrate wording boundaries. They do not provide evidence that this repository has public benchmark runs, leaderboard scores, or real client-document validation.

## Privacy Boundary

Responses include claim hashes, matched document-type IDs, unsupported document-type IDs, reason codes, coverage counts, source URLs, and status only. They do not include raw claim text, client document text, prompts, model output, PII, secrets, or external dataset content.

## Validation

```bash
cd app/backend && python -m pytest tests/test_legal_document_coverage_claim_policy.py tests/test_legal_document_benchmark_coverage.py -q
cd app/frontend && npm run typecheck
```
