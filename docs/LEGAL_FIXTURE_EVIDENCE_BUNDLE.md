# Legal Fixture Evidence Bundle

The legal fixture evidence bundle aggregates the small legal benchmark evidence needed for release readiness, OSS support applications, and cheap-first model-routing reviews.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle
POST /api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle
```

`GET` returns a deterministic template. It marks the bundle `not_run` until fixture observations are supplied.

`POST` accepts the same payload shape as `/fixture-run-report`:

```json
{
  "observations": {
    "fixture-service-agreement-small": {
      "route": "fast",
      "output_text": "risk_matrix liability_cap missing_sla replacement_clause"
    }
  },
  "run_metadata": {
    "fixture-service-agreement-small": {
      "phase": "cheap_first",
      "model": "gemini-2.5-flash-lite",
      "estimated_cost_usd": 0.000123
    }
  }
}
```

## What It Contains

- component statuses for the benchmark suite, quick suite, fixture smoke evaluator, model matrix, prompt pack, gateway manifest, run plan, run report, and improvement plan,
- public benchmark sampler status for reviewed, resource-capped external benchmark plans,
- artifact references and archive fields for release evidence,
- validation commands for small local tests,
- release claims that are safe to make from synthetic fixture evidence,
- claims that must wait until observations pass,
- claims that must not be made from this bundle.

## Workflow

1. Fetch `/quick-suite` on low-resource machines, then fetch `/fixture-model-matrix`, `/prompt-pack`, `/gateway-manifest`, and `/fixture-run-plan`.
2. Fetch `/public-sampler` if public benchmark samples will be reviewed for the release.
3. Run cheap-first fixture batches one request at a time.
4. Submit normalized observations to `/fixture-smoke`.
5. Submit the same payload to `/fixture-run-report`.
6. Submit the payload to `/fixture-evidence-bundle`.
7. Use `/local-run-review` as the one-step version of steps 4-6 when a laptop can only run one or two fixture responses.
8. Archive the returned component statuses, release claims, validation commands, and evidence paths with release-readiness notes.

## Safety

- The service is deterministic and never calls a model or gateway.
- The response contains fixture IDs, scores, cost estimates, model IDs, and evidence paths only.
- Do not include real client documents, emails, gateway keys, passwords, or raw model outputs in payloads or committed evidence.

## Related Files

- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/backend/tests/test_legal_fixture_evidence_bundle.py`
- `app/backend/services/legal_fixture_quick_suite.py`
- `app/backend/tests/test_legal_fixture_quick_suite.py`
- `app/backend/services/legal_public_benchmark_sampler.py`
- `app/backend/tests/test_legal_public_benchmark_sampler.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_local_run_review.py`
- `app/backend/services/legal_fixture_model_matrix.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/LEGAL_REVIEW_BENCHMARK.md`
- `docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md`
- `docs/LEGAL_FIXTURE_QUICK_SUITE.md`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_FIXTURE_MODEL_MATRIX.md`
- `docs/LEGAL_FIXTURE_RUN_PLAN.md`
- `docs/LEGAL_FIXTURE_LOCAL_RUN_REVIEW.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
