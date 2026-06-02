# Legal Knowledge Audit

The local legal knowledge seed can now be audited before it is imported into the database or used as grounding material for deep review.

## Endpoint

```http
GET /api/v1/legal-knowledge/audit
```

Optional query:

```http
GET /api/v1/legal-knowledge/audit?seed_path=path/to/seed.json
```

## Checks

- Seed JSON shape and record count.
- Duplicate `source_id` values.
- Required legal-source metadata fields.
- Verification coverage.
- `generated_at` freshness.
- Critical contract-review topic coverage.
- Source type and authority level distribution.

## Status

- `pass`: seed is recent, verified, complete, and covers critical contract topics.
- `warn`: seed is usable but stale, under-verified, or missing critical topic coverage.
- `fail`: seed is empty, has duplicate source IDs, or has records missing required metadata.

## Related files

- `app/backend/services/legal_knowledge_audit.py`
- `app/backend/routers/legal_knowledge.py`
- `app/backend/tests/test_legal_knowledge_audit.py`
- `app/backend/data/legal_knowledge/contract_law_seed.json`
