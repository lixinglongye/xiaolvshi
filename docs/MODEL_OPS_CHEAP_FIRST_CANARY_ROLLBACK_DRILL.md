# ModelOps Cheap-First Canary Rollback Drill

`cheap_first_canary_rollback_drill` converts canary approval evidence into a
metadata-only rollback rehearsal packet. It is the required release gate after
the approval packet and before any human-owned default movement.

## Purpose

The packet helps maintainers inspect:

- which approval rows are ready for rollback rehearsal
- which rows are blocked or require failed-trigger review
- required reviewer roles before a drill can be scheduled
- holdout confirmation and rollback trigger checklist labels
- no-write, no-gateway, no-traffic-shift, and no-rollback-execution boundaries

It does not execute rollback, write configuration, persist drill state, call a
model gateway, record approver identity, or shift production traffic.

## Endpoint

```http
GET /api/v1/aihub/models/cheap-first-canary-rollback-drill
```

The full `/api/v1/aihub/models` payload includes
`cheap_first_canary_rollback_drill`. Posting sanitized canary observations to
`/api/v1/aihub/models/cheap-first-canary-observation` also returns
`data.rollback_drill` next to the observation review, promotion decision, and
approval packet.

## Drill Statuses

- `drill_ready`: approval evidence is ready and rehearsal roles/checklists are
  available for maintainer review.
- `rollback_drill_required`: failed observations or rollback-required promotion
  rows need trigger review before any default movement.
- `drill_blocked`: approval evidence, observations, or source promotion state
  are missing or blocked.
- `monitor_only`: the row tracks an already-aligned current default and has no
  rollback drill queued.

## Required Release Gate

`model-ops-cheap-first-canary-rollback-drill` is required release evidence for
cheap-first default movement. The validation command is:

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_canary_rollback_drill.py tests/test_model_ops_cheap_first_canary_approval_packet.py tests/test_model_ops_cheap_first_canary_promotion_decision.py -q
```

The gate is metadata-only. Passing it proves that rollback rehearsal evidence is
reviewable; it does not prove a rollback was executed or that production traffic
was shifted.

## Non-Claims

This packet does not:

- execute rollback
- write `.env` or runtime configuration
- persist drill records
- call NewAPI, Gemini, OpenAI, Google, or another gateway
- shift production traffic
- record approver identity
- approve automatic canary rollout
- prove public benchmark scores
- prove production legal accuracy

## Related Files

- `app/backend/services/model_ops_cheap_first_canary_rollback_drill.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_rollback_drill.py`
- `app/backend/services/model_ops_cheap_first_canary_approval_packet.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_approval_packet.py`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_APPROVAL_PACKET.md`
