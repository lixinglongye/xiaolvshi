# Legal Document Template Matrix

The legal document template matrix defines delivery coverage for generated legal documents. It is intended to close the product gap where document generation can stop at a free-form draft without template coverage, formatting checks, export readiness, or lawyer review.

## Purpose

- Track supported document types such as civil complaints, defense answers, evidence catalogs, lawyer letters, contract review reports, and settlement agreements.
- Define required fields before generation so the product can block incomplete drafts early.
- Record formatting requirements for each document type before final export.
- Keep pre-generation blockers explicit, including missing parties, unclear claims, incomplete evidence, missing authorization, or incomplete contract versions.
- Treat lawyer review as a critical gate before client delivery, court filing, external sending, or final archive.
- List export formats so delivery can be tested independently from model output quality.
- Provide low-resource validation commands that can run on a small local machine.

## Future API Endpoint Suggestion

```http
GET /api/v1/maintenance/legal-document-template-matrix
```

Suggested response shape:

- `status`: matrix readiness status.
- `summary`: document count, review-gate count, blocker count, and export-format count.
- `lawyer_review_gate`: shared lawyer-review policy for all document types.
- `document_types`: per-document template requirements, blockers, export formats, and delivery checklist.
- `low_resource_validation_commands`: local commands that validate the matrix without calling external model services.
- `privacy_notes`: rules for avoiding real party data, case facts, attachments, and model output in the matrix itself.

## Delivery Policy

- Generated documents remain drafts by default.
- A document can move toward final export only after required fields, formatting checks, blockers, and lawyer review all pass.
- Any document sent to a client, court, counterparty, or third party should retain the reviewed version and export record.
- Test fixtures should use redacted placeholders rather than real names, identity numbers, contact details, addresses, raw case facts, or full model outputs.

## Related Files

- `app/backend/services/legal_document_template_matrix.py`
- `app/backend/tests/test_legal_document_template_matrix.py`
- `docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md`
