# Legal Review Benchmark

The project now has a deterministic benchmark suite for legal-review pipeline changes.

## Purpose

Model, prompt, retrieval, extraction, and report-schema changes should be evaluated against repeatable legal workflow scenarios. The benchmark suite provides a stable set of cases and required metrics before a release is marked ready.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark
POST /api/v1/maintenance/legal-review-benchmark
GET /api/v1/maintenance/legal-review-benchmark/fixture-smoke
POST /api/v1/maintenance/legal-review-benchmark/fixture-smoke
GET /api/v1/maintenance/legal-review-benchmark/fixture-improvements
POST /api/v1/maintenance/legal-review-benchmark/fixture-improvements
GET /api/v1/maintenance/legal-review-benchmark/prompt-pack
```

`GET` returns the suite, required metrics, a default run template, and a `not_run` evaluation.
It also returns a lightweight public benchmark source catalog and small synthetic document fixtures for local smoke tests.

`POST` accepts benchmark results keyed by case ID:

```json
{
  "service-contract-risk": {
    "field_coverage": "pass",
    "risk_grounding": "pass",
    "release_decision": "pass",
    "cost_route": "pass"
  }
}
```

Metric values can be `pass`, `warn`, `fail`, booleans, or `0-100` numeric scores.

`GET /fixture-smoke` returns the small synthetic document fixtures, expected signals, expected task outputs, and an empty observation template.

`POST /fixture-smoke` accepts observed model or pipeline output by fixture ID:

```json
{
  "fixture-service-agreement-small": {
    "route": "fast",
    "output_text": "risk matrix ... liability cap ... missing facts ... replacement clause ..."
  }
}
```

The smoke evaluator scores signal coverage, task output coverage, and route match. It does not call a model and does not fetch public datasets.

`GET/POST /fixture-improvements` converts fixture smoke gaps into prompt clauses, report-schema targets, and validation hints so failed small-document tests produce actionable algorithm and schema work.

`GET /prompt-pack` returns cheap-first model prompt payloads for the same fixtures, including recommended Gemini/NewAPI task defaults, request parameters, output schema, and follow-up evaluation endpoints.

## Research Basis

- LegalBench: use multiple legal reasoning task families instead of a single generic accuracy score.
- RAGAS: track faithfulness, answer relevance, and context relevance for RAG-style outputs.
- CRAG: use comprehensive factual QA and retrieval-style checks for answer reliability.

## Public Sources and Fixtures

The suite catalogs LegalBench, CUAD, LexGLUE, and Pile of Law as future benchmark candidates, but default tests do not fetch them. Large public datasets should only be sampled in a resource-controlled job after license and attribution review.

Bundled local fixtures are short synthetic snippets for:

- service agreement risk review,
- lease dispute evidence completeness,
- low-text PDF extraction,
- privacy-sensitive and instruction-injection uploads.

## Benchmark Cases

- Service contract risk review.
- Lease dispute evidence completeness.
- Long PDF extraction and routing.
- Privacy-sensitive upload.
- Instruction-injection upload resilience.
- Legal RAG grounding.

## Required Metric Families

- Field coverage.
- Risk grounding.
- Citation grounding.
- Evidence plan completeness.
- Extraction quality.
- Privacy and instruction-risk visibility.
- Secret safety.
- Cheap-first or premium-exception route correctness.
- Release decision.

## Release Use

The `legal-review-benchmark` release-readiness check requires this service, its tests, and this document. It should be run after any major change to:

- model routing,
- prompts,
- report schema,
- retrieval or legal source handling,
- PDF extraction,
- safety preflight.

## Related files

- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_fixture_prompt_pack.py`
- `app/backend/services/legal_fixture_improvement.py`
- `app/backend/routers/maintenance.py`
- `app/backend/tests/test_legal_review_benchmark.py`
- `app/backend/tests/test_legal_fixture_prompt_pack.py`
- `app/backend/tests/test_legal_fixture_improvement.py`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_FIXTURE_PROMPT_PACK.md`
- `docs/LEGAL_FIXTURE_IMPROVEMENT.md`
- `app/backend/services/release_readiness.py`
