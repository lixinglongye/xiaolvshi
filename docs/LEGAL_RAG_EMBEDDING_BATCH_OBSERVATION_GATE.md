# Legal RAG Embedding Batch Observation Gate

`legal-rag-embedding-batch-observation-gate` adds metadata-only aggregate
observation review after the embedding batch approval packet and before any
index-commit review.

Ready observations are reviewed separately by
`legal-rag-embedding-index-commit-review-packet`; this gate itself never writes
an index or records commit approval.

## Endpoint

- `GET /api/v1/maintenance/legal-rag-embedding-batch-observation-gate`
- `POST /api/v1/maintenance/legal-rag-embedding-batch-observation-gate`

The POST body may provide `source_rows`, `sources`, `records`, or
`metadata_rows` plus `observations`, `embedding_observations`,
`batch_observations`, `observation_rows`, or `rows`. Inputs are reduced to
safe metadata and aggregate counts only.

## What It Provides

- Observed batch, chunk, vector-slot, token, and cost totals.
- Expected-vs-observed deltas for approved queue rows.
- `max_parallel_embedding_requests=1` carried forward from approval evidence.
- Review actions: `allow_index_commit_review_only`,
  `hold_for_observation_review`, and `block_index_commit`.
- A typed maintenance API helper and maintenance UI panel for reviewer evidence.

## Boundaries

This gate does not run embeddings. It does not claim maintainer approval,
collect approver identity, write approval records, call NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, models, indexes, databases, or the
network. It does not create embeddings, write vector indexes, write databases,
download datasets, change defaults, shift traffic, or claim live pricing
accuracy.

It also does not return source ids, approval item ids, raw query text, retrieved
context, raw legal text, source chunks, embedding vectors, prompts, model
outputs, gateway payloads, credentials, emails, legal advice quality, retrieval
quality, embedding quality, index quality, provider execution, or client
delivery.

## Validation

```bash
python -m pytest tests/test_legal_rag_embedding_batch_observation_gate.py tests/test_legal_rag_embedding_batch_approval_packet.py -q
python -m pytest tests/test_legal_rag_embedding_batch_observation_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
