# ModelOps Legal Fixture Cheap-First Benchmark Gate

`modelops-legal-fixture-cheap-first-benchmark-gate` joins the laptop-safe legal
fixture quick suite, fixture model matrix, run report, evidence bundle, legal
document benchmark suite, legal document fact-consistency benchmark, legal
document coverage matrix, selector replay, and Gemini/NewAPI cheap-first
calibration into a metadata-only gate for cheap-first Gemini default evidence.
The same gate is exposed in the AIHub ModelOps payload, the direct
`/api/v1/aihub/models/legal-fixture-cheap-first-benchmark-gate` endpoint, the
maintenance page, and the ModelOps main page so reviewers can inspect it beside
cheap-first calibration and default-change evidence.

The gate answers one release question: can selected small legal-document fixture
results plus local legal-document benchmark results support keeping cheap-first
defaults, or must reviewers run/fix/escalate the fixture before any default
model change?

It records only:

- Synthetic fixture ids and titles.
- Synthetic document case ids and document types.
- Expected issue, document-structure, citation, PII, and risk-label counts.
- Cheap-first model ids, cost tiers, and estimated request costs.
- Gate status, document benchmark status, fact-consistency status, coverage-gap
  counts, calibration status, linked calibration task ids, calibration
  decisions, calibration release gates, release action, validation targets, and
  reason codes.
- Public benchmark source ids and license-review state as metadata only.

It does not call NewAPI, Gemini, OpenAI, Google, any gateway, or the network. It
does not return real legal text, fixture excerpts, document snippets, prompts,
candidate generated text, raw model outputs, gateway payloads, calibration
payloads, credentials, emails, phone numbers, or identity numbers.

Primary validation:

```bash
cd app/backend
python -m pytest tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_gemini_newapi_cheap_first_calibration.py tests/test_gemini_newapi_selector_replay.py tests/test_legal_fixture_quick_suite.py tests/test_legal_fixture_model_matrix.py tests/test_legal_fixture_run_report.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_fact_consistency_benchmark.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```
