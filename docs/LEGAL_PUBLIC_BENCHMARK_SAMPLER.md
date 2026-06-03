# Legal Public Benchmark Sampler

The public benchmark sampler turns external legal benchmark research into a resource-capped local sampling plan. It does not download benchmark datasets and does not import raw examples by default.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/public-sampler
POST /api/v1/maintenance/legal-review-benchmark/public-sampler
```

`GET` returns the default plan for LegalBench, CUAD, LexGLUE, and Pile of Law.

`POST` accepts explicit source and license-review settings:

```json
{
  "enabled_source_ids": ["cuad", "legalbench"],
  "max_samples_per_source": 2,
  "license_reviews": {
    "cuad": "approved",
    "legalbench": "pass"
  }
}
```

## Research Mapping

- LegalBench maps to multi-task legal reasoning, evidence reasoning, and legal RAG checks.
- CUAD maps to contract clause extraction and service-agreement risk fixtures.
- LexGLUE maps to legal classification and CaseHOLD-style reasoning checks.
- Pile of Law remains catalog-only for local runs because it is corpus-scale.

## Local Run Policy

- Default local runs stay on synthetic fixtures from `/fixture-smoke`.
- Low-resource local checks can start from `/quick-suite`, which maps a 3-fixture subset back to public source metadata without downloading datasets.
- Public-source sampling requires source-level license, attribution, privacy, and resource review.
- The sampler caps samples per source and sample text size before any reviewed import.
- Large corpus sources stay out of laptop tests unless a resource-controlled CI job is approved.

## Output

- `source_plans`: source metadata, local fixture mapping, sampling state, license gate, and recommended action.
- `sampling_batches`: task-oriented batches that map public-source samples back to fixture or benchmark endpoints.
- `resource_policy`: network, storage, and sample-size limits.
- `validation_commands`: focused tests that prove the sampler and release evidence indexes are wired.

## Safety

Do not commit raw public benchmark examples, client documents, personal data, gateway keys, emails, or model outputs. Store only source IDs, task labels, normalized observations, attribution notes, and review status unless license review explicitly permits snippets.

## Related Files

- `app/backend/services/legal_public_benchmark_sampler.py`
- `app/backend/tests/test_legal_public_benchmark_sampler.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/LEGAL_REVIEW_BENCHMARK.md`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
