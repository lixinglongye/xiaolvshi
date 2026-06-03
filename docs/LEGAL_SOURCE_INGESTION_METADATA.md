# Legal Source Ingestion Metadata

`LegalSourceIngestionMetadataService` defines a deterministic, local-only
contract for legal source records before they enter a retrieval corpus.

It sits next to `legal_source_freshness_policy` but does not modify it. The
service has no network calls, model calls, database writes, filesystem writes,
router integration, release gate integration, or ledger integration.

## Purpose

Legal retrieval needs a narrow metadata envelope before any source can be
indexed or cited. This service defines that envelope and evaluates sample source
records for:

- required source record fields
- jurisdiction metadata
- effective-date metadata
- citation metadata
- freshness metadata
- local dedupe keys
- forbidden fields
- sample record readiness

## Source Record Schema

Required fields:

- `id`: stable local source identifier
- `title`: reviewer-readable source title
- `source_type`: `statute`, `regulation`, `judicial_interpretation`, `case`, `template`, or `internal_note`
- `jurisdiction`: retrieval and citation jurisdiction tag
- `effective_date`: legal effective date in `YYYY-MM-DD`
- `citation`: stable reviewer-checkable citation
- `last_verified_at`: local verification date in `YYYY-MM-DD`

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

## Jurisdiction Fields

`jurisdiction` is required and must be one of the supported local tags:

- `CN`
- `CN-National`
- `CN-Beijing`
- `CN-Shanghai`
- `CN-Guangdong`
- `CN-Zhejiang`
- `CN-Jiangsu`

Unsupported or missing jurisdiction metadata blocks ingestion because it can
cause cross-jurisdiction citation drift.

## Effective Date Fields

`effective_date` is required. `publication_date` and `amendment_date` are
optional. All date fields use ISO `YYYY-MM-DD`.

Future effective dates block ingestion as active sources. Invalid date formats
also block ingestion because downstream freshness and citation checks need a
stable date boundary.

## Citation Fields

`citation` is required and should be stable enough for a legal reviewer to trace
the source. `official_url` and `retrieval_locator` are optional locators. The
service does not fetch URLs or inspect locator targets.

Weak citations produce a warning; missing citations block ingestion.

## Freshness Fields

`last_verified_at` and `source_type` anchor the local freshness snapshot. The
service calculates:

- `status`: `fresh`, `review_due`, `stale`, or `unknown`
- `window_days`
- `warning_after_days`
- `days_since_last_verified`
- `next_review_due_at`
- `policy_ref`: `legal_source_freshness_policy`

Freshness windows mirror the adjacent policy contract:

- `statute`: 365 days
- `regulation`: 365 days
- `judicial_interpretation`: 365 days
- `case`: 730 days
- `template`: 365 days
- `internal_note`: 180 days

## Dedupe Keys

The service computes local dedupe keys without storing raw legal source text:

- `citation_key`: `source_type`, `jurisdiction`, `citation`
- `effective_title_key`: `source_type`, `jurisdiction`, `title`, `effective_date`
- `issuer_title_key`: `source_type`, `jurisdiction`, `issuer`, `title`
- `content_hash_key`: `content_hash`

Duplicate source IDs or duplicate dedupe keys block ingestion until a canonical
record is selected.

## Forbidden Fields

The metadata envelope must not contain raw source bodies, private matter data,
prompts, model responses, credentials, or client identifiers.

Forbidden fields include:

- `raw_text`
- `full_text`
- `document_body`
- `html`
- `pdf_bytes`
- `base64_pdf`
- `ocr_text`
- `client_name`
- `client_email`
- `phone`
- `personal_id`
- `case_number`
- `matter_id`
- `prompt`
- `model_response`
- `authorization`
- `api_key`
- `password`

Secret-like values and email-like values are redacted before the service returns
evaluation output.

## Sample Source Records

`build_metadata_contract()` returns three synthetic sample records:

- a ready national statute metadata record
- a local regulation record that is due for freshness review
- a template metadata record intentionally missing `citation`

The default sample evaluation is therefore `blocked`. This is intentional: it
shows pass, warning, and blocking states in one local contract payload.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_legal_source_ingestion_metadata.py -q
python -m compileall services/legal_source_ingestion_metadata.py
```

The service is ready for later integration by router, release, or ledger work,
but this slice intentionally does not modify those surfaces.
