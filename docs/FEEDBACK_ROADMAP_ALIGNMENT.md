# Feedback Roadmap Alignment

The project now maps deterministic feedback triage results to user-needs roadmap items.

## Purpose

Feedback should not become scattered one-off fixes. The alignment service connects a feedback item to:

- triage priority and owner,
- user need ID,
- confidence score,
- release gates,
- next product or maintenance actions.

## Endpoints

```http
POST /api/v1/entities/feedback_tickets/triage-preview
GET /api/v1/maintenance/feedback-roadmap
```

`triage-preview` now returns `roadmap_alignment` along with the existing triage result.

`feedback-roadmap` returns the mapping catalog so maintainers can audit how feedback maps into roadmap needs.

## Current Mappings

- Privacy or security feedback -> `privacy-safe-upload`
- Prompt or instruction attack feedback -> `prompt-injection-resilience`
- Incorrect citation, hallucination, or missed legal risk -> `traceable-legal-review`
- Upload, OCR, PDF, or extraction failures -> `robust-extraction-quality`
- Cost, premium model, slow model, or Gemini routing feedback -> `cheap-first-review-routing`
- UI, summary, next-step, or readability feedback -> `plain-language-actionability`
- General workflow feedback -> `feedback-to-roadmap-loop`

## Safety

The mapper uses category, content keywords, deterministic triage labels, and the public user-needs radar. It does not store prompts, uploaded documents, credentials, or private user identifiers.

## Related files

- `app/backend/services/feedback_roadmap_alignment.py`
- `app/backend/services/feedback_triage.py`
- `app/backend/services/user_needs_radar.py`
- `app/backend/tests/test_feedback_roadmap_alignment.py`
