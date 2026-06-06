# Model Ops Readiness

The project now aggregates model-operation checks into one release-oriented readiness result.

## Purpose

Model operations now include configuration audit, default template alignment, default optimization, gateway compatibility, gateway health planning, optional gateway probe evaluation evidence, Gemini lifecycle policy, Gemini catalog source audit, observed Gemini intake, candidate patch planning, runtime routing, reasoning effort policy, request parameter policy, request cost bounds, cache policy, route telemetry, route telemetry repository, route telemetry operations summary, route telemetry triage queue, route telemetry remediation plan, route guardrails, cheap-first route quality budgets, cheap-first escalation budgets, callsite audit, capability matrix, routing replay, fallback chains, escalation policy, cost forecast, cost guardrails, Gemini/NewAPI cheap-first calibration, price refresh monitoring, ModelOps load performance budgets, release decision packets, default-change queues, canary packets, and maintainer execution evidence. Reviewing each signal separately is error-prone before a release.

`model_ops_readiness` combines these signals into one pass/warn/fail result.
`cheap_first_release_decision` consumes this readiness result downstream, along
with focused Gemini/cheap-first signals, but it is not counted as another
readiness component.

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
      "component_count": 50,
      "required_component_count": 49,
      "optional_component_count": 1,
      "pass_count": 50,
      "warn_count": 0,
      "fail_count": 0,
      "required_warning_count": 0,
      "optional_review_count": 0,
      "required_failure_count": 0,
      "optional_failure_count": 0,
      "blocking_count": 0,
      "warning_count": 0,
      "warning_drilldown_count": 0,
      "p0_warning_count": 0,
      "p1_warning_count": 0,
      "p2_warning_count": 0
    },
    "warning_category_counts": {},
    "warning_drilldown": []
  }
}
```

The frontend `/model-ops` page shows the readiness summary near the top of the page, followed by the warning drilldown, warning category counts, and component table.

## Warning Drilldown

`warning_drilldown` expands every non-passing readiness component into an actionable row:

- `severity`: `p0_blocking_required`, `p1_required_review`, or `p2_optional_review`.
- `priority`: numeric sort key used to put blocking and high-risk warning rows first.
- `warning_category`: one of `manual_evidence_gap`, `canary_evidence_gap`, `catalog_pricing_review`, `runtime_telemetry_review`, `routing_quality_review`, `cost_guardrail_review`, `release_evidence_review`, `configuration_review`, `resilience_review`, or `general_review`.
- `next_action`: the maintainer action to resolve or accept the warning.
- `validation_hint`: the local pytest command most relevant to the warning class.
- `privacy_boundary`: explicit metadata-only flags showing that the row does not include prompts, raw payloads, model outputs, credentials, gateway responses, or network/model calls.

`warning_category_counts` mirrors the drilldown rows as aggregate counts for UI filtering and release review. The drilldown never calls NewAPI, Gemini, OpenAI, Google, gateways, or the network; it only classifies existing readiness metadata already present in the `/api/v1/aihub/models` response.

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
- cheap-first escalation budget,
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

`cheap-first-escalation-budget` is required evidence for cheap-first cascade cost control. It checks aggregate failure, verification, escalation, premium escalation, operator review, and wasted escalation spend rates before a cheap Gemini/NewAPI default can be promoted.

`catalog-source-audit` is required evidence for source-backed Gemini catalog maintenance. It checks official source URL coverage, pricing metadata visibility, stable Flash-Lite high-frequency defaults, and preview/premium default drift before model changes are promoted.

`cheap_first_release_decision` is a downstream release decision packet that uses
readiness plus cheap-first calibration, Gemini variant review, catalog source
audit, route quality, escalation budget, price refresh, and ModelOps performance
signals to decide whether current cheap-first defaults can remain and whether
new default promotion requires maintainer review.

The readiness warning drilldown is release evidence for maintainers reviewing cheap-first model changes. It makes warning ownership visible without exposing legal text, prompts, model output, provider credentials, request bodies, response bodies, or gateway payloads.

## Release Readiness

`model-ops-readiness` is a required release-readiness check. Maintainers should run:

```bash
python -m pytest tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q && cd ../frontend && npm run typecheck && npm run ui:regression
```

## Safety

The service only aggregates existing status and summary metadata. It does not store prompts, documents, file names, API keys, passwords, emails, user identifiers, raw payloads, gateway responses, or raw model output.

## Related files

- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/model_ops_cheap_first_release_decision.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/maintenance_evidence.py`
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
- `app/backend/services/model_ops_cheap_first_escalation_budget.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_ops_readiness.py`
- `app/backend/tests/test_release_readiness.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/tests/test_maintenance_evidence.py`
- `app/backend/tests/test_model_ops_cheap_first_release_decision.py`
- `app/backend/tests/test_model_ops_performance_budget.py`
- `app/backend/tests/test_model_route_quality_budget.py`
- `app/backend/tests/test_model_ops_cheap_first_escalation_budget.py`
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
- `app/frontend/scripts/ui-regression.mjs`
