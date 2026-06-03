# Legal Source Durable Index Plan

`LegalSourceDurableIndexPlanService` defines a deterministic, local-only plan
for materializing legal source metadata into durable index entries.

This slice does not connect to a database, vector store, network fetcher,
router, release gate, or ledger. It also does not modify the existing ingestion
metadata or freshness services.

## Purpose

Legal retrieval needs a durable index contract before a storage backend is
introduced. This service keeps that contract metadata-only and validates that
future index entries can be rebuilt from source metadata without copying raw
legal text or private matter data.

The plan covers:

- metadata-only source record inputs
- durable index entry schema
- jurisdiction, effective-date, citation, freshness, and dedupe fields
- metadata query filters
- retention and rebuild policy
- forbidden raw text and runtime fields
- sample index entry validation

## Source Record Input

Source records are accepted only as metadata. Required fields:

- `id`
- `title`
- `source_type`
- `jurisdiction`
- `effective_date`
- `citation`
- `last_verified_at`

Optional metadata fields:

- `authority_level`
- `issuer`
- `publication_date`
- `amendment_date`
- `official_url`
- `retrieval_locator`
- `content_hash`
- `use_case`
- `ingestion_batch_id`

These records are normalized into durable index entries. Raw source bodies,
chunks, embeddings, prompts, model outputs, client identifiers, and credentials
are rejected.

## Index Entry Schema

Required durable index entry fields:

- `index_entry_id`: stable entry id for a specific source metadata version
- `source_id`: stable local source id
- `title`: reviewer-readable metadata title, not the raw source body
- `source_type`: source class used for freshness windows
- `jurisdiction`: query and citation jurisdiction tag
- `effective_date`: legal effective date in `YYYY-MM-DD`
- `citation`: reviewer-checkable citation
- `last_verified_at`: local verification date in `YYYY-MM-DD`
- `freshness_status`: `fresh`, `review_due`, `stale`, or `unknown`
- `freshness_expires_at`: computed next review boundary
- `dedupe_key`: canonical dedupe selector
- `metadata_hash`: hash of metadata-only source fields
- `index_version`: local index schema version

Optional fields include issuer, authority level, publication/amendment dates,
official locator, local retrieval locator, content hash, use case, batch id,
indexed date, retention bucket, and dedupe helper keys.

## Field Groups

Jurisdiction:

- `jurisdiction` is required and must be one of the supported local tags:
  `CN`, `CN-National`, `CN-Beijing`, `CN-Shanghai`, `CN-Guangdong`,
  `CN-Zhejiang`, or `CN-Jiangsu`.

Effective date:

- `effective_date` is required.
- `publication_date` and `amendment_date` are optional metadata.
- Future effective dates are blocked from active indexing.

Citation:

- `citation` is required for reviewer traceability.
- `official_url` is a manual locator only; the service never fetches it.
- `retrieval_locator` is a local pointer and must not contain source text.

Freshness:

- `last_verified_at` and `source_type` determine freshness.
- Active query values are `fresh` and `review_due`.
- `stale` entries are retained only for audit or rebuild review and are
  excluded from active retrieval.

Dedupe:

- `citation_key`: `source_type`, `jurisdiction`, `citation`
- `effective_title_key`: `source_type`, `jurisdiction`, `title`,
  `effective_date`
- `content_hash_key`: `content_hash`
- `dedupe_key`: selected from the dedupe helper keys
- `metadata_hash`: deterministic hash for incremental rebuild diffing

## Query Filters

The durable index plan allows metadata filters only:

- `jurisdiction`
- `source_type`
- `effective_on_or_before`
- `citation`
- `freshness_status`
- `last_verified_at_min`
- `authority_level`
- `issuer`
- `use_case`
- `index_version`
- `retention_bucket`

Raw text search filters, vector similarity filters, prompt filters, client data
filters, and credential-bearing filters are forbidden in this service.

## Retention Policy

- Raw text retention: never store.
- Active metadata entries: retain while the source remains supported and fresh.
- Review-due metadata entries: retain but mark review-required.
- Stale metadata entries: exclude from active retrieval and keep 180 days for
  rebuild audit.
- Superseded metadata versions: keep 400 days for release diff and rollback.
- Dedupe tombstones: keep 730 days to prevent duplicate reintroduction.
- Rejected entries: delete immediately after the validation report.

## Rebuild Policy

Rebuilds are deterministic and local. Inputs are metadata-only source records,
schema constants, and the reference date.

Full rebuild triggers:

- schema version change
- index version change
- jurisdiction taxonomy change
- source-type freshness window change
- dedupe algorithm change
- forbidden-field policy change

Incremental rebuild triggers:

- `metadata_hash` changed
- `last_verified_at` changed
- `citation` changed
- `effective_date` changed
- `content_hash` changed
- `retention_bucket` changed

No database, vector store, network service, model call, router, release gate, or
ledger is required by this service.

## Forbidden Fields

Forbidden raw text and vector fields include:

- `raw_text`
- `full_text`
- `document_body`
- `source_body`
- `law_text`
- `article_text`
- `text`
- `body`
- `content`
- `html`
- `markdown`
- `pdf_bytes`
- `base64_pdf`
- `ocr_text`
- `chunk_text`
- `chunk_body`
- `excerpt`
- `snippet`
- `embedding`
- `embedding_vector`
- `vector`
- `dense_vector`
- `sparse_vector`

Forbidden private or runtime fields include client identifiers, personal IDs,
matter IDs, prompts, model outputs, request and response bodies, headers,
authorization values, API keys, passwords, secrets, and tokens.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_legal_source_durable_index_plan.py -q
python -m compileall services/legal_source_durable_index_plan.py
```

The service is ready for later integration work, but this implementation
intentionally stops at a pure local plan and validator.
