# Legal Fixture Run Plan

The legal fixture run plan turns safe gateway request manifests into a cheap-first local execution schedule.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/fixture-run-plan
GET /api/v1/maintenance/legal-review-benchmark/local-run-package
```

The endpoint returns batch and step metadata only. It does not call NewAPI, Gemini, OpenAI-compatible gateways, or the app AI hub.

## What It Contains

- `batches`: serial cheap-first batches and conditional escalation batches grouped by task and model.
- `steps`: fixture-level run steps with model, task, request budget, smoke route, observation target, and improvement target.
- `estimated_min_cost_usd`: cost estimate for cheap-first steps only.
- `estimated_max_cost_usd`: worst-case estimate if every eligible fixture needs escalation.
- `max_parallel_requests`: fixed at `1` for laptop-safe local smoke runs.

Use `/local-run-package` for the smallest executable subset: it wraps selected cheap-first run-plan steps with request JSON bodies, PowerShell/curl templates, observation slots, and run-report payload scaffolding.

## Workflow

1. Fetch `/fixture-model-matrix` to inspect model candidates and premium boundaries.
2. For low-resource machines, fetch `/quick-suite` first and run only the selected fixture subset.
3. Fetch `/local-run-package?fixture_limit=1` or `/fixture-run-plan`.
4. Run `cheap_first` batches first, one request at a time.
5. Submit normalized outputs to `/fixture-smoke`.
6. Run only the `escalation_if_needed` steps whose cheap-first smoke result fails or leaves high-priority improvement actions.
7. Submit the same observations to `/fixture-run-report`.
8. Submit the same observations to `/fixture-evidence-bundle`.
9. Attach smoke scores, the run report, and the evidence bundle to release-readiness evidence before changing default model routes.

## Safety

- The plan references synthetic fixture prompts and placeholder credentials only.
- It never stores observations or raw model outputs.
- Do not commit real client documents, gateway keys, emails, or production model outputs.

## Related Files

- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/services/legal_fixture_local_run_package.py`
- `app/backend/services/legal_fixture_model_matrix.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/backend/services/legal_fixture_gateway_manifest.py`
- `app/backend/tests/test_legal_fixture_run_plan.py`
- `app/backend/tests/test_legal_fixture_local_run_package.py`
- `app/backend/tests/test_legal_fixture_model_matrix.py`
- `app/backend/tests/test_legal_fixture_run_report.py`
- `app/backend/tests/test_legal_fixture_evidence_bundle.py`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/LEGAL_FIXTURE_MODEL_MATRIX.md`
- `docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md`
- `docs/LEGAL_FIXTURE_LOCAL_RUN_PACKAGE.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
