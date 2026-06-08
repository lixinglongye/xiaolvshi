# Legal RAG Embedding Chunk Policy Gate

`GET /api/v1/maintenance/legal-rag-embedding-chunk-policy-gate`

`POST /api/v1/maintenance/legal-rag-embedding-chunk-policy-gate`

`LegalRagEmbeddingChunkPolicyGateService` exposes metadata-only chunk planning
evidence for Legal RAG before any cheap embedding preflight can be used for
source-index work.

## Purpose

The gate answers a narrow release-readiness question: can the project review
source chunking policy from safe metadata before using the default cheap text
embedding route, while still blocking unsafe source metadata?

The default cheap embedding model remains `gemini-embedding-001`. This gate
only plans chunk policy rows; it does not create embeddings, write an index, or
prove retrieval quality.

It joins:

- `modelops-gemini-embedding-cheap-first-preflight`
- `legal-rag-embedding-readiness-gate`
- `legal-rag-index-coverage-gate`
- `legal-rag-retrieval-diagnostics-gate`
- `legal-source-durable-index-plan`
- `legal-source-ingestion-metadata`

## Chunk Planning Policy

Rows are evaluated from metadata fields such as source type, jurisdiction,
freshness status, estimated token count, section count, citation-anchor count,
retrieval-locator presence, language, and authority level.

The built-in target policy is:

- `statute`, `regulation`, and `judicial_interpretation`: 512 target tokens,
  64 overlap tokens, split at article or section boundaries.
- `case`: 640 target tokens, 80 overlap tokens, split at issue, fact, or
  holding boundaries.
- `template`: 384 target tokens, 48 overlap tokens, split at clause or field
  boundaries.
- `internal_note`: 256 target tokens, 32 overlap tokens, split at heading or
  bullet boundaries.

The laptop-safe planning limit is 12 planned chunks per source. The gate may
flag rows that exceed that limit, but it still remains a local metadata review
surface.

## Evaluation

Rows become:

- `ready`: source metadata has a supported source type and jurisdiction, fresh
  status, positive token estimate, retrieval locator, citation anchor, and no
  forbidden or sensitive fields.
- `review_required`: source metadata can be planned but needs reviewer attention
  for citation-anchor gaps, review-due freshness, or laptop-safe chunk limits.
- `blocked`: unknown source type, unsupported jurisdiction, empty token
  estimate, missing retrieval locator, stale or unknown freshness, forbidden
  fields, or sensitive values block embedding chunking.

The release actions are metadata labels only:

- `allow_embedding_chunk_preflight`
- `review_embedding_chunk_policy`
- `block_embedding_chunking`

## Metadata Boundary

The response may include only policy row IDs, source-type labels, jurisdiction
status, freshness status, token estimates, section and citation-anchor counts,
retrieval-locator status, planned chunk counts, overlap sizes, split strategies,
status counts, release actions, reason codes, linked gate IDs, validation
commands, and privacy or claim boundary booleans.

It must not return source ids, raw query text, user questions, retrieved
context, raw legal text, source chunks, source chunk text, embedding vectors,
prompts, model outputs, gateway payloads, account data, credentials, client
material, or emails.

The gate must not call NewAPI, Gemini, models, gateways, app AI endpoints, or
the network. It must not create embeddings, write indexes, download datasets,
write configuration, change defaults, or shift traffic.

## Input Contract

Accepted source-row fields are metadata only:

- `source_type`
- `jurisdiction`
- `freshness_status`
- `estimated_token_count`
- `section_count`
- `citation_anchor_count`
- `retrieval_locator_present`
- `language`
- `authority_level`

Forbidden or sensitive fields are detected for blocker metadata and are not
echoed as values. Examples include raw text fields, source IDs, document IDs,
client ids, source chunks, chunk text, embeddings, embedding vectors, request
or response bodies, prompts, model outputs, gateway payloads, API keys,
passwords, bearer tokens, credentials, and emails.

## Maintenance UI

The maintenance evidence page should expose the gate as
`Legal RAG embedding chunk policy gate`.

The panel should show:

- source-row counts, planned chunk totals, and the default model
  `gemini-embedding-001`
- ready, review-required, and blocked row counts
- source-type split strategies, target chunk sizes, overlap sizes, and
  laptop-safe chunk-limit status
- citation-anchor, retrieval-locator, freshness, forbidden-field, and
  sensitive-value blockers
- linked-gate statuses for embedding readiness, index coverage, retrieval
  diagnostics, durable index planning, and ingestion metadata
- claim and privacy boundaries, including no source ids, raw legal text, source
  chunks, embedding vectors, credentials, provider calls, embedding creation, or
  index writes
- validation commands

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_rag_embedding_chunk_policy_gate.py tests/test_legal_rag_embedding_readiness_gate.py tests/test_legal_source_durable_index_plan.py -q
python -m pytest tests/test_legal_rag_embedding_chunk_policy_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
