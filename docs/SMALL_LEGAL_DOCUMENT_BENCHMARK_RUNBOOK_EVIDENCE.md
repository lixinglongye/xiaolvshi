# Small Legal Document Benchmark Runbook Evidence

This slice adds a metadata-only runbook packet for small, local legal-document
benchmark checks. It joins existing synthetic corpus, document structure,
fact-consistency, and final-delivery release gate evidence so reviewers can see
one low-resource readiness packet before any public claims are made.

## Endpoint

- `GET /api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence`
- `POST /api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence`

The `POST` endpoint accepts optional local evaluation metadata:

- `document_benchmark_outputs`
- `document_fact_consistency_outputs`
- `final_delivery_payload`

Raw input values are never echoed. The service counts suspicious raw fields and
sensitive-looking values only as metadata so reviewers can block unsafe runs.

## Evidence Packet

The packet includes:

- `runbook_steps` for the serial low-resource review flow
- `document_benchmark_rows` for structure, citation, and risk-label checks
- `fact_consistency_rows` for amount, date, fact, and contradiction checks
- `delivery_gate_rows` for final package, review, payment, and client-delivery
  readiness controls
- aggregate `checks`, `blocking_check_ids`, and `warning_check_ids`
- `privacy_boundary` and `claim_boundary` flags

Statuses are conservative:

- `ready` when all joined checks pass
- `review_required` when rows are not run, warnings exist, or a template gate is
  still present
- `blocked` when any joined check fails or unsafe raw input is detected

## Boundaries

This evidence does not:

- call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the
  network
- download public benchmark datasets or import public benchmark text
- return raw legal text, fixture snippets, document snippets, generated text,
  prompts, request bodies, response bodies, gateway payloads, model outputs,
  emails, identifiers, or credentials
- claim public benchmark scores, production legal quality, client document
  coverage, final document generation, legal advice, or client delivery

Allowed claim:

`Small local benchmark runbook evidence for synthetic legal-document delivery readiness.`

## Validation

Run the focused backend test:

```powershell
cd app/backend
python -m pytest tests/test_small_legal_document_benchmark_runbook_evidence.py -q
```

Run the release-facing chain before claiming the slice is reviewable:

```powershell
cd app/backend
python -m pytest tests/test_small_legal_document_benchmark_runbook_evidence.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_fact_consistency_benchmark.py tests/test_final_document_delivery_release_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```

## Files

- `app/backend/services/small_legal_document_benchmark_runbook_evidence.py`
- `app/backend/tests/test_small_legal_document_benchmark_runbook_evidence.py`
- `app/backend/routers/maintenance.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
