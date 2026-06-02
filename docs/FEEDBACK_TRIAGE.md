# Feedback Triage

User feedback now has deterministic issue triage before it enters the maintenance queue.

## Backend

- Service: `app/backend/services/feedback_triage.py`
- Router integration: `app/backend/routers/feedback_tickets.py`
- Tests: `app/backend/tests/test_feedback_triage.py`

## Behavior

When a user creates a feedback ticket, the API enriches the payload with:

- `status`: defaults to `triaged`.
- `priority`: `P0`, `P1`, `P2`, or `P3`.
- `assignee`: suggested internal queue owner.
- `resolution_note`: auto-triage summary with labels and operator actions.

The service is deterministic and does not call an AI model. This keeps triage cheap, predictable, and safe for feedback that may contain sensitive legal or personal details.

## Priority policy

- `P0`: privacy, security, data deletion, or personal-information leak signals.
- `P1`: payment/access blockers or risky legal output such as wrong law, hallucinated citations, or missed high-risk findings.
- `P2`: upload, OCR, PDF extraction, timeout, crash, or document-processing failures.
- `P3`: feature requests, usability feedback, templates, exports, and general product suggestions.

## Preview endpoint

```http
POST /api/v1/entities/feedback_tickets/triage-preview
```

Request:

```json
{
  "category": "report",
  "content": "The report has an incorrect citation and missed risk."
}
```

The endpoint returns the same triage fields without creating a ticket.
