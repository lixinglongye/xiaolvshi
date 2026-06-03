# Legal Benchmark Fixtures

This project keeps legal benchmark runs lightweight by separating public benchmark candidates from local synthetic fixtures.

## Local Run Policy

- Do not fetch large public legal datasets during default local tests.
- Use the bundled synthetic snippets returned by `/api/v1/maintenance/legal-review-benchmark`.
- Keep each fixture short enough for unit tests and laptop smoke tests.
- Store no real client facts, credentials, emails, API keys, or copied contract text in fixtures.
- Treat public datasets as cataloged candidates until their license and attribution requirements are reviewed.

## Public Benchmark Candidates

- LegalBench: legal reasoning task families for issue spotting, evidence reasoning, and legal RAG grounding.
- CUAD: contract-clause review candidate for service agreement and complex contract tests.
- LexGLUE: legal NLP benchmark candidate for classification and CaseHOLD-style reasoning tasks.
- Pile of Law: corpus-scale legal language reference, not suitable for default local regression runs.

## Bundled Synthetic Fixtures

- `fixture-service-agreement-small`: service contract risks, liability cap gaps, missing SLA attachment, and route-cost checks.
- `fixture-lease-dispute-notice-small`: deposit, repair notice, invoice, handover checklist, and evidence completeness checks.
- `fixture-low-text-pdf-page-small`: OCR confidence, low-text page handling, version conflict, and extraction routing checks.
- `fixture-adversarial-upload-small`: privacy redaction, prompt-injection visibility, loan evidence gaps, and safety preflight checks.

## Smoke Evaluator

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-smoke
POST /api/v1/maintenance/legal-review-benchmark/fixture-smoke
```

The evaluator accepts observed output text and an optional route for each fixture. It returns:

- signal coverage,
- task output coverage,
- route match,
- missing signals and missing task outputs.

This is meant for quick laptop checks after prompt, routing, report schema, extraction, or safety changes.

Use `/api/v1/maintenance/legal-review-benchmark/fixture-improvements` to convert smoke-test gaps into prompt clauses, report-schema targets, and validation hints.

Use `/api/v1/maintenance/legal-review-benchmark/prompt-pack` to fetch cheap-first Gemini/NewAPI prompt payloads for the same fixtures.

Use `/api/v1/maintenance/legal-review-benchmark/fixture-model-matrix` to inspect fixture-level Gemini/NewAPI candidate ladders before spending on escalations.

Use `/api/v1/maintenance/legal-review-benchmark/gateway-manifest` to fetch safe OpenAI-compatible request bodies and local AI hub payloads for laptop-sized fixture checks without storing real keys.

Use `/api/v1/maintenance/legal-review-benchmark/fixture-run-plan` to run those requests in serial cheap-first batches before any conditional escalation.

Use `/api/v1/maintenance/legal-review-benchmark/fixture-run-report` to convert observations and run metadata into a cheap-first release decision.

Use `/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle` to bundle smoke scores, model routing evidence, run reports, validation commands, and release-safe claims after a small local run.

## Release Use

The fixtures support the `legal-review-benchmark` release-readiness check. They are intended for deterministic local tests, while larger public benchmarks can be sampled later in a resource-controlled CI job after license review.

## Related Files

- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_fixture_model_matrix.py`
- `app/backend/services/legal_fixture_prompt_pack.py`
- `app/backend/services/legal_fixture_gateway_manifest.py`
- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/backend/services/legal_fixture_improvement.py`
- `app/backend/tests/test_legal_review_benchmark.py`
- `app/backend/tests/test_legal_fixture_model_matrix.py`
- `app/backend/tests/test_legal_fixture_prompt_pack.py`
- `app/backend/tests/test_legal_fixture_gateway_manifest.py`
- `app/backend/tests/test_legal_fixture_run_plan.py`
- `app/backend/tests/test_legal_fixture_run_report.py`
- `app/backend/tests/test_legal_fixture_evidence_bundle.py`
- `app/backend/tests/test_legal_fixture_improvement.py`
- `docs/LEGAL_REVIEW_BENCHMARK.md`
- `docs/LEGAL_FIXTURE_MODEL_MATRIX.md`
- `docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md`
- `docs/LEGAL_FIXTURE_RUN_PLAN.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
- `app/backend/services/release_readiness.py`
