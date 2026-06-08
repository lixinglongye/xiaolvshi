# Legal RAG Embedding Retrieval Diagnostics Handoff Gate

`legal-rag-embedding-retrieval-diagnostics-handoff-gate` adds a
metadata-only handoff gate between embedding index post-commit verification
and retrieval diagnostics review.

## Endpoint

- `GET /api/v1/maintenance/legal-rag-embedding-retrieval-diagnostics-handoff-gate`
- `POST /api/v1/maintenance/legal-rag-embedding-retrieval-diagnostics-handoff-gate`

The POST body may provide upstream `source_rows`, `sources`, `records`, or
`metadata_rows` plus sanitized observation containers, or it may provide
already-built `verification_rows`, `handoff_source_rows`, `verification_gate`,
or `post_commit_verification_gate` metadata. Direct verification rows are used
as verification metadata and are not reinterpreted as raw post-commit
observations.

## What It Provides

- Ready, hold, and blocked handoff rows linked to post-commit verification
  rows.
- Safe handoff payload field lists for downstream retrieval diagnostics
  review packets.
- Diagnostics-review-only actions and rollback-review links.
- Production retrieval false flags at both row and gate level.
- Input-contract and claim/privacy boundary evidence for the maintenance UI.

## Ready Rules

A row is ready for retrieval diagnostics handoff only when the post-commit
verification row is verified, failed-entry count is zero, rollback is not
required, and index-entry, metadata-record, retrieval-locator, and checksum
counts are present. Review and blocked rows take precedence at gate level.

Ready handoff rows may be referenced by retrieval diagnostics review. They are
not production retrieval enablement and are not proof of retrieval quality.

## Boundaries

This gate does not execute retrieval diagnostics. It does not enable production
retrieval, claim index or retrieval quality, execute embeddings, call NewAPI,
Gemini, OpenAI, Google, gateways, app AI endpoints, models, indexes,
databases, or the network. It does not write indexes, databases, or commit
records, download datasets, change defaults, shift traffic, or provide legal
advice.

It also does not return source ids, approval item ids, raw query text, user
questions, retrieved context, raw legal text, source chunks, embedding vectors,
prompts, model outputs, gateway payloads, credentials, emails, committer
identity, live pricing claims, provider execution claims, or client delivery
claims.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_rag_embedding_retrieval_diagnostics_handoff_gate.py tests/test_legal_rag_embedding_index_post_commit_verification_gate.py -q
python -m pytest tests/test_legal_rag_embedding_retrieval_diagnostics_handoff_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```
