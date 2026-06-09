# Legal Public Benchmark Sampler

The public benchmark sampler turns external legal benchmark research into a resource-capped local sampling plan. It does not download benchmark datasets and does not import raw examples by default.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/public-sampler
POST /api/v1/maintenance/legal-review-benchmark/public-sampler
```

`GET` returns the default plan for LegalBench, CUAD, LexGLUE, LegalBench-RAG, LexEval, CaseGen, and Pile of Law.

Use `/api/v1/maintenance/legal-review-benchmark/fixture-crosswalk` when you need the same public sources joined to local benchmark case IDs, `fixture-*` IDs, `ldoc-*` document fixture IDs, and tiny `small-corpus-*` metadata IDs. Use `/api/v1/maintenance/legal-review-benchmark/public-fixture-priority-queue` when you need those mappings ranked into the next synthetic fixture work queue.

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
- LegalBench-RAG maps to legal retrieval, citation grounding, abstention, and hallucination-triage fixture design.
- LexEval maps to Chinese legal cognition, reasoning, and generation coverage over local zh-CN fixtures.
- CaseGen maps to staged legal document generation checks for structure, citation, PII exclusion, and risk labels.
- Pile of Law remains catalog-only for local runs because it is corpus-scale.

## Local Run Policy

- Default local runs stay on synthetic fixtures from `/fixture-smoke`.
- Low-resource local checks can start from `/quick-suite`, which maps a 3-fixture subset back to public source metadata without downloading datasets.
- Public-source sampling requires source-level license, attribution, privacy, and resource review.
- The sampler caps samples per source and sample text size before any reviewed import.
- Large corpus sources stay out of laptop tests unless a resource-controlled CI job is approved.

## Output

- `source_plans`: source metadata, local fixture mapping, sampling state, license gate, and recommended action.
- `source_plans[].document_fixture_ids`: local `ldoc-*` legal-document fixture IDs used for Chinese legal generation and legal RAG planning.
- `sampling_batches`: task-oriented batches that map public-source samples back to fixture, document-fixture, or benchmark endpoints.
- `fixture-crosswalk`: companion endpoint that shows whether each public source has local fixture, legal-document fixture, and small-corpus coverage.
- `public-fixture-priority-queue`: companion endpoint that prioritizes LawBench, LexEval, LegalBench, LegalBench-RAG, CUAD, LexGLUE, CaseGen, and corpus-scale references into synthetic fixture work items without importing public examples.
- `resource_policy`: network, storage, and sample-size limits.
- `validation_commands`: focused tests that prove the sampler and release evidence indexes are wired.

## Safety

Do not commit raw public benchmark examples, client documents, personal data, gateway keys, emails, or model outputs. Store only source IDs, task labels, normalized observations, attribution notes, and review status unless license review explicitly permits snippets.

## Related Files

- `app/backend/services/legal_public_benchmark_sampler.py`
- `app/backend/services/legal_benchmark_fixture_crosswalk.py`
- `app/backend/tests/test_legal_public_benchmark_sampler.py`
- `app/backend/tests/test_legal_benchmark_fixture_crosswalk.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/LEGAL_REVIEW_BENCHMARK.md`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
