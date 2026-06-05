# Model Ops Readiness

The project now aggregates model-operation checks into one release-oriented readiness result.

## Purpose

Model operations now include configuration audit, default optimization, gateway compatibility, gateway health planning, optional gateway probe evaluation evidence, Gemini lifecycle policy, Gemini catalog source audit, runtime routing, reasoning effort policy, request parameter policy, request cost bounds, cache policy, route telemetry, route telemetry repository, route telemetry operations summary, route telemetry triage queue, route telemetry remediation plan, route guardrails, cheap-first route quality budgets, callsite audit, capability matrix, routing replay, fallback chains, escalation policy, cost forecast, cost guardrails, Gemini/NewAPI cheap-first calibration, price refresh monitoring, and ModelOps load performance budgets. Reviewing each signal separately is error-prone before a release.

`model_ops_readiness` combines these signals into one pass/warn/fail result.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes:

```json
{
  "model_ops_readiness": {
    "status": "pass",
    "release_recommendation": "ready_for_model_ops_release",
    "summary": {
      "component_count": 31,
      "required_component_count": 30,
      "optional_component_count": 1,
      "pass_count": 30,
      "warn_count": 0,
      "fail_count": 0,
      "required_warning_count": 0,
      "optional_review_count": 0,
      "required_failure_count": 0,
      "optional_failure_count": 0,
      "blocking_count": 0,
      "warning_count": 0
    }
  }
}
```

The frontend `/model-ops` page shows the readiness summary near the top of the page, followed by a component table.

## Components

The readiness service checks:

- model configuration audit,
- default optimization plan,
- gateway compatibility,
- gateway health plan,
- Gemini variant matrix,
- Gemini catalog source audit,
- gateway probe evaluation,
- Gemini lifecycle policy,
- budget policy,
- capability matrix,
- runtime router,
- reasoning policy,
- request policy,
- request cost bounds,
- cache policy,
- callsite audit,
- route telemetry,
- route telemetry repository,
- route telemetry operations summary,
- route telemetry triage queue,
- route telemetry remediation plan,
- route guardrails,
- cheap-first route quality budget,
- routing replay,
- fallback chains,
- escalation policy,
- cost forecast,
- cost guardrails,
- Gemini/NewAPI cheap-first calibration,
- Gemini/NewAPI price refresh monitor,
- ModelOps performance budget.

Any required `fail` status blocks model-ops readiness. Any `warn` status requires maintainer review before treating the model stack as release-ready. The summary separates `required_warning_count`, `required_failure_count`, and `optional_review_count` so manual evidence does not look like a required gate failure. `gateway-probe-evaluation` is optional manual evidence: missing or `not_run` results warn but do not block, while supplied failing probe evidence is surfaced as a warning with its underlying blocker IDs. After a maintainer posts sanitized gateway probe results, `/api/v1/aihub/models` uses the latest in-process sanitized snapshot for this optional component; rejected payloads only contribute a minimal safe failure snapshot.

`model-ops-performance-budget` is required evidence for the local operations UI. It checks that the heavyweight `/api/v1/aihub/models` payload has a short backend cache, the frontend has a request timeout and abort path, and the page does not repeat the cheap-first calibration request on first load.

`route-quality-budget` is required evidence for cheap-first model routing. It checks that each task has deterministic quality gates, a cheap-start model where appropriate, and a visible review action when a runtime default lacks the required task capabilities.

`catalog-source-audit` is required evidence for source-backed Gemini catalog maintenance. It checks official source URL coverage, pricing metadata visibility, stable Flash-Lite high-frequency defaults, and preview/premium default drift before model changes are promoted.

## Release Readiness

`model-ops-readiness` is a required release-readiness check. Maintainers should run:

```bash
python -m pytest tests/test_model_ops_readiness.py -q
```

## Safety

The service only aggregates existing status and summary metadata. It does not store prompts, documents, file names, API keys, passwords, emails, user identifiers, or raw model output.

## Related files

- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/model_default_optimization.py`
- `app/backend/services/model_gateway_compatibility.py`
- `app/backend/services/model_gateway_health_plan.py`
- `app/backend/services/model_gateway_probe_evaluation.py`
- `app/backend/services/model_lifecycle_policy.py`
- `app/backend/services/model_catalog_source_audit.py`
- `app/backend/services/model_request_cost_bounds.py`
- `app/backend/services/model_cache_policy.py`
- `app/backend/services/route_telemetry_repository.py`
- `app/backend/services/route_telemetry_ops_summary.py`
- `app/backend/services/route_telemetry_triage_queue.py`
- `app/backend/services/route_telemetry_remediation_plan.py`
- `app/backend/services/gemini_newapi_cheap_first_calibration.py`
- `app/backend/services/model_ops_performance_budget.py`
- `app/backend/services/model_route_quality_budget.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_ops_readiness.py`
- `app/backend/tests/test_model_ops_performance_budget.py`
- `app/backend/tests/test_model_route_quality_budget.py`
- `app/backend/tests/test_model_default_optimization.py`
- `app/backend/tests/test_model_gateway_compatibility.py`
- `app/backend/tests/test_model_gateway_health_plan.py`
- `app/backend/tests/test_model_gateway_probe_evaluation.py`
- `app/backend/tests/test_model_lifecycle_policy.py`
- `app/backend/tests/test_model_catalog_source_audit.py`
- `app/backend/tests/test_model_request_cost_bounds.py`
- `app/backend/tests/test_model_cache_policy.py`
- `app/backend/tests/test_route_telemetry_repository.py`
- `app/backend/tests/test_route_telemetry_ops_summary.py`
- `app/backend/tests/test_route_telemetry_triage_queue.py`
- `app/backend/tests/test_route_telemetry_remediation_plan.py`
- `app/backend/tests/test_gemini_newapi_cheap_first_calibration.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
