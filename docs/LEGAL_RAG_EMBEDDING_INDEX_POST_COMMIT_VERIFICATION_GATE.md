# Legal RAG Embedding Index Post-Commit Verification Gate

`legal-rag-embedding-index-post-commit-verification-gate` adds a
metadata-only verification gate after the embedding index commit review packet
and before retrieval diagnostics review.

## Endpoint

- `GET /api/v1/maintenance/legal-rag-embedding-index-post-commit-verification-gate`
- `POST /api/v1/maintenance/legal-rag-embedding-index-post-commit-verification-gate`

The POST body may provide `source_rows`, `sources`, `records`, or
`metadata_rows` plus sanitized upstream embedding observations and
`post_commit_observations`, `commit_observations`, `verification_rows`, or
`post_commit_rows`. Nested `rows` containers are accepted for post-commit
observations. Inputs are reduced to aggregate metadata counts and status
signals only.

## What It Provides

- Verification rows linked to commit-review rows.
- Expected versus observed vector-slot and index-entry counts.
- Metadata-record, retrieval-locator, and checksum-record count review.
- Failed-entry totals and rollback-required signals.
- Review actions: `allow_retrieval_diagnostics_review_only`,
  `hold_for_post_commit_review`, `block_retrieval_use`, and
  `block_retrieval_use_and_prepare_rollback`.

## Ready Rules

A row is verified for retrieval diagnostics review only when the upstream
commit-review row is ready, a success-like post-commit observation is present,
rollback is not required, failed-entry count is zero, and vector-slot,
index-entry, metadata-record, retrieval-locator, and checksum counts match the
expected vector slots.

Review and blocked rows take precedence over ready rows at the gate level.
Verified rows are not production retrieval enablement.

Verified rows can feed
`legal-rag-embedding-retrieval-diagnostics-handoff-gate`, which converts them
into safe metadata-only handoff rows for retrieval diagnostics review. The
handoff gate still blocks production retrieval and keeps query text, retrieved
context, source chunks, vectors, source ids, and committer identity out of the
payload.

## Boundaries

This gate does not approve or execute an index commit. It does not collect
committer identity, write commit records, call NewAPI, Gemini, OpenAI, Google,
gateways, app AI endpoints, models, indexes, databases, or the network. It does
not create embeddings, write vector indexes, write databases, enable production
retrieval, download datasets, change defaults, shift traffic, or claim live
pricing accuracy.

It also does not return source ids, approval item ids, raw query text, retrieved
context, raw legal text, source chunks, embedding vectors, prompts, model
outputs, gateway payloads, credentials, emails, legal advice quality, retrieval
quality, embedding quality, index quality, provider execution, or client
delivery.

## Validation

```bash
python -m pytest tests/test_legal_rag_embedding_index_post_commit_verification_gate.py tests/test_legal_rag_embedding_index_commit_review_packet.py -q
python -m pytest tests/test_legal_rag_embedding_index_post_commit_verification_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
