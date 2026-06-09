# Legal RAG Embedding Batch Preview

`legal-rag-embedding-batch-preview-runtime` adds a maintainer-only executable
smoke-test route for Legal RAG embeddings:

`POST /api/v1/legal-rag/embedding-batch-preview`

Run `POST /api/v1/legal-rag/embedding-batch-preflight` first to locally audit
chunk size, duplicate hashes, PII signals, and secret-like input blockers
without calling the embedding gateway.

The route accepts up to five small text chunks, calls the existing AIHub
embedding runtime, and returns sanitized preview metadata only. It is designed
for laptop-safe checks before any durable vector index work.

## Runtime Boundary

- Uses `AIHubService.embed_text`.
- Routes through the configured cheap-first embedding model, normally
  `gemini-embedding-001`.
- Uses the OpenAI-compatible `embeddings.create` shape supported by Gemini API
  compatibility docs.
- Returns vector dimensions, L2 norms, vector checksums, text hashes, usage
  units, route metadata, and budget metadata.
- Does not write the Legal RAG index or database.
- Does not return source text, source ids, raw legal text, prompts, gateway
  payloads, model outputs, credentials, or embedding vectors.

## Request Shape

```json
{
  "chunks": [
    { "chunk_id": "local-maintainer-id-1", "text": "small legal source chunk" }
  ],
  "model": "auto-embedding"
}
```

`chunk_id` and text are hashed before response metadata is returned.

## Validation

```powershell
python -m pytest tests/test_legal_rag_embedding_batch_preview.py tests/test_legal_rag_router.py tests/test_aihub_runtime_routing.py -q
python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q
```

## Source Anchors

- Gemini embeddings: https://ai.google.dev/gemini-api/docs/embeddings
- Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
