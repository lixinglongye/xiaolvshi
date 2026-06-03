# Legal Fixture Gateway Manifest

The legal fixture gateway manifest turns cheap-first fixture prompts into safe OpenAI-compatible request bodies.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/gateway-manifest
```

The endpoint returns request manifests only. It does not call NewAPI, Gemini, OpenAI-compatible gateways, or the app AI hub.

## What It Contains

- `openai_request_body`: request body for `{{APP_AI_BASE_URL}}/v1/chat/completions`.
- `app_request_body`: request body for the local `/api/v1/aihub/gentxt` endpoint.
- `cheap_first_policy`: first-attempt model, escalation model, and deterministic escalation trigger.
- `smoke_observation_template`: payload shape for `/fixture-smoke`.
- `expected_response_contract`: required JSON fields and follow-up endpoints.

## Safety

- The manifest uses `{{APP_AI_BASE_URL}}` and `Bearer {{APP_AI_KEY}}` placeholders only.
- It contains only synthetic fixture prompts.
- It must not be edited to include real API keys, client documents, emails, or raw production model outputs.

## Workflow

1. Fetch `/prompt-pack` or `/gateway-manifest`.
2. Run each `openai_request_body` against the configured local gateway.
3. Paste normalized output into the `smoke_observation_template`.
4. Submit observations to `/fixture-smoke`.
5. Use `/fixture-improvements` if smoke coverage fails.

For low-resource local machines, fetch `/fixture-run-plan` first and follow its serial cheap-first batches before running any escalation step.
Fetch `/local-run-package` when you need the smallest selected request files and command templates in one response.
Fetch `/local-run-review` after a local gateway response when you want normalization, smoke scoring, the run report, and the evidence bundle in one deterministic response.
After the smoke pass, submit observations to `/fixture-run-report` to decide whether cheap-first defaults can be kept.

## Related Files

- `app/backend/services/legal_fixture_gateway_manifest.py`
- `app/backend/services/legal_fixture_local_run_package.py`
- `app/backend/services/legal_fixture_local_run_review.py`
- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_prompt_pack.py`
- `app/backend/tests/test_legal_fixture_gateway_manifest.py`
- `app/backend/tests/test_legal_fixture_local_run_package.py`
- `app/backend/tests/test_legal_fixture_local_run_review.py`
- `app/backend/tests/test_legal_fixture_run_plan.py`
- `app/backend/tests/test_legal_fixture_run_report.py`
- `docs/LEGAL_FIXTURE_PROMPT_PACK.md`
- `docs/LEGAL_FIXTURE_LOCAL_RUN_PACKAGE.md`
- `docs/LEGAL_FIXTURE_LOCAL_RUN_REVIEW.md`
- `docs/LEGAL_FIXTURE_RUN_PLAN.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
- `docs/LEGAL_FIXTURE_IMPROVEMENT.md`
