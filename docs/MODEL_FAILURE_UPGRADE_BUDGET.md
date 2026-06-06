# Model Failure Upgrade Budget

`model-failure-upgrade-budget` is a metadata-only gate for deciding what should
happen after one cheap-first model attempt fails.

## Purpose

The gate answers a narrow question before any retry is executed:

- keep retrying within the current cheap tier,
- run a verification step,
- retry on the next non-premium model,
- stop because a hard-stop signal or attempt budget is exhausted,
- or allow a premium upgrade only after operator review and quota checks pass.

It is based on cheap-first cascade research such as FrugalGPT
<https://arxiv.org/abs/2305.05176>, RouteLLM
<https://arxiv.org/abs/2406.18665>, and Language Model Cascades
<https://arxiv.org/abs/2207.10342>. The local implementation uses only routing
metadata, catalog cost tiers, escalation policy, estimated token cost, attempt
counters, and premium quota policy.

## Endpoints

```http
GET /api/v1/aihub/models/failure-upgrade-budget
GET /api/v1/aihub/models/failure-upgrade-budget-template
POST /api/v1/aihub/models/failure-upgrade-budget
```

The full `/api/v1/aihub/models` payload also includes
`failure_upgrade_budget`, and `/model-ops` renders it between the route quality
budget and cheap-first escalation budget panels.

## Payload

Allowed fields are sanitized metadata only:

- `task`
- `attempt_index`
- `failure_signals`
- `current_model`
- `prompt_tokens`
- `completion_tokens`
- `plan_type`
- `subscription_status`
- `user_role`
- `premium_escalations_used_month`
- `operator_approved`

Forbidden fields include credentials, headers, prompts, messages, copied
document text, raw responses, raw model output, emails, phone numbers, and
identity numbers. Forbidden keys or secret-like values cause
`reject_unsanitized_payload`.

## Decisions

- `allow_retry_up`: a bounded non-premium retry is available.
- `continue_current_tier_verification`: the next step should verify before a
  stronger retry.
- `allow_premium_upgrade_after_operator_review`: premium is allowed only when
  operator approval, quota, attempt budget, hard-stop, and cost checks all pass.
- `block_premium_upgrade`: premium quota or approval policy blocks the upgrade.
- `block_upgrade`: a remaining blocker prevents any upgrade.
- `stop_hard_signal`: a hard-stop signal prevents retry.
- `stop_attempt_budget_exhausted`: no attempts remain.
- `reject_unsanitized_payload`: forbidden fields or secret-like values were
  detected.

## Safety Boundary

The service does not call models, gateways, NewAPI, Gemini, OpenAI, or Google.
It does not execute retries, consume quota, shift traffic, write configuration,
or persist submitted payloads. Responses include only task IDs, failure signal
IDs, model IDs, cost tiers, estimated aggregate cost, quota reason codes, check
IDs, and recommended maintainer actions.

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_failure_upgrade_budget.py tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/model_failure_upgrade_budget.py`
- `app/backend/tests/test_model_failure_upgrade_budget.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/model_ops_cheap_first_release_decision.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/frontend_ui_regression_gate.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/maintenance_evidence.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
