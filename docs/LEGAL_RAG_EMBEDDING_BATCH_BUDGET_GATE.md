# Legal RAG Embedding Batch Budget Gate

`legal-rag-embedding-batch-budget-gate` adds a metadata-only batch budget
review step between the embedding index dry-run manifest and any live embedding
run. It is built for low-resource local validation and cheap-first Gemini
embedding defaults.

## Endpoint

- `GET /api/v1/maintenance/legal-rag-embedding-batch-budget-gate`
- `POST /api/v1/maintenance/legal-rag-embedding-batch-budget-gate`

The POST body may provide `source_rows`, `sources`, `records`, or
`metadata_rows`. Only safe source metadata is used. Forbidden raw legal text,
source ids, source chunks, embedding vectors, credentials, gateway payloads,
prompts, model outputs, and emails are ignored and not echoed.

## What It Checks

- Converts dry-run manifest rows into batch budget rows.
- Keeps text embedding on `gemini-embedding-001`.
- Uses the local Gemini embedding cheap-first preflight batch price estimate.
- Computes planned batch counts, token totals, estimated cost, and per-batch
  laptop-safe limits.
- Blocks rows inherited from blocked dry-run rows.
- Requires review for review-only dry-run rows or rows that need local batch
  splitting.

## Boundaries

This gate does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, indexes, databases, or the network. It does not create
embeddings, write vector indexes, write databases, download datasets, change
defaults, or shift traffic.

It also does not claim live pricing accuracy, embedding quality, retrieval
quality, index quality, legal advice quality, or that any batch has been
executed.

## Validation

```bash
python -m pytest tests/test_legal_rag_embedding_batch_budget_gate.py tests/test_legal_rag_embedding_index_dry_run_gate.py tests/test_model_ops_gemini_embedding_cheap_first_preflight.py -q
python -m pytest tests/test_legal_rag_embedding_batch_budget_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q
cd app/frontend && npm run typecheck && npm run ui:regression
```
