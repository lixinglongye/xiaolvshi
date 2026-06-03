# Legal Fixture Improvement Plan

The fixture improvement planner turns local legal fixture smoke-test gaps into prompt and report-schema actions.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-improvements
POST /api/v1/maintenance/legal-review-benchmark/fixture-improvements
```

`GET` returns a `not_run` plan and the fixture observation template.

`POST` accepts the same observation object used by `/fixture-smoke`:

```json
{
  "fixture-service-agreement-small": {
    "route": "fast",
    "output_text": "risk matrix ... liability cap ..."
  }
}
```

## What It Returns

- `status`: `not_run`, `ready`, `review_recommended`, or `needs_improvement`.
- `actions`: prompt and report-schema improvements for missing fixture signals and task outputs.
- `grouped_actions`: the same actions grouped by report section.
- `smoke_result`: fixture smoke scores and missing labels.
- `privacy_note`: reminder that observed output text is evaluated in request scope and is not returned.

## Use

Use this after model, prompt, report schema, extraction, or safety changes:

1. Run the small fixture smoke test.
2. Send observations to `/fixture-improvements`.
3. Update the target prompt clause or report schema field named in each high-priority action.
4. Re-run the fixture smoke test and the legal benchmark tests.

## Related Files

- `app/backend/services/legal_fixture_improvement.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/tests/test_legal_fixture_improvement.py`
- `app/backend/tests/test_legal_review_benchmark.py`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
