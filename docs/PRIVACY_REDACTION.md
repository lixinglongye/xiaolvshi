# Privacy Redaction

Legal documents often contain resident ID numbers, phone numbers, emails, bank cards, addresses, and payment identifiers. The project now has a deterministic privacy redaction scanner for common high-risk identifiers.

## What it detects

- Chinese resident ID numbers.
- Mainland China mobile phone numbers.
- Bank card style numeric identifiers.
- Email addresses.

## Output

- `status`: `pass` or `warn`.
- `risk_level`: `none`, `low`, `medium`, or `high`.
- `counts_by_type`: count by finding type.
- `findings`: bounded finding metadata with masked samples.
- `redacted_preview`: first 1200 characters with common identifiers replaced.
- `recommended_actions`: operator guidance for safe logging, screenshots, and review handoff.

## Integration

`DocumentReviewPreflightService` attaches privacy scan results to `preflight.privacy_scan`. Critical or high privacy findings add a preflight warning so maintainers can avoid leaking raw personal data in prompts, logs, screenshots, or benchmark artifacts.

## Related files

- `app/backend/services/privacy_redaction.py`
- `app/backend/services/document_preflight.py`
- `app/backend/tests/test_privacy_redaction.py`
