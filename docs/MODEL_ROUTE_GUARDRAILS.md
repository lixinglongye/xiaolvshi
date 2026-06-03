# Model Route Guardrails

The project now turns aggregate route telemetry into release-oriented guardrail checks.

## Purpose

`route_telemetry` shows what happened at runtime. `route_guardrails` decides whether those routing patterns are acceptable before a maintainer treats a build as release-ready.

The guardrails protect the cheap-first model policy by checking:

- route telemetry availability,
- route failure rate,
- over-budget requested model ratio,
- downgrade ratio,
- operator-review-gated request ratio,
- unknown-price gateway model count,
- allowed over-budget request count.

Empty telemetry does not block a release by itself. Ratio checks pass with a no-data reason until staging or production traffic has routed text calls to evaluate.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `route_guardrails` next to `route_telemetry`, `cost_guardrails`, and the runtime router data:

```json
{
  "route_guardrails": {
    "status": "pass",
    "summary": {
      "request_count": 0,
      "failure_rate": 0.0,
      "over_budget_route_ratio": 0.0,
      "downgrade_ratio": 0.0,
      "operator_review_route_ratio": 0.0,
      "unknown_price_model_count": 0,
      "allowed_over_budget_count": 0
    },
    "blocking_check_ids": [],
    "warning_check_ids": []
  }
}
```

The frontend `/model-ops` page shows route guardrail summary cards and a check table.

## Release Readiness

`model-route-guardrails` is a required release-readiness check. Maintainers should run:

```bash
python -m pytest tests/test_model_route_guardrails.py -q
```

When route guardrails warn or fail, the recommended actions point to the routing drift to inspect before increasing budgets or accepting premium model usage.

## Safety

Route guardrails only evaluate aggregate route counters. They do not store prompts, uploaded documents, file names, API keys, passwords, emails, user identifiers, or raw model output.

## Related files

- `app/backend/services/model_route_guardrails.py`
- `app/backend/services/model_route_telemetry.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_route_guardrails.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
