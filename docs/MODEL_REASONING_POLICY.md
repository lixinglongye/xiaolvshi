# Model Reasoning Policy

The project now controls Gemini/OpenAI-compatible `reasoning_effort` for text generation.

## Purpose

Cheap-first routing should not only pick cheaper models; it should also avoid unnecessary thinking budget on high-volume tasks. The reasoning policy sets task-aware defaults for `POST /api/v1/aihub/gentxt`:

- `fast`, `ocr`, and `classification`: disable or minimize thinking when the Gemini model supports it.
- `review`: use low reasoning effort for balanced legal review quality and cost.
- `pdf` and complex review paths: use high reasoning effort because these are already premium-exception tasks.
- unknown gateway-specific models: omit `reasoning_effort` to preserve pass-through compatibility.

Unsupported requested efforts are coerced to the cheapest supported safe effort. For example, `reasoning_effort=none` is not sent to Gemini Pro models that cannot disable thinking; the policy coerces it to `low`.

## API

`GenTxtRequest` accepts:

```json
{
  "reasoning_effort": "auto"
}
```

Allowed values are:

- `auto`
- `none`
- `minimal`
- `low`
- `medium`
- `high`

When omitted or set to `auto`, the backend chooses a task-aware default after task inference and runtime model routing. Non-streaming `GenTxtResponse` includes `reasoning_policy` with the effective decision.

## Model Ops

```http
GET /api/v1/aihub/models
```

The response includes `reasoning_policy`, and the frontend `/model-ops` page shows each task default, effective effort, supported effort set, adjustment status, and rationale.

## Release Readiness

`model-reasoning-policy` is a required release-readiness check. Maintainers should run:

```bash
python -m pytest tests/test_model_reasoning_policy.py tests/test_aihub_runtime_routing.py -q
```

## Safety

The policy never stores prompts, uploaded documents, API keys, passwords, emails, user identifiers, or raw model output. It only records routing metadata and the selected effort level.

## Related files

- `app/backend/services/model_reasoning_policy.py`
- `app/backend/services/aihub.py`
- `app/backend/schemas/aihub.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_reasoning_policy.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`

## Sources

- Google Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Google Gemini thinking controls: https://ai.google.dev/gemini-api/docs/thinking
