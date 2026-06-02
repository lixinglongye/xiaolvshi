# Instruction Injection Audit

Uploaded documents can contain text that looks like instructions to the AI system rather than legal content. The project now scans document text for common prompt-injection style patterns before deep review.

## What it detects

- Attempts to ignore previous or system instructions.
- Attempts to reveal hidden prompts or developer messages.
- Attempts to extract credentials or tokens.
- Role overrides such as developer mode or jailbreak wording.
- Requests to run commands, tools, webhooks, or external network calls.

## Integration

`DocumentReviewPreflightService` attaches the result as `preflight.instruction_audit`.

When medium or high instruction-injection risk is detected, preflight adds a warning. The upload progress event also exposes:

- `instruction_risk_level`
- `instruction_finding_count`

This does not prevent legitimate legal review by itself. It tells maintainers and future UI flows to treat the matched text as document content, not as instructions.

## Related files

- `app/backend/services/instruction_injection_audit.py`
- `app/backend/services/document_preflight.py`
- `app/backend/tests/test_instruction_injection_audit.py`
