# Feedback Capture Plan

The project now has a metadata-only feedback capture plan for user-facing
feedback intake.

## What It Does

- Previews feedback priority, support owner, SLA, roadmap user-need ID, release
  gates, lifecycle blockers, and missing intake fields before ticket creation.
- Enriches created `feedback_tickets` with a privacy-safe support note that
  links the ticket to roadmap and lifecycle evidence.
- Adds a product feedback form to `/settings`, alongside the existing data
  deletion request.
- Keeps the existing admin feedback queue compatible because no database schema
  migration is required.

## Endpoints

```text
POST /api/v1/entities/feedback_tickets/capture-plan
POST /api/v1/entities/feedback_tickets
```

`capture-plan` does not write a ticket. It returns a deterministic preview from
`FeedbackCapturePlanService` using the existing triage, roadmap alignment, and
lifecycle policy services.

## Privacy Boundary

The capture plan does not call an AI model or external network. The preview
returns metadata only: priority, owner, user-need IDs, release-gate IDs,
lifecycle blockers, missing field names, and public acknowledgement text. It
does not return raw feedback text, user contact details, prompts, model output,
credentials, payment secrets, or legal matter content.

## Validation

```powershell
python -m pytest tests/test_feedback_capture_plan.py tests/test_feedback_lifecycle_policy.py tests/test_feedback_roadmap_alignment.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
