# ModelOps Legal Fixture Cheap-First Benchmark Gate

`modelops-legal-fixture-cheap-first-benchmark-gate` joins the laptop-safe legal
fixture quick suite, fixture model matrix, run report, and evidence bundle into a
metadata-only gate for cheap-first Gemini default evidence.

The gate answers one release question: can selected small legal-document fixture
results support keeping cheap-first defaults, or must reviewers run/fix/escalate
the fixture before any default model change?

It records only:

- Synthetic fixture ids and titles.
- Expected issue tag counts and task counts.
- Cheap-first model ids, cost tiers, and estimated request costs.
- Gate status, release action, validation targets, and reason codes.
- Public benchmark source ids and license-review state as metadata only.

It does not call NewAPI, Gemini, OpenAI, Google, any gateway, or the network. It
does not return real legal text, fixture excerpts, prompts, raw model outputs,
gateway payloads, credentials, emails, phone numbers, or identity numbers.

Primary validation:

```bash
cd app/backend
python -m pytest tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_legal_fixture_quick_suite.py tests/test_legal_fixture_model_matrix.py tests/test_legal_fixture_run_report.py -q
```
