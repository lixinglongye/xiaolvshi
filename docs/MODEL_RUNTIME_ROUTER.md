# Model Runtime Router

The project now routes text generation requests through a deterministic runtime model router before calling the OpenAI-compatible gateway.

## Purpose

Earlier model-ops services documented the cheap-first strategy, but the text endpoint still needed request-level task semantics. The runtime router now lets callers declare the intended task and lets the backend choose the task default model before the model call is made.

This helps keep high-volume legal workflows on cheaper Gemini models while still allowing explicit premium use when a maintainer or caller deliberately enables it.

## Request Fields

`POST /api/v1/aihub/gentxt` accepts:

- `task`: routing task such as `auto`, `fast`, `classification`, `ocr`, `review`, or `pdf`. The default is `auto`.
- `model`: optional model name or routing alias. If omitted, the task default is used.
- `allow_over_budget_model`: default `false`. When false, over-budget or operator-review models are routed to the task recommended model.

## Runtime Behavior

- Omitted model + `task=auto` -> deterministic task inference before model routing.
- Omitted model + `task=fast` -> `gemini-2.5-flash-lite`.
- Omitted model + `task=review` -> `gemini-2.5-flash`.
- Explicit premium model + `task=fast` -> downgraded to `gemini-2.5-flash-lite` unless `allow_over_budget_model=true`.
- Gateway-specific model names still pass through, but the route metadata marks pricing as unverified.
- Usage counters record the normalized task, not prompts or document content.

## Endpoint Visibility

```http
GET /api/v1/aihub/models
```

The response includes `runtime_router` with request fields, enforcement rules, and task default decisions.

Non-streaming text responses include `task_inference` and `budget_decision`, which record the inferred task, selected model, requested model, over-budget status, and whether the request was routed to the recommended model.

## Safety

The router records only model names, task names, cost tier metadata, and aggregate usage. It does not store prompts, documents, file names, API keys, passwords, emails, or user identifiers.

## Related files

- `app/backend/services/model_runtime_router.py`
- `app/backend/services/model_task_inference.py`
- `app/backend/services/aihub.py`
- `app/backend/schemas/aihub.py`
- `app/backend/tests/test_model_runtime_router.py`
- `app/backend/tests/test_model_task_inference.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
- `app/frontend/src/pages/ModelOpsPage.tsx`
