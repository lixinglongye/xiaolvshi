# Legal Fixture Run Plan

The legal fixture run plan turns safe gateway request manifests into a cheap-first local execution schedule.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-run-plan
```

The endpoint returns batch and step metadata only. It does not call NewAPI, Gemini, OpenAI-compatible gateways, or the app AI hub.

## What It Contains

- `batches`: serial cheap-first batches and conditional escalation batches grouped by task and model.
- `steps`: fixture-level run steps with model, task, request budget, smoke route, observation target, and improvement target.
- `estimated_min_cost_usd`: cost estimate for cheap-first steps only.
- `estimated_max_cost_usd`: worst-case estimate if every eligible fixture needs escalation.
- `max_parallel_requests`: fixed at `1` for laptop-safe local smoke runs.

## Workflow

1. Fetch `/fixture-run-plan`.
2. Run `cheap_first` batches first, one request at a time.
3. Submit normalized outputs to `/fixture-smoke`.
4. Run only the `escalation_if_needed` steps whose cheap-first smoke result fails or leaves high-priority improvement actions.
5. Submit the same observations to `/fixture-run-report`.
6. Attach smoke scores and the run report to release-readiness evidence before changing default model routes.

## Safety

- The plan references synthetic fixture prompts and placeholder credentials only.
- It never stores observations or raw model outputs.
- Do not commit real client documents, gateway keys, emails, or production model outputs.

## Related Files

- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_gateway_manifest.py`
- `app/backend/tests/test_legal_fixture_run_plan.py`
- `app/backend/tests/test_legal_fixture_run_report.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
