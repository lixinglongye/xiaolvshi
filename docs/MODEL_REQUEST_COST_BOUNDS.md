# Model Request Cost Bounds

`model_request_cost_bounds.py` estimates per-request cost boundaries for core Gemini/NewAPI text tasks before a model routing release.

## Purpose

The request policy already sets `temperature` and `max_tokens` by task. This check translates those token ceilings into estimated USD cost so maintainers can see whether fast, OCR, classification, review, and PDF routes still fit the cheap-first strategy.

## What It Checks

- Runtime default model for each tracked task.
- Prompt-token planning assumption, aligned with the monthly cost forecast profile.
- Default `max_tokens` cost estimate.
- Maximum allowed `max_tokens` ceiling cost estimate.
- Warning and fail thresholds for default and ceiling request cost.
- Unknown pricing when a gateway model is not in `model_catalog.py`.

High-volume tasks such as `fast`, `classification`, and `ocr` fail if they drift above the lowest Gemini cost tier.

## Official Price And Status Gate

When official provider or gateway pricing, lifecycle status, or model
availability has not been confirmed, request cost bounds must keep the model
`unpriced` and `review-only`. Do not hard-code per-request costs, count the
model in cheap-first savings, or treat it as a valid default candidate until
source-backed price, status, capability, and gateway evidence are refreshed.

## API Surface

`GET /api/v1/aihub/models` returns `request_cost_bounds`:

- `status`: `pass`, `warn`, or `fail`.
- `summary`: total default and ceiling request cost estimates.
- `task_bounds`: per-task model, token assumptions, estimated costs, thresholds, status, and reason.
- `blocking_check_ids` and `warning_check_ids`.

The frontend `/model-ops` page shows the same data near the request policy table.

## Release Check

```bash
cd app/backend
python -m pytest tests/test_model_request_cost_bounds.py tests/test_model_request_policy.py -q
```

A `fail` means a task default, token ceiling, or cost tier has drifted past the policy threshold. A `warn` means pricing is unknown or the cost is close enough to require maintainer review.

## Safety

This service never reads prompts, documents, users, emails, filenames, API keys, or raw model output. It only uses public catalog pricing, model ids, and static token planning assumptions.
