# Legal Fixture Quick Suite

The quick suite is the smallest legal benchmark run plan for low-resource local machines. It reuses existing synthetic fixtures, cheap-first run plans, and public benchmark source mappings without downloading datasets or calling any model.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/quick-suite
GET /api/v1/maintenance/legal-review-benchmark/quick-suite?fixture_limit=2
```

`fixture_limit` is clamped to 1-4. The default is 3 fixtures:

- service agreement risk review,
- lease dispute evidence completeness,
- low-text PDF extraction.

The fourth optional fixture covers privacy-sensitive and instruction-injection uploads.

## Output

- `selected_fixtures`: fixture IDs, expected tasks/signals, linked benchmark cases, cheap-first model, estimated request cost, and source mappings.
- `quick_steps`: fetch, serial cheap-first run, smoke scoring, run-report, and evidence-bundle steps.
- `public_source_mapping`: LegalBench, CUAD, LexGLUE, and Pile of Law mappings for the selected fixtures, with download disabled by default.
- `observation_template`: minimal payload to paste normalized outputs into `/fixture-smoke`.
- `validation_commands`: small pytest commands for the quick suite and its dependencies.

## Low-Resource Policy

- Run one fixture request at a time.
- Use cheap-first models before any escalation.
- Keep public benchmark rows as metadata until license, attribution, and privacy review are complete.
- Do not commit raw model outputs, public benchmark raw text, client documents, emails, or API keys.

## Validation

```bash
python -m pytest tests/test_legal_fixture_quick_suite.py tests/test_legal_review_benchmark.py -q
python -m pytest tests/test_legal_fixture_run_plan.py tests/test_legal_public_benchmark_sampler.py -q
```

## Related Files

- `app/backend/services/legal_fixture_quick_suite.py`
- `app/backend/tests/test_legal_fixture_quick_suite.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/services/legal_public_benchmark_sampler.py`
- `docs/LEGAL_REVIEW_BENCHMARK.md`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
