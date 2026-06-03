# Legal Source Freshness Policy

`LegalSourceFreshnessPolicyService` defines a deterministic metadata check for
legal knowledge sources before they are used by retrieval or generated legal
answers.

## Purpose

Legal RAG must know whether a source is current, citable, and jurisdictionally
appropriate. This slice keeps that review local and privacy-safe:

- no network calls
- no model calls
- no real client documents
- no raw legal matter text
- no API keys or account credentials

## Checks

The service reviews each source metadata record for:

- known source type
- supported jurisdiction
- effective date
- stable citation
- last verified date
- stale or review-due freshness window

Blocking flags include missing jurisdiction, unsupported jurisdiction, missing
effective date, future effective date, missing citation, missing verification,
stale source, and unknown source type.

## API Shape

The payload contains:

- `status`
- `summary`
- `freshness_rules`
- `source_reviews`
- `manual_review_escalations`
- `recommended_actions`
- `privacy_note`
- `validation_commands`

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_legal_source_freshness_policy.py -q
```

Run the focused credential scan from the repository root:

```powershell
rg -n "(s[k]-[A-Za-z0-9]{20,}|APP_AI_KEY=s[k]-)" app/backend/services/legal_source_freshness_policy.py docs/LEGAL_SOURCE_FRESHNESS_POLICY.md
```
