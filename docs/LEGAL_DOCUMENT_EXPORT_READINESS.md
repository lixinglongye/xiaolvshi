# Legal Document Export Readiness

This service evaluates whether a generated legal document can move from draft to final export.

## Endpoints

```http
GET /api/v1/maintenance/legal-document-export-readiness
POST /api/v1/maintenance/legal-document-export-readiness
```

The `GET` endpoint returns the export gate template. The `POST` endpoint accepts status metadata and returns:

- `status`: `template`, `blocked`, or `ready`.
- `format_gate`: whether the requested export format is supported.
- `gates`: required fields, blocker clearance, lawyer review, source support, redaction, and version-lock checks.
- `blocking_items`: reviewer-facing reasons final export is blocked.
- `audit_record_requirements`: fields to retain for reviewed-version and delivery traceability.

## Product Gap Covered

The document generator should not export client-facing or filing-ready files just because a draft exists. Export must be blocked until the template matrix, lawyer review, source support, redaction, and version-lock gates pass.

## Safety Policy

The readiness payload stores booleans, status labels, version IDs, and format names only. It must not store raw legal text, party identifiers, full attachments, model outputs, API keys, login credentials, or user contact details.

## Related Files

- `app/backend/services/legal_document_export_readiness.py`
- `app/backend/tests/test_legal_document_export_readiness.py`
- `app/backend/services/legal_document_template_matrix.py`
- `app/backend/services/client_delivery_risk_checklist.py`
- `docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md`
- `docs/CLIENT_DELIVERY_RISK_CHECKLIST.md`
