# ModelOps Cheap-First Canary Change Manifest

`cheap_first_canary_change_manifest` is the metadata-only release evidence that
turns rollback-drill readiness into a maintainer review packet for proposed
cheap-first default edits. It is the required release gate after rollback drill
evidence and before any human-owned configuration change.

## Purpose

The manifest should help maintainers inspect:

- external change-set metadata for env var names and model ids
- source approval and rollback-drill evidence ids
- rollback preparedness and holdout percentages
- required validation commands before a manual config edit
- prerequisites and operator steps for the maintainer-owned change process
- no-write, no-secret, no-gateway, and no-traffic-shift boundaries

The full `/api/v1/aihub/models` payload includes
`cheap_first_canary_change_manifest`. Posting sanitized canary observations to
`/api/v1/aihub/models/cheap-first-canary-observation` also returns
`data.change_manifest` next to the observation review, promotion decision,
approval packet, and rollback drill.

## Required Release Gate

`model-ops-cheap-first-canary-change-manifest` is required release evidence for
cheap-first default movement. The validation command is:

```powershell
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_canary_change_manifest.py tests/test_model_ops_cheap_first_canary_rollback_drill.py tests/test_model_ops_cheap_first_canary_approval_packet.py -q
```

The gate should pass only when the manifest remains metadata-only and can be
reviewed without copying secret values, raw prompts, raw legal text, raw model
outputs, account identifiers, or approval identities.

## Expected Manifest Rows

Each row should contain only compact metadata such as:

- source canary step id
- task and phase labels
- env var name when the source plan has one
- current model id and recommended model id
- source approval item id
- source rollback drill item id
- approval and rollback drill status
- external change-set metadata with `apply_mode: manual_only`
- prerequisites and operator steps
- manual maintainer action text

## Non-Claims

This manifest does not:

- write `.env` or runtime configuration
- call NewAPI, Gemini, OpenAI, Google, or another gateway
- shift production traffic
- execute rollback
- persist drill or approval records
- record approver identity
- store API keys, passwords, account identifiers, prompts, legal text, or raw
  model output
- claim automatic canary rollout or automatic default promotion
- prove public benchmark scores or production legal accuracy

## Related Files

- `app/backend/services/model_ops_cheap_first_canary_change_manifest.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_change_manifest.py`
- `app/backend/services/model_ops_cheap_first_canary_rollback_drill.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_rollback_drill.py`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_ROLLBACK_DRILL.md`
