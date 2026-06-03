# Case Intake Completeness

This service exposes a deterministic readiness checklist for deciding whether a matter has enough structured metadata to proceed to document generation, lawyer review, or client delivery.

## Endpoints

```http
GET /api/v1/maintenance/case-intake-completeness
POST /api/v1/maintenance/case-intake-completeness
```

The `GET` endpoint returns the template. The `POST` endpoint accepts field-presence metadata and returns:

- `status`: `template`, `blocked`, `needs_review`, or `ready`.
- `requirements`: case profile, venue, timeline, claim, evidence, and risk disclosure requirements.
- `blocking_items`: missing fields that block drafting or export.
- `next_actions`: product-safe follow-up steps for intake or lawyer review.

## Product Gap Covered

The case workspace should not generate filing-ready documents from incomplete intake. This checklist makes missing parties, venue, deadlines, claims, evidence support, and risk disclosures explicit before the system drafts or exports legal work.

## Safety Policy

The checklist stores field names and presence metadata only. It must not store raw client documents, private matter narratives, login credentials, API keys, user contact details, or model outputs.

## Related Files

- `app/backend/services/case_intake_completeness.py`
- `app/backend/tests/test_case_intake_completeness.py`
- `app/backend/routers/maintenance.py`
- `app/backend/services/case_evidence_graph.py`
- `docs/CASE_EVIDENCE_GRAPH.md`
