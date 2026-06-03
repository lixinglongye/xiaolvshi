# Small Legal Document Corpus Expansion

This document records the local fixture expansion for small Chinese legal-document scenarios. The corpus is intentionally synthetic, deterministic, and small enough to run on a low-resource laptop.

## Scope

- Service: `app/backend/services/small_legal_document_corpus_expansion.py`
- Tests: `app/backend/tests/test_small_legal_document_corpus_expansion.py`
- Output keys: `corpus_items`, `coverage_matrix`, `expansion_plan`, `privacy_note`, `validation_commands`
- Runtime: local Python only
- Network: disabled
- Model calls: not required

## Corpus Items

The service returns 8 short synthetic scenario metadata items:

1. Labor termination compensation arbitration
2. Lease arrears demand letter
3. Sales contract quality objection
4. Service delivery delay refund
5. Private lending overdue repayment
6. Traffic accident tort compensation
7. Property damage mediation
8. Consumer service refund notice

Each item includes:

- `domain`
- `matter_type`
- `document_type`
- `scenario`
- `synthetic_excerpt`
- `tasks`
- `expected_fields`
- `risk_tags`
- `local_checks`

## Coverage Matrix

The coverage matrix groups fixture items by:

- Required domains: labor, lease, sales, service, lending, traffic or tort
- Document types
- Local evaluation tasks
- Risk tags

Core task coverage includes classification, party-role detection, amount extraction, date/deadline extraction, claim or obligation extraction, risk labeling, evidence-gap detection, and next-action generation.

## Privacy Boundary

All items use generic party labels and short synthetic facts. Do not add real client documents, real names, contact details, identity identifiers, addresses, access secrets, or raw model outputs.

## Low-Resource Validation

Run:

```powershell
cd app/backend
python -m pytest tests/test_small_legal_document_corpus_expansion.py -q
```

Expected result: all tests pass without network access or external model calls.
