# Legal RAG Index Coverage Gate

`GET /api/v1/maintenance/legal-rag-index-coverage-gate`

This endpoint exposes metadata-only review evidence for Legal RAG index binding
plans before retrieval diagnostics, retrieval observations, answer generation,
or export readiness are considered.

## Purpose

The gate checks whether an index binding plan has enough safe metadata to be
used by downstream Legal RAG flows:

- filter validation status
- candidate, selected, requested, and missing source counts
- retrieval locator coverage
- stale or review-due source counts
- jurisdiction and freshness alignment
- cheap-first review action metadata

It is a local review surface. It does not query an index, call models, call
NewAPI/Gemini/gateways, crawl the network, or download datasets.

## Evaluation

Rows become:

- `ready`: filters pass, at least one selected source is available, retrieval
  locators are present, jurisdiction matches, and freshness is current.
- `review_required`: index coverage exists but jurisdiction, freshness, or
  requested-source coverage needs reviewer attention.
- `blocked`: forbidden filters, empty source coverage, missing retrieval
  locators, or invalid filter metadata block retrieval-plan use.

Premium model use is not a substitute for missing source coverage or missing
retrieval locators. Cheap-first routing is allowed only when the index plan is
ready or has been explicitly reviewed.

## Metadata Boundary

The response may include only counts, status labels, reason codes, release
actions, linked gate IDs, policy metadata, input-contract metadata, and privacy
or claim boundary booleans.

It must not return source IDs, raw query text, user questions, retrieved
context, raw legal text, prompts, model outputs, gateway payloads, account data,
credentials, client material, or emails.

## Maintenance UI

The maintenance evidence page exposes the gate through
`getLegalRagIndexCoverageGate` and a panel titled
`Legal RAG index coverage gate`.

The panel shows:

- index-plan status and release-action rows
- filter, locator, coverage, jurisdiction, and freshness metadata
- status, release, coverage, and locator distributions
- the accepted metadata fields and ignored raw-text fields
- claim and privacy boundaries
- validation commands

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_rag_index_coverage_gate.py tests/test_legal_rag_index_binding.py -q
python -m pytest tests/test_legal_rag_index_coverage_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
