# ModelOps Cheap-First Maintainer Execution Checklist

## Purpose

The cheap-first maintainer execution checklist turns the existing ModelOps evidence chain into a single manual review packet for low-cost Gemini default work.

It is designed for maintainer visibility, not for automatic execution. The service helps answer:

- Which cheap-first tasks are ready for an external manual change request?
- Which tasks are blocked or need review?
- Which evidence is missing before a maintainer can approve a default change?
- Which safety boundary proves this service did not write configuration, call a gateway, or shift traffic?

## Inputs

The checklist consumes existing metadata-only ModelOps signals:

- `cheap_first_priority_queue`
- `cheap_first_release_decision`
- `cheap_first_canary_plan`
- `cheap_first_canary_promotion_decision`
- `cheap_first_canary_approval_packet`
- `cheap_first_canary_rollback_drill`
- `cheap_first_canary_change_manifest`

It does not consume prompts, legal documents, raw model output, gateway headers, API keys, user email addresses, or credential values.

## Output

The API endpoint is:

`GET /api/v1/aihub/models/cheap-first-maintainer-execution-checklist`

The checklist is also embedded in:

`GET /api/v1/aihub/models`

Each execution item includes:

- task id
- execution rank and status
- priority score and label
- release, canary, approval, rollback, and manifest source statuses
- env var name
- current and recommended model ids
- missing evidence ids
- operator action
- validation commands

## Statuses

- `ready_for_external_change`: release decision, canary evidence, approval packet, rollback drill, and manual change manifest are ready.
- `review_required`: one or more evidence packets need maintainer review before any external change request.
- `blocked`: release, rollback, or manifest evidence blocks the change.
- `rollback_review_required`: canary evidence requires rollback review before any default promotion.
- `monitor_only`: no default change is queued; continue observing current cheap-first defaults.

## Safety Boundary

The checklist never:

- writes env files
- changes default model configuration
- records approvals
- calls NewAPI, Gemini, OpenAI, Google, or any gateway
- shifts production traffic
- returns prompts, raw payloads, legal text, model output, API keys, headers, or credential values
- claims automatic default promotion
- claims public benchmark scores
- claims 24h completion or 100-update completion

## Validation

Recommended local checks:

```bash
cd app/backend
python -m pytest tests/test_model_ops_cheap_first_maintainer_execution_checklist.py tests/test_model_ops_readiness.py -q
python -m pytest tests/test_model_ops_cheap_first_canary_change_manifest.py tests/test_model_ops_cheap_first_canary_rollback_drill.py tests/test_model_ops_cheap_first_priority_queue.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```
