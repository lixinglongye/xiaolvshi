# Legal Document Benchmark Fixtures

Related coverage evidence: `docs/LEGAL_DOCUMENT_BENCHMARK_COVERAGE.md` maps the tiny synthetic fixtures to document-type, section, citation, risk-label, and PII coverage without exposing fixture snippets or model outputs. The first matrix now covers civil complaints, lawyer letters, contract review, evidence catalogs, settlement agreements, and legal opinions.

This module adds a small, deterministic benchmark fixture set for Chinese legal-document smoke tests on low-resource local machines.

## Purpose

`LegalDocumentBenchmarkFixturesService` helps test short-text legal workflows without external model calls. It is intended for quick checks of:

- Document classification
- Party extraction
- Amount, claim, evidence, and deadline extraction
- Risk label coverage
- Contract, civil complaint, lawyer letter, and settlement-agreement snippets

All fixtures are synthetic. They use generic names such as `A公司`, `张某`, and `C公司`; they do not contain real client documents or personal contact data.

## Output Shape

`build_suite()` returns:

- `benchmark_cases`: 4 synthetic Chinese snippets with expected document type, expected fields, expected task labels, and expected risk labels.
- `expected_tasks`: task definitions for classification, extraction, deadline extraction, and risk labeling.
- `evaluation_plan`: a local-only scoring plan with disabled network access and no model calls.
- `privacy_note`: repository safety guidance for fixture maintenance.
- `validation_commands`: the pytest command for this module.

`evaluate_predictions(predictions)` accepts local structured predictions keyed by fixture ID:

```python
{
    "fixture-contract-payment-small": {
        "document_type": "contract",
        "classification_labels": ["service_contract", "payment_clause"],
        "task_labels": [
            "document_classification",
            "party_extraction",
            "amount_or_claim_extraction",
            "deadline_extraction",
            "risk_labeling",
        ],
        "risk_labels": [
            "missing_data_liability",
            "missing_service_level_attachment",
            "termination_fee_gap",
        ],
        "extracted_fields": {
            "parties": "A公司;B公司",
            "amount_or_claim": "120000元",
            "deadline": "验收后15日",
        },
    }
}
```

The evaluator scores classification, task-label coverage, risk-label coverage, and field coverage equally. It performs exact deterministic string checks only.

## Privacy And Resource Policy

- No external model calls.
- No network access.
- No downloaded public datasets.
- No real client documents, identity numbers, phone numbers, emails, addresses, gateway keys, or raw model outputs.
- Keep snippets short enough for laptop pytest runs.

## Validation

Run from the repository root:

```powershell
cd app/backend
python -m pytest tests/test_legal_document_benchmark_fixtures.py -q
```
