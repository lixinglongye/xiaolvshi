# Legal RAG Retrieval Observation Gate

`POST /api/v1/maintenance/legal-rag-retrieval-observation-gate`

This endpoint evaluates sanitized local Legal RAG retrieval observations before
maintainers claim that retrieval metadata is ready for answer release. It is a
low-resource, metadata-only check: it does not query an index, call a model, or
download public benchmark data.

## Input Contract

The payload accepts one of these array containers:

- `retrieval_observations`
- `observations`
- `rows`

Each row should contain structured metadata only:

- `id` and `query_intent`
- `expected_source_count`
- `selected_source_ids`
- `citation_source_ids`
- `top_k_depth`
- `jurisdiction_match` or `jurisdiction_status`
- `freshness_status`
- optional `stale_source_ids`, `unknown_source_ids`, `citation_gap`,
  `retrieval_gap`, and deterministic `signals`

Raw fields such as query text, user questions, retrieved context, prompts, model
outputs, and legal text are ignored and must not be returned.

## Evaluation

The gate joins selected-source citation validation with retrieval metadata:

- source coverage: expected source count vs selected source count
- citation validation: unexpected, missing, stale, or unknown cited sources
- top-k depth: sufficient, shallow, or empty
- jurisdiction and freshness status
- citation and retrieval gap flags
- cheap-first routing decision labels from local escalation metadata

Rows become:

- `ready`: source coverage, citations, top-k depth, jurisdiction, and freshness
  all pass.
- `review_required`: partial coverage, shallow top-k, review-due freshness,
  jurisdiction uncertainty, or citation/retrieval warnings need maintainer
  review.
- `blocked`: missing selected-source context, blocked citation validation,
  empty top-k depth, source coverage gaps, or overlapping citation and retrieval
  gaps block answer release.

Premium model use is not a substitute for missing retrieval context. The gate
keeps cheap-first routing for ready rows and requires operator review when
retrieval metadata blocks release.

## Metadata Boundary

The response may include only counts, status labels, reason codes, release
actions, cheap-first action metadata, input-contract metadata, and privacy or
claim boundary booleans.

It must not return source ids, raw query text, retrieved context, raw legal text,
prompts, model outputs, gateway payloads, account data, credentials, client
material, or emails. It must not call NewAPI, Gemini, OpenAI, models, gateways,
crawlers, or the network, and it must not download datasets.

## Maintenance UI

The maintenance evidence page exposes the gate through
`evaluateLegalRagRetrievalObservationGate` and a review panel titled
`Legal RAG retrieval observation gate`.

The panel includes:

- summary counts for ready, review, blocked, citation-gap, and top-k-gap rows
- retrieval status and release action distributions
- source-validation counts and per-row cheap-first action metadata
- the accepted input contract and ignored raw-text fields
- a sanitized sample payload editor for local maintainer review
- explicit privacy and claim boundary booleans

The UI path is review-only. It posts local metadata rows to the maintenance
endpoint and must not display source ids, raw query text, retrieved context,
raw legal text, prompts, model outputs, gateway payloads, credentials, emails,
or client material.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_rag_retrieval_observation_gate.py tests/test_legal_rag_selected_source_validation.py -q
python -m pytest tests/test_legal_rag_retrieval_observation_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
