# Legal RAG Embedding Index Dry-Run Gate

`legal-rag-embedding-index-dry-run-gate` adds metadata-only review evidence
between chunk planning and any future embedding index write.

The gate is implemented by
`LegalRagEmbeddingIndexDryRunGateService` and exposed through:

- `GET /api/v1/maintenance/legal-rag-embedding-index-dry-run-gate`
- `POST /api/v1/maintenance/legal-rag-embedding-index-dry-run-gate`

The POST endpoint accepts metadata rows under `source_rows`, `sources`,
`records`, or `metadata_rows`. It does not accept or return source text,
source chunks, source ids, embedding vectors, prompts, model outputs, gateway
payloads, or credentials.

## Purpose

The previous embedding gates answer two separate questions:

- `legal-rag-embedding-readiness-gate`: whether the cheap Gemini embedding route
  can be reviewed before index use.
- `legal-rag-embedding-chunk-policy-gate`: whether metadata-only source rows can
  be chunk-planned safely.

This gate turns the chunk-policy rows into a dry-run manifest that reviewers can
inspect before any vector or durable metadata persistence is attempted. It adds:

- dry-run rows with `dry_run_status` and `commit_action`
- planned chunk and planned vector-slot counts
- durable index persistence-field visibility
- repository-validation linkage to `legal_source_index_repository`
- explicit blockers for chunk-policy failures
- a UI panel in the maintenance evidence page

## Safe Output

The service returns only metadata such as source type, status, chunk counts,
manifest fields, linked gate ids, and validation commands. It keeps:

- `creates_embeddings = false`
- `writes_index = false`
- `writes_database = false`
- `returns_source_ids = false`
- `returns_raw_legal_text = false`
- `returns_source_chunks = false`
- `returns_embedding_vectors = false`
- `network_called = false`

`gemini-embedding-001` is reported as the cheap default embedding model, but the
gate never calls Gemini, NewAPI, OpenAI, Google, a gateway, or any network
endpoint.

## Commit Actions

Rows use the following review-only commit actions:

- `allow_manifest_review_only`
- `review_before_index_manifest`
- `block_index_write`

These labels are intentionally not write instructions. They are release-review
states for maintainers.

## Validation

Run from `app/backend`:

```bash
python -m pytest tests/test_legal_rag_embedding_index_dry_run_gate.py tests/test_legal_rag_embedding_chunk_policy_gate.py tests/test_legal_source_durable_index_plan.py -q
```

Cross-gate validation:

```bash
python -m pytest tests/test_legal_rag_embedding_index_dry_run_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
```

Frontend validation from `app/frontend`:

```bash
npm run typecheck
npm run ui:regression
```
