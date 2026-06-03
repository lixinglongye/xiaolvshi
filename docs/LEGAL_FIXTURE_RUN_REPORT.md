# Legal Fixture Run Report

The legal fixture run report turns fixture smoke observations into cheap-first release and escalation decisions.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-run-report
POST /api/v1/maintenance/legal-review-benchmark/fixture-run-report
```

`GET` returns a `not_run` report template. `POST` accepts fixture observations and optional run metadata:

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

## Decisions

- `run_cheap_first_fixture_batches`: no observations have been submitted.
- `hold_default_changes_and_fix_selected_fixtures`: one or more fixtures need escalation or high-priority prompt/schema fixes.
- `review_warnings_before_release`: results are usable but need maintainer review before release readiness is marked pass.
- `keep_cheap_first_defaults`: cheap-first fixture observations pass without high-priority improvement actions.

## Safety

- The service scores request payloads only and does not call a model.
- The response returns scores, fixture IDs, cost summaries, and next actions, not raw model output text.
- Do not commit real gateway keys, client documents, emails, or production model outputs.

## Related Files

- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_model_matrix.py`
- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/tests/test_legal_fixture_run_report.py`
- `app/backend/tests/test_legal_fixture_model_matrix.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/LEGAL_FIXTURE_MODEL_MATRIX.md`
- `docs/LEGAL_FIXTURE_RUN_PLAN.md`
