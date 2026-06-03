# Document Delivery Package Manifest

`DocumentDeliveryPackageManifestService` defines a deterministic local manifest check for final legal-document delivery packages.

The service evaluates metadata only. It does not open exported files, inspect uploaded documents, call models, run OCR, read credentials, or use network services. The main thread can later expose it through routers or release workflows without changing the service contract.

## Service

- File: `app/backend/services/document_delivery_package_manifest.py`
- Class: `DocumentDeliveryPackageManifestService`
- Entry point: `build_manifest(payload: dict | None = None) -> dict`
- Status values: `template`, `blocked`, or `ready`

## Output Contract

The response always includes:

- `status`: overall manifest result.
- `summary`: section counts, risk counts, document count, supported export formats, and delivery readiness.
- `manifest_sections`: deterministic checks for package identity, included documents, source support, missing facts, lawyer review, client transparency notice, export formats, and version notes.
- `risk_flags`: blocking risk codes grouped by manifest section.
- `recommended_actions`: reviewer or product actions needed before delivery.
- `privacy_note`: metadata-only integration rule.
- `validation_commands`: local pytest and compile commands.

## Required Payload Areas

Use redacted IDs and metadata only:

```json
{
  "package": {
    "package_id": "package-001",
    "case_id": "case-001",
    "current_version_id": "version-002",
    "delivery_channel": "client_portal"
  },
  "documents": [
    {
      "document_id": "doc-001",
      "document_type": "complaint",
      "version_id": "version-002",
      "export_formats": ["pdf", "docx"],
      "checksum": "sha256:<redacted>"
    }
  ],
  "source_support": {
    "status": "complete",
    "citation_count": 4,
    "unsupported_claim_count": 0,
    "evidence_links": ["evidence-001"]
  },
  "missing_facts": {
    "status": "resolved",
    "items": []
  },
  "lawyer_review": {
    "status": "approved",
    "reviewer_id": "lawyer-001",
    "reviewed_at": "2026-06-04T08:00:00Z",
    "reviewed_version_id": "version-002"
  },
  "client_transparency": {
    "notice_present": true,
    "client_visible": true,
    "risk_notice_included": true,
    "scope_limits_included": true
  },
  "export": {
    "formats": ["pdf", "docx"],
    "final_format": "pdf",
    "version_locked": true
  },
  "version_notes": {
    "current_version_id": "version-002",
    "previous_version_id": "version-001",
    "summary_present": true,
    "generated_at": "2026-06-04T08:05:00Z"
  }
}
```

## Manifest Sections

- `package-identity`: package ID, case ID, current version, and delivery channel.
- `documents`: final legal document rows with ID, type, reviewed version, and export format metadata.
- `source-support`: citation or evidence support, source count, and unsupported-claim count.
- `missing-facts`: missing-fact register status and item list, including an empty list when no gaps remain.
- `lawyer-review`: responsible-lawyer approval for the exact package version.
- `client-transparency-notice`: client-visible notice containing risk and scope-limit context.
- `export-formats`: supported output formats and reviewed-version lock.
- `version-notes`: current-version notes and generated change summary.

## Blocking Behavior

The manifest is `blocked` when any required section is missing, incomplete, or inconsistent. Common blocking risks include:

- No deliverable legal document rows.
- Missing or incomplete source support.
- Unsupported claims.
- Unresolved missing facts.
- Lawyer review pending or tied to the wrong version.
- Hidden or incomplete client transparency notice.
- Unsupported export format.
- Export version not locked.
- Version notes missing or mismatched.

The manifest is `ready` only when every section passes and `risk_flags` is empty.

## Privacy

Do not send raw legal text, private party details, client contact details, local file paths, private notes, model outputs, API keys, or login credentials to this service. Keep sensitive matter data in protected case storage and pass only stable IDs, status labels, booleans, counts, timestamps, format names, version IDs, and checksum labels.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_document_delivery_package_manifest.py -q
python -m compileall services/document_delivery_package_manifest.py
```
