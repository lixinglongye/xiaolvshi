# Legal Public Fixture Priority Queue

The public fixture priority queue turns public legal benchmark source metadata into the next synthetic fixture work queue. It is designed for the user's low-resource constraint: it does not download datasets, copy public benchmark examples, call models, or require GPU resources.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/public-fixture-priority-queue
```

## What It Joins

- `legal_public_benchmark_sampler`: source IDs, license state, task fit, and capped sampling batches.
- `legal_benchmark_fixture_crosswalk`: benchmark case IDs, `fixture-*`, `ldoc-*`, and `small-corpus-*` metadata paths.
- `user_need_benchmark_coverage`: user-need IDs and high-priority coverage links.
- `legal_document_benchmark_fixtures.local_rule_baseline`: local no-model baseline status and score.
- `small_legal_document_corpus_expansion`: tiny synthetic zh-CN corpus coverage.

## Priority Behavior

The queue boosts public sources that are:

- high priority for product coverage;
- tied to high-priority user needs;
- Chinese legal task sources such as LawBench, LexEval, and CaseGen;
- missing a local synthetic document fixture or small-corpus mapping;
- still license-review-only and therefore safe for metadata planning, not raw text import.

LawBench is registered as a Chinese legal task-taxonomy source for local fixture planning. The queue uses it to prioritize synthetic zh-CN classification, evidence reasoning, citation, and document-structure fixtures without copying public benchmark examples.

## Safety Boundary

The response intentionally omits:

- public benchmark example text;
- dataset examples;
- local fixture snippets;
- small-corpus excerpts;
- prompts;
- model outputs;
- gateway payloads;
- credentials, emails, phone numbers, identity numbers, and client material.

It does not claim public benchmark scores, public dataset coverage, production accuracy, real client-document coverage, or default model changes.

## Validation

```bash
cd app/backend
python -m pytest tests/test_legal_public_fixture_priority_queue.py -q
python -m pytest tests/test_legal_public_benchmark_sampler.py tests/test_legal_benchmark_fixture_crosswalk.py tests/test_user_need_benchmark_coverage.py -q
cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/legal_public_fixture_priority_queue.py`
- `app/backend/tests/test_legal_public_fixture_priority_queue.py`
- `app/backend/routers/maintenance.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
