# Model Runtime Router

The project now routes text, PDF, image, video, audio, and transcription requests through a deterministic runtime model router before calling the OpenAI-compatible gateway.

## Purpose

Earlier model-ops services documented the cheap-first strategy, but the AIHub endpoints still needed request-level task semantics. The runtime router now lets callers declare the intended task and lets the backend choose the task default model before the model call is made.

This helps keep high-volume legal workflows on cheaper Gemini models while still allowing explicit premium use when a maintainer or caller deliberately enables it.

## Request Fields

`POST /api/v1/aihub/gentxt` accepts:

- `task`: routing task such as `auto`, `fast`, `classification`, `ocr`, `review`, or `pdf`. The default is `auto`. Media and speech task labels are rejected for gentxt and routed to the review text budget instead of media defaults.
- `model`: optional model name or routing alias. If omitted, the task default is used.
- `allow_over_budget_model`: default `false`. When false, over-budget or operator-review models are routed to the task recommended model.

`POST /api/v1/aihub/analyzepdf` uses the configured PDF route with `task=pdf`.

`POST /api/v1/aihub/genimg` uses the requested or default image model with `task=image`.
`model=auto` and `model=auto-image` resolve to `APP_AI_IMAGE_MODEL`, which
defaults to `gemini-2.5-flash-image`.

`POST /api/v1/aihub/genvideo`, `/genaudio`, and `/transcribe` use explicit
media/speech tasks. `model=auto-video`, `model=auto-audio`, and
`model=auto-transcription` resolve to `APP_AI_VIDEO_MODEL`,
`APP_AI_AUDIO_MODEL`, and `APP_AI_TRANSCRIPTION_MODEL`.

## Runtime Behavior

- Omitted model + `task=auto` -> deterministic task inference before model routing.
- Omitted model + `task=fast` -> `gemini-2.5-flash-lite`.
- Omitted model + `task=review` -> `gemini-2.5-flash`.
- Explicit premium model + `task=fast` -> downgraded to `gemini-2.5-flash-lite` unless `allow_over_budget_model=true`.
- `model=auto` + `task=image` -> `gemini-2.5-flash-image` unless `APP_AI_IMAGE_MODEL` is configured.
- Media endpoint omitted model + `task=video`, `task=audio`, or `task=transcription` -> the explicit media/speech task default, with non-catalog gateway ids remaining review-only until pricing and lifecycle are documented.
- Gentxt + media or speech task labels -> the review text budget, with `unsupported_for_gentxt:*` task-inference signals.
- Unknown gateway-specific explicit model names are downgraded to the task recommendation unless `allow_over_budget_model=true`.
- Catalog models with `preview`, `review`, or other non-stable lifecycle states are downgraded to stable task recommendations unless `allow_over_budget_model=true`.
- Explicitly allowed unknown or non-stable models remain review exceptions and are marked with pass-through or lifecycle reason codes.
- Usage counters record the normalized task, not prompts or document content.
- PDF, image, video, audio, and transcription routes write the same aggregate routing evidence as text routes. Video, audio, and transcription responses also expose sanitized route payload metadata.
- Image defaults are also checked by the price refresh monitor for per-image cost metadata.

## Structured Reason Codes

Each runtime route now includes bounded allowlisted `reason_codes` for maintainer review.
Examples include `task_default_selected`, `over_task_budget`,
`operator_review_required`, `routed_to_recommended_model`,
`unknown_catalog_model`, `unknown_gateway_routed_to_recommended`,
`lifecycle_preview`, `non_stable_model_routed_to_recommended`,
`gateway_passthrough`, and `explicit_gateway_passthrough_allowed`.

These codes are policy labels only. They explain why cheap-first routing chose
the selected model and are safe for aggregate route telemetry because they do
not contain prompts, legal text, request payloads, model responses, user
identity, or credentials.

## Endpoint Visibility

```http
GET /api/v1/aihub/models
```

The response includes `runtime_router` with request fields, enforcement rules, and task default decisions.

Non-streaming text responses include `task_inference` and `budget_decision`, which record the inferred task, selected model, requested model, over-budget status, and whether the request was routed to the recommended model.

Non-streaming PDF, image, video, audio, and transcription responses expose sanitized route/task/budget metadata where the response shape allows it. Image, video, audio, and transcription responses also expose sanitized usage units for ModelOps review without raw payloads.

`route_telemetry` records aggregate runtime routing outcomes so maintainers can inspect auto-inference rates, downgrades, over-budget requests, operator-review-gated requests, and route reason-code counts over the current backend process.

`callsite_audit` is exposed on the same model-ops endpoint to verify that service-layer `GenTxtRequest` calls provide explicit `task=...` metadata instead of relying only on inference.

## Safety

The router records only model names, task names, cost tier metadata, bounded reason codes, and aggregate usage. It does not store prompts, PDF bytes, uploaded images, generated image URLs, raw model outputs, file names, API keys, passwords, emails, or user identifiers.

## Related files

- `app/backend/services/model_runtime_router.py`
- `app/backend/services/model_route_telemetry.py`
- `app/backend/services/model_task_inference.py`
- `app/backend/services/model_ops_gentxt_task_guard.py`
- `app/backend/services/model_callsite_audit.py`
- `app/backend/services/aihub.py`
- `app/backend/schemas/aihub.py`
- `app/backend/tests/test_model_runtime_router.py`
- `app/backend/tests/test_model_route_telemetry.py`
- `app/backend/tests/test_model_task_inference.py`
- `app/backend/tests/test_model_ops_gentxt_task_guard.py`
- `app/backend/tests/test_model_callsite_audit.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
- `app/frontend/src/pages/ModelOpsPage.tsx`
