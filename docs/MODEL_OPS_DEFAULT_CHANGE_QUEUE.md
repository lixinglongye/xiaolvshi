# ModelOps Default Change Queue

`default_change_queue` turns cheap-first ModelOps evidence into maintainer
review items before anyone changes default model environment variables.

## Purpose

The queue separates three things:

- defaults that are already aligned and need no action
- proposed cheap-first changes that require maintainer review
- proposed changes blocked by release, catalog, price, or optimization checks

It gives reviewers a visible task/env-var/model table without writing
configuration or calling a gateway.

## Endpoint

```http
GET /api/v1/aihub/models/default-change-queue
```

The full `/api/v1/aihub/models` payload also includes `default_change_queue`.
`cheap_first_canary_plan` consumes this queue downstream and turns ready,
review-required, blocked, and no-action rows into staged canary review steps.

## Inputs

The service consumes existing metadata only:

- `cheap_first_release_decision`
- `default_optimization`
- `gateway_probe_evaluation`
- `price_refresh_monitor`
- `catalog_source_audit`

It reads task IDs, env var names, model IDs, statuses, reason codes, and
estimated savings. It does not read secrets, prompts, legal documents, raw model
output, raw probe payloads, or client data.

## Queue Status

- `no_action`: the current runtime default already matches the recommended
  cheap-first model.
- `ready`: a change could proceed after standard validation and maintainer
  approval.
- `review_required`: the change is not blocked, but release decision, gateway
  probe, catalog, price, operator-review, or optimization evidence requires a
  human review.
- `blocked`: the change must not be applied until blocking ModelOps checks pass.

## Non-Claims

This queue does not:

- write `.env` or runtime configuration
- call NewAPI, Gemini, OpenAI, Google, or another gateway
- prove live gateway health
- prove public benchmark scores
- prove production legal accuracy
- approve automatic default changes

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_default_change_queue.py tests/test_model_ops_cheap_first_release_decision.py tests/test_model_default_optimization.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

Related files:

- `app/backend/services/model_ops_default_change_queue.py`
- `app/backend/tests/test_model_ops_default_change_queue.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_PLAN.md`
