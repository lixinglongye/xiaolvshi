# ModelOps Cheap-First Canary Approval Packet

`cheap_first_canary_approval_packet` converts the canary promotion decision into
a maintainer-facing approval checklist. It is the step after promotion decision
review and before any human-owned configuration change.

## Purpose

The packet helps maintainers inspect:

- which canary rows are ready for maintainer approval
- which rows are blocked, not ready, monitor-only, or rollback-review required
- required signoff roles for each row
- pre-approval checks that must be completed outside this service
- no-write and no-traffic-shift boundaries

It is metadata-only. It does not store approver identity, record approval,
write configuration, call a model gateway, persist rollout state, or shift
traffic.

## Endpoint

```http
GET /api/v1/aihub/models/cheap-first-canary-approval-packet
```

The full `/api/v1/aihub/models` payload includes
`cheap_first_canary_approval_packet`.

Posting sanitized observations to
`/api/v1/aihub/models/cheap-first-canary-observation` returns
`data.approval_packet` next to `data.promotion_decision` so the `/model-ops`
page can refresh approval evidence immediately after aggregate observations are
reviewed.

## Approval Statuses

- `approval_ready`: the source promotion decision is `advance_next_batch` and
  the row needs maintainer signoff before any default movement.
- `approval_blocked`: observations, source plan state, or reviewer evidence are
  not ready.
- `rollback_review_required`: rollback-required promotion rows must be reviewed
  before any default movement.
- `monitor_only`: the row represents an already-aligned current default and has
  no approval queued.
- `not_supplied`: no source promotion decision was supplied.

## Non-Claims

This packet does not:

- claim maintainer approval has happened
- record approver identity
- write `.env` or runtime configuration
- call NewAPI, Gemini, OpenAI, Google, or another gateway
- shift production traffic
- approve automatic canary rollout
- prove public benchmark scores
- prove production legal accuracy

## Validation

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_canary_approval_packet.py tests/test_model_ops_cheap_first_canary_promotion_decision.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

Related files:

- `app/backend/services/model_ops_cheap_first_canary_approval_packet.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_approval_packet.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_PROMOTION_DECISION.md`
