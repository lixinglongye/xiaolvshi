# Legal Document Fact Consistency Benchmark

This benchmark adds deterministic, laptop-safe checks for structured legal-document outputs.

## Purpose

The existing local legal-document benchmark checks structure, citations, PII exclusion, and risk labels. This benchmark covers a different failure mode: a generated or normalized legal document may preserve the right structure while getting amounts, dates, deadlines, or mutually exclusive facts wrong.

`legal_document_fact_consistency_benchmark` checks:

- amount consistency, such as `monthly_rent * 2 = arrears_total`;
- deadline consistency, such as notice date plus cure period;
- required fact presence, such as payment schedule, source attachment, or SLA gap facts;
- contradiction exclusion, such as asserting both paid and unpaid states;
- raw-input rejection, so prompts, generated text, raw responses, headers, credentials, and client identifiers are never echoed.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/document-fact-consistency
POST /api/v1/maintenance/legal-review-benchmark/document-fact-consistency
```

The GET endpoint returns synthetic structured expectations only.

The POST endpoint accepts a map keyed by benchmark case ID:

```json
{
  "fact-lease-arrears-mini": {
    "amounts": {
      "monthly_rent": 4800,
      "arrears_total": 9600
    },
    "deadlines": {
      "cure_due_date": "2026-04-08"
    },
    "facts": [
      "lease_exists",
      "two_month_arrears",
      "written_notice_required"
    ]
  }
}
```

The POST result returns case IDs, scores, missing/mismatch counts, contradiction counts, raw-field counts, and reason codes. It does not return raw document text or candidate text.

## ModelOps Gate

`modelops_legal_fixture_cheap_first_benchmark_gate` now requires all three local legal-document signals before cheap-first default-change evidence can be treated as ready:

- selected legal fixture observations pass;
- legal document benchmark structure/citation/PII/risk checks pass;
- legal document fact consistency checks pass.

If fact consistency is `not_run`, failed, or blocked by amount/date/fact contradictions, `default_change_evidence_allowed` remains false.

## Safety

This benchmark is metadata-only. It does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network. It does not download public datasets, import external benchmark samples, write configuration, shift traffic, or claim public benchmark scores.

The service rejects or counts forbidden raw fields without echoing their content:

- `document_text`
- `fixture_text`
- `generated_text`
- `output_text`
- `raw_output`
- `raw_response`
- `prompt`
- `messages`
- `headers`
- `authorization`
- `api_key`

## Validation

```bash
python -m pytest tests/test_legal_document_fact_consistency_benchmark.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py -q
```

For release readiness and UI evidence:

```bash
python -m pytest tests/test_legal_document_fact_consistency_benchmark.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/legal_document_fact_consistency_benchmark.py`
- `app/backend/tests/test_legal_document_fact_consistency_benchmark.py`
- `app/backend/services/modelops_legal_fixture_cheap_first_benchmark_gate.py`
- `app/backend/tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py`
- `app/backend/routers/maintenance.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/maintenance_evidence.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
