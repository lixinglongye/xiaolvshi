# ModelOps Gentxt Routing Guard

`modelops-gentxt-routing-guard` is metadata-only evidence for the text
generation task boundary.

## Scope

`POST /api/v1/aihub/gentxt` accepts a caller-provided `task`, but the endpoint
must not route media or speech task aliases to media default models. The guard
runs deterministic local task inference against sanitized dummy text messages
and verifies that `image`, `video`, `audio`, `transcription`, `tts`, and
`speech-to-text` are rejected for gentxt and routed to the review text budget.

The media endpoint aliases remain visible for operator review:

- `auto-video` -> `APP_AI_VIDEO_MODEL`
- `auto-audio` -> `APP_AI_AUDIO_MODEL`
- `auto-transcription` -> `APP_AI_TRANSCRIPTION_MODEL`

Those aliases are scoped to media endpoints, not to gentxt.

## Endpoint

```http
GET /api/v1/aihub/models/gentxt-routing-guard
```

The same signal is included in:

```http
GET /api/v1/aihub/models
```

as `gentxt_routing_guard`, and it is registered in `model_ops_readiness` as a
routing component.

## Boundary

The guard does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network. It does not write configuration, shift
traffic, or include request bodies, response bodies, headers, prompts, raw
payloads, legal text, model outputs, gateway responses, credentials, emails, or
user identifiers.

## Validation

```powershell
python -m pytest tests/test_model_ops_gentxt_task_guard.py tests/test_model_task_inference.py tests/test_aihub_runtime_routing.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q
cd ..\frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_gentxt_task_guard.py`
- `app/backend/services/model_task_inference.py`
- `app/backend/services/aihub.py`
- `app/backend/routers/aihub.py`
- `app/backend/tests/test_model_ops_gentxt_task_guard.py`
- `app/backend/tests/test_aihub_runtime_routing.py`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/src/lib/modelOpsApi.ts`
