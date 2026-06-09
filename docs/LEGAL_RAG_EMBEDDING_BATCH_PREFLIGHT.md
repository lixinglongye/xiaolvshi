# Legal RAG Embedding Batch Preflight

`POST /api/v1/legal-rag/embedding-batch-preflight` is a local, metadata-only input audit before `POST /api/v1/legal-rag/embedding-batch-preview`.

The preflight inspects `chunks` without calling NewAPI, Gemini, AIHub, models, gateways, or the network. It is designed for low-resource maintainer checks before any executable embedding smoke test.

## Request Shape

```json
{
  "model": "auto-embedding",
  "chunks": [
    {
      "chunk_id": "local-source-row-1",
      "text": "Text to audit locally before preview."
    }
  ]
}
```

Accepted chunk text fields are `text`, `chunk_text`, and `content`. Accepted identifier fields are `chunk_id`, `id`, and `source_id`; identifiers are hashed and are never echoed.

## Response Boundary

The response returns only local metadata:

- chunk and text hashes
- character and estimated token counts
- local catalog cost estimate when available
- duplicate text-hash flags
- PII signal counts and types
- secret-like input blockers
- preview eligibility and release actions

The response does not return source text, source ids, sensitive values, prompts, model outputs, gateway payloads, credentials, or embedding vectors. It does not create embeddings, write indexes, or write database records.

## Validation

```bash
python -m pytest tests/test_legal_rag_embedding_batch_preflight.py tests/test_legal_rag_embedding_batch_preview.py tests/test_legal_rag_router.py -q
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q
```

Use this preflight before the executable embedding preview when reviewing legal RAG source chunks on a low-resource machine.
