# Legal RAG Embedding Batch Approval Packet

`legal-rag-embedding-batch-approval-packet` adds a metadata-only maintainer
review packet after the embedding batch budget gate and before any live Gemini
embedding run.

After an external low-resource embedding run, aggregate observations are
reviewed separately by `legal-rag-embedding-batch-observation-gate`; this packet
itself never records run results or index-commit decisions.

## Endpoint

- `GET /api/v1/maintenance/legal-rag-embedding-batch-approval-packet`
- `POST /api/v1/maintenance/legal-rag-embedding-batch-approval-packet`

The POST body may provide `source_rows`, `sources`, `records`, or
`metadata_rows`. Inputs are reduced to safe source metadata. Source ids, raw
legal text, source chunks, embedding vectors, credentials, gateway payloads,
prompts, model outputs, emails, and approver identities are not returned.

## What It Provides

- Serial low-resource queue order for reviewed embedding batches.
- `max_parallel_embedding_requests=1`.
- Required signoff roles for ready rows: `maintainer_owner` and
  `rag_index_reviewer`.
- Hold/block actions for review-required or blocked budget rows.
- Pre-approval checks that must be completed outside the service.
- Release actions such as `advance_next_embedding_batch_review_only`,
  `hold_embedding_batch_for_review`, and `block_embedding_run`.

## Boundaries

This packet does not approve a batch. It does not collect approver identity,
write approval records, call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, indexes, databases, or the network. It does not create
embeddings, write vector indexes, write databases, download datasets, change
defaults, shift traffic, or claim live pricing accuracy.

It also does not claim legal advice quality, retrieval quality, embedding
quality, index quality, vector-store quality, provider execution, or client
delivery.

## Validation

```bash
python -m pytest tests/test_legal_rag_embedding_batch_approval_packet.py tests/test_legal_rag_embedding_batch_budget_gate.py -q
python -m pytest tests/test_legal_rag_embedding_batch_approval_packet.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
