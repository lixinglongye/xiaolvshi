# Case Evidence Catalog Export Preflight

`CaseEvidenceCatalogExportPreflightService` connects two existing evidence
quality gates to case evidence-catalog generation:

- `EvidenceExhibitPackagePolicyService` for exhibit numbering, attachment
  numbering, page anchors, proof purpose, source anchors, and three-factor
  review metadata.
- `EvidenceBundleIntegrityService` for duplicate groups, missing sources,
  missing proof purposes, date/amount/checksum gaps, and privacy flags.

The preflight is attached to `CaseDraftingService.generate_evidence_catalog`.
It does not stop draft generation, because lawyers may still need a working
draft while evidence metadata is incomplete. It does block final export by
returning `export_allowed: false` when package policy or bundle integrity checks
are blocked.

## Boundary

The service is deterministic and metadata-only:

- no uploaded files are read,
- no OCR is run,
- no model or gateway is called,
- no attachment bundle is created,
- no checksum is verified against file storage,
- no lawyer review is marked complete,
- raw evidence names, raw document text, file names, PII, credentials, and
  original row payloads are not returned by the preflight object.

The generated document can still include its existing evidence-catalog rows.
The preflight object is only the export gate summary and should remain
privacy-safe.

## Focused Checks

Run from `app/backend`:

```powershell
python -m pytest tests/test_case_evidence_catalog_export_preflight.py tests/test_case_generation_quota.py -q
python -m py_compile services/case_evidence_catalog_export_preflight.py services/case_intelligence.py
```

The next product step is frontend integration: show this preflight before a user
downloads or externally delivers an evidence catalog, while still allowing
internal draft review.
