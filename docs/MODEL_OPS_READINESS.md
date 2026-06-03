# Model Ops Readiness

The project now aggregates model-operation checks into one release-oriented readiness result.

## Purpose

Model operations now include configuration audit, default optimization, gateway compatibility, Gemini lifecycle policy, runtime routing, reasoning effort policy, request parameter policy, request cost bounds, cache policy, route telemetry, route guardrails, callsite audit, capability matrix, routing replay, fallback chains, escalation policy, cost forecast, and cost guardrails. Reviewing each signal separately is error-prone before a release.

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
      "component_count": 19,
      "pass_count": 19,
      "warn_count": 0,
      "fail_count": 0,
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
- route guardrails,
- routing replay,
- fallback chains,
- escalation policy,
- cost forecast,
- cost guardrails.

Any required `fail` status blocks model-ops readiness. Any `warn` status requires maintainer review before treating the model stack as release-ready.

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
- `app/backend/services/model_lifecycle_policy.py`
- `app/backend/services/model_request_cost_bounds.py`
- `app/backend/services/model_cache_policy.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_ops_readiness.py`
- `app/backend/tests/test_model_default_optimization.py`
- `app/backend/tests/test_model_gateway_compatibility.py`
- `app/backend/tests/test_model_lifecycle_policy.py`
- `app/backend/tests/test_model_request_cost_bounds.py`
- `app/backend/tests/test_model_cache_policy.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
