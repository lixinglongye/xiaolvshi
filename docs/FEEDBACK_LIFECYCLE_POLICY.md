# Feedback Lifecycle Policy

This document describes the pure local feedback lifecycle service in
`app/backend/services/feedback_lifecycle_policy.py`.

The service does not modify routers, release readiness checks, or the continuous
update ledger. It evaluates feedback metadata already available in memory and
returns a deterministic lifecycle assessment for maintainers.

## State Machine

Happy path:

```text
intake -> triage -> linked_gap -> in_progress -> release_validation -> customer_visible_resolution -> closed
```

States:

- `intake`: the ticket has a user signal such as category, title, summary, or content.
- `triage`: deterministic feedback triage has produced priority, owner, labels, and matched rules.
- `linked_gap`: the ticket is attached to a roadmap gap or release gate.
- `in_progress`: an owner is accountable for the fix, review, or support action.
- `release_validation`: the linked roadmap gap or release gate is checked before public resolution.
- `customer_visible_resolution`: a support-safe public resolution is ready.
- `closed`: the customer update and internal closure summary are present.

## Transition Checks

- `intake -> triage`: requires `intake-signal-present`.
- `triage -> linked_gap`: requires `triage-complete`, `roadmap-gap-or-release-gate-linked`, and `high_risk_feedback_linked`.
- `linked_gap -> in_progress`: requires `work-owner-present`.
- `in_progress -> release_validation`: requires `release-validation-plan-present` and `high_risk_release_gate_linked`.
- `release_validation -> customer_visible_resolution`: requires `release-validation-accepted`, `customer-resolution-note-present`, and `privacy-safe-public-note`.
- `customer_visible_resolution -> closed`: requires `customer-notification-ready` and `closure-summary-present`.

High-risk feedback is any item with P0/P1 triage priority or privacy, security,
legal-quality, high-risk-output, or revenue-blocker labels. Every high-risk item
must have a `roadmap_gap_id` or at least one `release_gate_links` entry before it
can leave triage. Before release validation, high-risk items must also have an
explicit release gate.

## Sample Ticket Evaluation

`FeedbackLifecyclePolicyService().build_policy()` returns
`sample_tickets_evaluation` covering:

- privacy upload exposure feedback linked to `privacy-safe-upload` and privacy release gates;
- incorrect citation feedback linked to `traceable-legal-review` and citation/evidence release gates;
- OCR blank-output feedback linked to `robust-extraction-quality`;
- a lower-risk export template request linked to roadmap feedback clustering.

Each sample is evaluated with the same local checks used for normal tickets.

## Privacy Note

The lifecycle service is deterministic and local. It evaluates ticket metadata,
triage labels, roadmap gap IDs, release gate names, validation status, and
customer-visible notes. It does not call an AI model, persist feedback, inspect
uploaded legal documents, or store raw personal data, credentials, prompts, or
model outputs.

Customer-visible resolution notes are checked for obvious secret-like fragments
such as raw API keys, password markers, or token markers before a ticket can move
from `release_validation` to `customer_visible_resolution`.

## Validation Commands

```bash
python -m pytest app/backend/tests/test_feedback_lifecycle_policy.py
python -m compileall app/backend/services/feedback_lifecycle_policy.py app/backend/tests/test_feedback_lifecycle_policy.py
```

For the full backend regression pass used in this change:

```bash
python -m pytest app/backend/tests
python -m compileall app/backend
```
