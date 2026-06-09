# Model Gateway Probe Runbook Gate

`model_gateway_probe_runbook_gate.py` joins the NewAPI channel bootstrap, runtime gateway configuration, gateway health plan, and latest sanitized gateway probe evaluation into one ordered maintainer runbook.

It is metadata-only. It does not call NewAPI, Gemini, OpenAI, Google, yibuapi, gateways, app AI endpoints, models, or the network. It does not write `.env`, source configuration, default routes, or traffic decisions.

## Endpoint

```http
GET /api/v1/aihub/models/gateway-probe-runbook-gate
POST /api/v1/aihub/models/gateway-probe-runbook-gate
```

The aggregate `GET /api/v1/aihub/models` response also includes `gateway_probe_runbook_gate`, and the ModelOps page renders the same panel between the gateway health plan and gateway probe evaluation.

## Runbook Order

1. Normalize runtime channel.
2. Verify secret boundary.
3. Run list-models first.
4. Run cheap JSON probe.
5. Optionally run image smoke.
6. Run small synthetic legal fixture smoke.
7. Review any default-change proposal.

The gate requires model-list evidence before cheap probe readiness, cheap JSON probe evidence before legal fixture smoke, and maintainer review before any default change. The gate never performs those actions automatically.

## Safe Evidence

The service accepts already-sanitized source packets or builds them locally from existing metadata services. It returns:

- step status, next action, source statuses, and evidence links,
- pass/warn/fail checks for ordered runbook readiness,
- privacy flags proving credentials, raw probe payloads, prompts, legal text, gateway responses, and model output are not included,
- claim flags proving live gateway execution, actual key validation, model inventory validation, default changes, pricing accuracy, and legal quality are not claimed.

## Validation

```bash
python -m pytest tests/test_model_gateway_probe_runbook_gate.py tests/test_model_gateway_health_plan.py tests/test_model_gateway_probe_evaluation.py tests/test_model_gateway_runtime_configuration.py tests/test_model_ops_newapi_channel_bootstrap.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q
cd ../frontend && npm run typecheck && npm run ui:regression
```

## Related Files

- `app/backend/services/model_gateway_probe_runbook_gate.py`
- `app/backend/tests/test_model_gateway_probe_runbook_gate.py`
- `app/backend/services/model_gateway_health_plan.py`
- `app/backend/services/model_gateway_probe_evaluation.py`
- `app/backend/services/model_gateway_runtime_configuration.py`
- `app/backend/services/model_ops_newapi_channel_bootstrap.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/MODEL_GATEWAY_HEALTH_PLAN.md`
- `docs/MODEL_GATEWAY_PROBE_EVALUATION.md`
