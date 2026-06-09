# Legal Benchmark Fixture Crosswalk

The fixture crosswalk connects public legal benchmark source IDs to the local, laptop-safe evidence path used by this repository. It is metadata-only: it does not download public datasets, return local snippets, return small-corpus excerpts, call models, or claim public benchmark scores.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-crosswalk
```

## What It Maps

- Public source IDs such as LegalBench, LawBench, CUAD, LexGLUE, Pile of Law, LegalBench-RAG, LexEval, and CaseGen.
- Local legal-review benchmark case IDs such as `service-contract-risk`, `lease-dispute-evidence`, and `legal-rag-grounding`.
- Synthetic fixture IDs such as `fixture-service-agreement-small` and `fixture-low-text-pdf-page-small`.
- Local legal-document fixture IDs such as `ldoc-contract-review-mini`, `ldoc-evidence-catalog-mini`, and `ldoc-legal-opinion-mini`.
- Tiny small-corpus item IDs such as `small-corpus-service-004` and `small-corpus-labor-001`.

## Safety Boundary

The response intentionally omits:

- public benchmark example text,
- local fixture sample text,
- small-corpus synthetic excerpts,
- generated legal document text,
- raw model output,
- prompts,
- credentials,
- emails, phone numbers, identity numbers, and API keys.

## Product Use

Use the crosswalk before adding new benchmark samples or claiming broader legal coverage. A source should have a local fixture path and, for document-generation or legal-RAG claims, at least one `ldoc-*` document fixture mapping.

Use `/api/v1/maintenance/legal-review-benchmark/public-fixture-priority-queue` after the crosswalk when you need the next synthetic fixture work items ranked by LawBench/LexEval/LegalBench source priority, high-priority user needs, local baseline status, and document/corpus mapping gaps.

The `gap_queue` highlights sources that still need license review, document fixture mapping, or small-corpus mapping. Corpus-scale sources can remain catalog-only until a resource-controlled CI job is approved.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_benchmark_fixture_crosswalk.py -q
python -m pytest tests/test_legal_public_benchmark_sampler.py tests/test_user_need_benchmark_coverage.py -q
```

## Related Files

- `app/backend/services/legal_benchmark_fixture_crosswalk.py`
- `app/backend/tests/test_legal_benchmark_fixture_crosswalk.py`
- `app/backend/routers/maintenance.py`
- `app/backend/services/legal_public_benchmark_sampler.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/services/legal_document_benchmark_coverage.py`
- `app/backend/services/small_legal_document_corpus_expansion.py`
