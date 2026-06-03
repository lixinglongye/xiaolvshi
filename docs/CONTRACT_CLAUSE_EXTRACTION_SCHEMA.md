# Contract Clause Extraction Schema

`ContractClauseExtractionSchemaService` defines a deterministic metadata schema
for clause-level contract review.

## Scope

The service covers these clause types:

- parties
- payment
- delivery
- term
- termination
- liability
- confidentiality
- dispute resolution
- governing law

Required clause types must be present before the extraction result is considered
ready for clause-level review.

## Checks

The service flags:

- unsupported clause types
- missing source anchors
- missing required clause types
- high-risk clauses without lawyer review
- critical clauses without proposed edits

The service is local-only and metadata-only. It does not accept raw contracts,
client contact details, account credentials, API keys, passwords, or full
confidential text.

## Validation

Run from `app/backend`:

```powershell
python -m pytest tests/test_contract_clause_extraction_schema.py -q
python -m compileall services/contract_clause_extraction_schema.py tests/test_contract_clause_extraction_schema.py
```
