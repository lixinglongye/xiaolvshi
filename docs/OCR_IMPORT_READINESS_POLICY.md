# OCR Import Readiness Policy

This service defines the backend-only policy surface for scanned documents, OCR routing, retry state, and manual review decisions.

## Product Gap

Legal uploads can include scanned PDFs, image-only pages, corrupted pages, and pages with weak or empty text layers. Without an explicit readiness policy, the product can look stalled or send poor input into downstream legal parsing.

`OcrImportReadinessPolicyService.build_policy(payload=None)` keeps that state visible and deterministic.

## Endpoints

```http
GET /api/v1/maintenance/ocr-import-readiness-policy
POST /api/v1/maintenance/ocr-import-readiness-policy
GET /api/v1/deep-review/analyze-uploaded/status/{document_id}
```

The `GET` endpoint returns the template. The `POST` endpoint accepts metadata from upload preflight and returns an import status, OCR detection signals, retry state, blocking conditions, manual review conditions, and next actions.

The deep-review uploaded-document status endpoint now returns `ocr_readiness`
alongside extraction metadata. The upload and review-progress UIs render that
status so users can see whether a scanned or low-text file is waiting for OCR,
completed OCR, needs manual review, or hit an OCR retry failure before legal
parsing continues.

## Status Enumeration

- `uploaded`: the file has been received but preflight has not completed.
- `preflight`: size, type, encryption, readability, and text-density checks are still being evaluated.
- `ocr_needed`: scanned pages, image-only pages, or low-text pages require OCR before parsing.
- `ocr_failed`: the latest OCR attempt failed but retry budget may remain.
- `parsed`: the document is ready for downstream legal parsing.
- `blocked`: import must stop until a corrected upload, support action, or reviewer decision exists.
- `manual_review`: OCR or parse readiness is ambiguous and needs a human reviewer.

## Detection Signals

The policy treats these as OCR readiness signals:

- `scan_detected` or `image_only` flags.
- Page-level `image_only=True`.
- Page-level `has_text_layer=False`.
- Page-level `text_char_count` below the low-text threshold.
- High ratio of low-text pages.
- Unreadable, corrupted, or unsupported pages.

The default low-text threshold is 80 extracted characters per page. The default ratio threshold is 35 percent of pages.

## Retry and Blocking

Default retry policy:

- Maximum OCR attempts: 3.
- Retryable states: `ocr_needed`, `ocr_failed`.
- Backoff seconds: 30, 120, 600.
- Manual review is recommended after 2 attempts.
- Automatic import is blocked after 3 failed attempts.

Blocking conditions include encrypted files, unsupported file types, files over product limits, unreadable pages, and exhausted OCR retry budget.

## Low Resource Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_ocr_import_readiness_policy.py -q
python -m pytest tests/test_deep_review_ocr_readiness_runtime.py tests/test_ocr_import_readiness_policy.py -q
```

Expected static scan from the repository root:

```powershell
rg -n "s[k]-[A-Za-z0-9]{20,}|APP_AI_KEY=s[k]-" app/backend/services/ocr_import_readiness_policy.py app/backend/tests/test_ocr_import_readiness_policy.py docs/OCR_IMPORT_READINESS_POLICY.md
```

Expected result: no matches.

## Privacy Notes

Store document IDs, page-level counts, status labels, retry counts, and OCR engine metadata. Do not store raw legal text, uploaded images, credentials, user contact details, or full local paths in readiness payloads. Manual review should disclose the smallest useful set of page numbers and detection reasons.

The uploaded-document runtime binding stores only readiness metadata and safe
failure codes. It must not expose raw OCR text, uploaded page images, original
exception strings, full local paths, client emails, or credentials in polling
responses.
