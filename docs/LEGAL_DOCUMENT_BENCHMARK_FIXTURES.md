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

All fixtures are synthetic. They use generic names such as `A公司`, `张某`,
and `C公司`; they do not contain real client documents or personal contact
data. The fixture service exposes `summary.locale_quality = readable_zh_cn`,
and the pytest suite blocks common mojibake markers so reviewer-facing fixture
metadata stays readable Chinese.

## Output Shape

`build_suite()` returns:

- `benchmark_cases`: 4 synthetic Chinese snippets with expected document type, expected fields, expected task labels, and expected risk labels.
- `expected_tasks`: task definitions for classification, extraction, deadline extraction, and risk labeling.
- `evaluation_plan`: a local-only scoring plan with disabled network access and no model calls.
- `privacy_boundary`: explicit flags for synthetic fixture snippets, UI raw-snippet rendering, no model calls, no network access, no credentials, no prompts, no gateway payloads, and no dataset downloads.
- `claim_boundary`: explicit non-claims for public benchmark scores, live model accuracy, production accuracy, real-client document coverage, universal document support, and legal advice.
- `privacy_note`: repository safety guidance for fixture maintenance.
- `validation_commands`: the pytest command for this module.

The Maintenance Evidence page now exposes a fixture-suite panel that displays
case IDs, document types, matter types, expected-check counts, field keys,
snippet length, the empty-prediction evaluation state, and validation commands.
The UI deliberately does not render raw fixture snippets even though the backend
fixture API returns short synthetic snippets for local pytest and evaluator
workflows. Use the coverage, gate, and promotion-packet evidence when a strictly
metadata-only review surface is required.

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

`build_local_rule_baseline()` adds a no-model baseline over the same synthetic
fixtures. It uses local keyword and regular-expression rules for document type,
party pair, amount/claim, deadline, evidence, and risk-label detection, then
passes those structured predictions through `evaluate_predictions()`. The
baseline returns status, score, per-case match counts, rule descriptions, and
privacy/claim boundaries only. It does not return the generated prediction
payload, extracted field values, raw model outputs, gateway payloads, or
credentials.

The baseline is also exposed at:

```http
GET /api/v1/maintenance/legal-review-benchmark/document-fixtures/local-baseline
```

The cheap-first default gate now requires this local baseline to pass before
local legal fixture evidence can support a Gemini/NewAPI cheap-first default
review. This keeps the lowest-cost model path tied to a laptop-safe legal
document smoke check before any gateway or model-backed fixture run is used.

## Privacy And Resource Policy

- No external model calls.
- No network access.
- No downloaded public datasets.
- No real client documents, identity numbers, phone numbers, emails, addresses, gateway keys, or raw model outputs.
- No local baseline prediction payloads or extracted field values are returned
  from gate or promotion-packet evidence.
- Keep snippets short enough for laptop pytest runs.
- Maintenance UI panels must not render raw fixture snippets, prompt text,
  candidate generated text, gateway payloads, credentials, or client material.

## Validation

Run from the repository root:

```powershell
cd app/backend
python -m pytest tests/test_legal_document_benchmark_fixtures.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```
