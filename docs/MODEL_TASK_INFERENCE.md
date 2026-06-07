# Model Task Inference

The project now has deterministic task inference for `POST /api/v1/aihub/gentxt`.

## Purpose

Runtime model routing depends on knowing the task. If callers forget to pass `task=review`, legal review prompts can accidentally run on the cheapest fast route. Task inference fixes this by making `task=auto` the default and resolving the task before budget enforcement.

The inference step is deterministic and does not call an AI model.

## Inference Rules

Explicit task values are honored first.

When `task=auto`, the service inspects message metadata and keyword signals:

- media or speech task values on gentxt, such as `image`, `video`, `audio`,
  `transcription`, `tts`, or `speech-to-text`, are rejected for the text endpoint
  and routed to the `review` text budget
- classification keywords plus JSON response format -> `classification`
- OCR or visible-text extraction prompts, especially with image input -> `ocr`
- contract, legal review, litigation, evidence, citation, risk, or clause terms -> `review`
- planning, preflight, summary, rewrite, formatting, or JSON repair terms -> `fast`
- unmatched requests -> `fast`

## Runtime Flow

```text
gentxt request
  -> deterministic task inference
  -> runtime model router
  -> budget enforcement
  -> OpenAI-compatible gateway call
  -> aggregate usage counter
```

Non-streaming responses include:

- `task`: normalized task used by the runtime router
- `task_inference`: source, confidence, matched signals, and reason
- `budget_decision`: selected model, requested model, cost tier, and downgrade status

## Safety

Task inference stores only matched metadata signals. It does not store prompt text, uploaded documents, API keys, passwords, file names, emails, user identifiers, or raw model output.

## Related files

- `app/backend/services/model_task_inference.py`
- `app/backend/services/model_runtime_router.py`
- `app/backend/services/aihub.py`
- `app/backend/schemas/aihub.py`
- `app/backend/services/model_ops_gentxt_task_guard.py`
- `app/backend/tests/test_model_ops_gentxt_task_guard.py`
- `app/backend/tests/test_model_task_inference.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
