# Legal RAG Embedding Readiness Gate

`GET /api/v1/maintenance/legal-rag-embedding-readiness-gate`

This endpoint exposes metadata-only review evidence that links Gemini embedding
cheap-first defaults to Legal RAG index coverage and retrieval diagnostics.

## Purpose

The gate answers a narrow release-readiness question: can the project review
text-only Legal RAG embedding routes before any durable index write, while still
blocking or escalating unsafe gaps?

It joins:

- `modelops-gemini-embedding-cheap-first-preflight`
- `legal-rag-index-coverage-gate`
- `legal-rag-retrieval-diagnostics-gate`
- the local `legal-rag-index-binding` contract

The default text embedding route uses `gemini-embedding-001`. Multimodal
`gemini-embedding-2` remains explicit-review before image, audio, video, PDF,
or evidence-index claims.

## Evaluation

Rows become:

- `ready`: text-only embedding preflight can be reviewed with the cheap Gemini
  default and metadata-only Legal RAG index/retrieval linkage.
- `review_required`: multimodal embedding or other explicit-review routes need
  operator review before route/default claims.
- `blocked`: empty or blocked index coverage, missing locators, or forbidden
  filters block embedding index writes.

The gate does not create embeddings, query an index, write an index, or improve
retrieval by itself. It only makes the embedding readiness boundary visible.

## Metadata Boundary

The response may include only model IDs, route labels, input scopes, status
counts, release actions, reason codes, linked gate IDs, checks, policy metadata,
input-contract metadata, and privacy or claim boundary booleans.

It must not return source IDs, raw query text, user questions, retrieved
context, raw legal text, source chunks, embedding vectors, prompts, model
outputs, gateway payloads, account data, credentials, client material, or
emails.

## Maintenance UI

The maintenance evidence page exposes the gate through
`getLegalRagEmbeddingReadinessGate` and a panel titled
`Legal RAG embedding readiness gate`.

The panel shows:

- readiness row counts and the embedding default model
- text embedding ready counts and multimodal review counts
- index blocker linkage and retrieval diagnostics linkage
- readiness rows with default model, input scope, release action, and reason
  codes
- status and release-action distributions
- linked-gate status, readiness policy, and input contract
- claim and privacy boundaries, including no embedding vectors and no index
  writes
- validation commands

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_rag_embedding_readiness_gate.py tests/test_model_ops_gemini_embedding_cheap_first_preflight.py tests/test_legal_rag_index_coverage_gate.py tests/test_legal_rag_retrieval_diagnostics_gate.py -q
python -m pytest tests/test_legal_rag_embedding_readiness_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
