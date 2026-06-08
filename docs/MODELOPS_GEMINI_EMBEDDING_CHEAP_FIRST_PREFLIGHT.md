# ModelOps Gemini Embedding Cheap-First Preflight

`modelops-gemini-embedding-cheap-first-preflight` records metadata-only release
evidence for Gemini embedding defaults before any embedding route is used for
retrieval, deduping, or source-index work.

## Scope

- Default text embedding model: `APP_AI_EMBEDDING_MODEL=gemini-embedding-001`.
- Routing alias: `auto-embedding` resolves through the local catalog and budget
  policy, not through a live provider call.
- Catalog coverage: `gemini-embedding-001` is the cheap-first text embedding
  default; `gemini-embedding-2` is tracked as the multimodal embedding review
  candidate.
- Review boundary: multimodal `gemini-embedding-2` remains review-required
  before image, audio, video, PDF, or source-index use.
- Endpoint: `/api/v1/aihub/models/gemini-embedding-cheap-first-preflight`.
- Aggregate key: `gemini_embedding_cheap_first_preflight`.

## Non-Claims

This preflight is metadata-only. It does not call NewAPI, Gemini, OpenAI,
Google, gateways, app AI endpoints, models, or the network. It does not write
configuration, change defaults, write indexes, shift traffic, or return source
text, raw legal text, source chunks, embedding vectors, request bodies, response
bodies, headers, prompts, raw payloads, model outputs, gateway responses,
credentials, emails, or user identifiers.

## Release Evidence

The required release check id is
`modelops-gemini-embedding-cheap-first-preflight`. It links the backend
preflight service, local catalog and budget policy, ModelOps readiness,
continuous update ledger, frontend source-contract evidence, and this document.

Suggested focused validation:

```powershell
cd app/backend
python -m pytest tests/test_model_ops_gemini_embedding_cheap_first_preflight.py tests/test_model_catalog.py tests/test_model_budget.py tests/test_model_configuration_audit.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
