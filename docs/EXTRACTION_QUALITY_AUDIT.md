# Extraction Quality Audit

Uploaded legal documents now run a deterministic extraction quality audit after text extraction and OCR.

## What it checks

- Extracted character count.
- Page count and characters per page.
- Text-layer page count.
- Low-text page count.
- OCR page count.
- Extraction warnings from the parser or OCR pipeline.

## Status

- `pass`: extracted text is dense enough for staged deep review.
- `warn`: review may proceed, but OCR pages, weak text layers, or low density should be spot-checked.
- `fail`: model review should stop because the extracted text is too short or too sparse.

## Uploaded-document integration

The audit result is attached to:

- `AnalyzeUploadedDocumentResponse.extraction.extraction_quality`
- Upload progress events through `progress.extraction_quality`
- Persisted `documents.extraction_metadata_json`

If extraction quality fails, the backend stops before model review and asks the user for a clearer PDF, DOCX, or copyable text version.

## Related files

- `app/backend/services/extraction_quality.py`
- `app/backend/routers/deep_review.py`
- `app/backend/tests/test_extraction_quality.py`
