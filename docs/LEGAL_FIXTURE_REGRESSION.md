# Legal Fixture Regression

`legal_fixture_regression.py` compares two cheap-first legal fixture runs using the same local fixture scoring as `/fixture-run-report`.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-regression
POST /api/v1/maintenance/legal-review-benchmark/fixture-regression
```

## Payload

```json
{
  "baseline": {
    "observations": {
      "fixture-service-agreement-small": {
        "route": "cheap",
        "output_text": "normalized local model output used only for scoring"
      }
    },
    "run_metadata": {
      "fixture-service-agreement-small": {
        "phase": "cheap_first",
        "model": "gemini-2.5-flash-lite",
        "estimated_cost_usd": 0.0001,
        "http_status": 200
      }
    }
  },
  "current": {
    "observations": {},
    "run_metadata": {}
  },
  "policy": {
    "score_regression_threshold": -0.15,
    "cost_increase_warn_ratio": 0.25,
    "missing_current_fixture_is_regression": true
  }
}
```

The service builds a baseline and current fixture run report, then compares fixture status, score, recommended next step, missing-signal counts, missing-task counts, model metadata, and observed cost.

## Output

The response includes:

- `status`: `not_run`, `pass`, `warn`, or `fail`,
- `release_decision`: whether current cheap-first defaults can move forward,
- `summary`: compared fixture count, regressed fixture count, newly blocking fixture count, resolved blocker count, average score delta, and cost delta,
- `fixture_deltas`: one metadata-only row per fixture,
- `regressed_fixture_ids`, `newly_blocking_fixture_ids`, and `resolved_blocking_fixture_ids`,
- `recommended_actions` for release review.

## Release And Ledger Evidence

`legal-fixture-regression-comparison` is optional release readiness evidence.
If it is not run, it stays review-only and does not block ordinary release
candidate preparation. If a maintainer submits a failed comparison, release
readiness includes it in `failed_check_ids` so the candidate is blocked until
fixture regressions are fixed or explicitly waived.

`POST /api/v1/maintenance/continuous-update-ledger` can receive the comparison
under `low_resource_fixture_regression`. The ledger keeps only status,
release-decision, count, cost-delta, safe fixture-id, and dropped raw-field
metadata. It does not return `fixture_deltas` raw scoring inputs, run report
payloads, gateway responses, prompts, legal text, client documents, headers,
credentials, or model outputs.

## Safety

The comparator does not call NewAPI, Gemini, OpenAI, a public benchmark, or any gateway. Raw `output_text`, gateway responses, prompts, client documents, emails, headers, and credentials are only used as local scoring inputs and are not returned. The response records only fixture IDs, scores, statuses, routes, model names, costs, deltas, and reason codes.

## Validation

```bash
python -m pytest tests/test_legal_fixture_regression.py tests/test_legal_fixture_run_report.py tests/test_continuous_update_ledger.py tests/test_release_readiness.py -q
```

## Related Files

- `app/backend/services/legal_fixture_regression.py`
- `app/backend/tests/test_legal_fixture_regression.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/release_readiness.py`
- `app/backend/routers/maintenance.py`
