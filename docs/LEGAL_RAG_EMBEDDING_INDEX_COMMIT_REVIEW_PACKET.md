# Legal RAG Embedding Index Commit Review Packet

`legal-rag-embedding-index-commit-review-packet` adds a metadata-only maintainer
review packet after aggregate embedding batch observations and before any real
embedding index commit.

## Endpoint

- `GET /api/v1/maintenance/legal-rag-embedding-index-commit-review-packet`
- `POST /api/v1/maintenance/legal-rag-embedding-index-commit-review-packet`

The POST body may provide `source_rows`, `sources`, `records`, or
`metadata_rows` plus `observations`, `embedding_observations`,
`batch_observations`, `observation_rows`, or `rows`. Inputs are reduced to
safe metadata and aggregate observation counts only.

## What It Provides

- Commit-review items derived from ready aggregate observation rows.
- Vector-slot match evidence, observed chunk counts, and observed cost evidence.
- Required signoffs for ready rows: `maintainer_owner`, `rag_index_reviewer`,
  and `privacy_reviewer`.
- Pre-commit checks that must be completed outside this service.
- Review actions: `prepare_external_index_commit_review`,
  `hold_index_commit_for_observation_review`, and `block_index_commit`.

## Boundaries

This packet does not approve or commit an index. It does not collect committer
identity, write commit records, call NewAPI, Gemini, OpenAI, Google, gateways,
app AI endpoints, models, indexes, databases, or the network. It does not
create embeddings, write vector indexes, write databases, download datasets,
change defaults, shift traffic, or claim live pricing accuracy.

It also does not return source ids, approval item ids, raw query text, retrieved
context, raw legal text, source chunks, embedding vectors, prompts, model
outputs, gateway payloads, credentials, emails, legal advice quality, retrieval
quality, embedding quality, index quality, provider execution, or client
delivery.

## Validation

```bash
python -m pytest tests/test_legal_rag_embedding_index_commit_review_packet.py tests/test_legal_rag_embedding_batch_observation_gate.py -q
python -m pytest tests/test_legal_rag_embedding_index_commit_review_packet.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
