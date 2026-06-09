# Model Gateway Probe Evaluation

`model_gateway_probe_evaluation.py` evaluates sanitized NewAPI/Gemini/OpenAI-compatible gateway probe results after a maintainer manually runs the dry-run contracts from the gateway health plan.

## Endpoints

```http
GET /api/v1/aihub/models/gateway-probe-template
POST /api/v1/aihub/models/gateway-probe-evaluation
POST /api/v1/aihub/models/gateway-live-probe
```

## Payload

```json
{
  "models_response": {
    "data": [
      {"id": "gemini-2.5-flash-lite"},
      {"id": "models/gemini-2.5-flash"}
    ]
  },
  "chat_probe_results": {
    "gemini-2.5-flash-lite": {
      "status": "pass",
      "http_status": 200,
      "json_ok": true,
      "latency_ms": 1200
    }
  },
  "image_probe_results": {
    "gemini-2.5-flash-image": {
      "status": "pass",
      "http_status": 200,
      "image_count": 1,
      "latency_ms": 2400
    }
  }
}
```

The evaluator also accepts `model_ids` as a plain array and chat or image probe rows as arrays. It only needs model IDs, HTTP status, JSON success, image counts, and latency.
It fails closed when submitted payloads include raw or secret-bearing fields such as `Authorization`, `api_key`, `prompt`, `messages`, `image_url`, `b64_json`, `raw_response`, or model output text. It also scans string values for key-like tokens, bearer tokens, email addresses, URLs, and data-URI/base64 image payloads. The response reports only sanitized paths and risk labels, not the matched values.

`POST /api/v1/aihub/models/gateway-probe-evaluation` also records the latest sanitized evaluation result in process memory. `GET /api/v1/aihub/models` then reuses that snapshot for `gateway_probe_evaluation`, `gateway_probe_runbook_gate`, and `model_ops_readiness`, so a browser refresh keeps the most recent manual evidence instead of reverting to `not_run`. The registry stores only the evaluated result, never the submitted payload. If a payload is rejected for forbidden raw or secret-bearing fields, the stored snapshot keeps the fail status, sanitized check IDs, summary counts, and actions, but drops model rows and `.env` recommendations.

## Maintainer Live Probe

`POST /api/v1/aihub/models/gateway-live-probe` provides a safer bridge between the dry-run runbook and a real NewAPI/Gemini-compatible gateway.

Default dry-run request:

```json
{
  "models": ["gemini-2.5-flash-lite"],
  "max_models": 1
}
```

Dry-run mode never calls the gateway. It returns the planned `list_models` and tiny chat JSON contracts, the configured base URL shape, and whether `APP_AI_KEY` is present.

Live request:

```json
{
  "execute": true,
  "models": ["gemini-2.5-flash-lite"],
  "max_models": 1
}
```

Live mode requires `APP_AI_BASE_URL` and `APP_AI_KEY` in local or deployment secrets. It calls `models.list()` and then probes at most three selected chat models with a static non-client JSON prompt. The endpoint returns only sanitized metadata:

- selected model IDs,
- pass/warn/fail status,
- HTTP status,
- JSON parse boolean,
- latency in milliseconds,
- a nested `gateway_probe_evaluation` result.

It never returns API keys, Authorization headers, raw gateway responses, raw prompts, user documents, emails, image URLs, base64 data, or model output text. When live execution produces an evaluation result, the router records that sanitized evaluation in the existing in-process readiness registry.

## What It Reports

- observed gateway models and canonical local Gemini model IDs,
- unknown Gemini-like pass-through names needing catalog review,
- cheap-first candidate count,
- cheap chat probe pass/fail status,
- image probe pass/fail status and per-image default recommendations,
- `.env` recommendations for cheap, fast, OCR, classification, review, PDF, and image roles,
- blockers when no known stable low-cost Gemini text model is available,
- blockers for forbidden raw/secret payload fields,
- blockers for forbidden raw/secret payload values without echoing the value,
- warnings for failed probes, missing chat or image probes, and unknown Gemini model names.

## Workflow

1. Fetch `/api/v1/aihub/models` and review `gateway_health_plan`.
2. Run `GET {{APP_AI_BASE_URL}}/models` manually.
3. Run a tiny chat probe for the cheapest candidate.
4. After text probes pass, optionally run `image-generation-smoke` for the configured image model with `n=1`.
5. Remove Authorization headers, bearer tokens, API keys, prompts, documents, image URLs, base64 payloads, emails, and raw model output.
6. Submit only sanitized model IDs, probe status, HTTP status, image count, JSON boolean, and latency in `/model-ops` or to `/gateway-probe-evaluation`.
7. Refresh `/model-ops` or `GET /api/v1/aihub/models` to confirm readiness is using the latest sanitized manual evidence.
8. Review `gateway_probe_runbook_gate` to confirm list-models, cheap JSON probe, optional image smoke, legal fixture smoke, and default-change review are in order.
9. Review `.env` recommendations before changing defaults.

For maintainer environments, steps 2-4 can be replaced by `POST /gateway-live-probe` with `execute=true`. Keep `max_models` small and cheap-first, then run the legal fixture quick suite before promoting any defaults.

## Validation

```bash
python -m pytest tests/test_model_gateway_probe_evaluation.py tests/test_model_gateway_health_plan.py tests/test_model_catalog.py -q
```

## Safety

Do not submit or commit API keys, bearer tokens, Authorization headers, user prompts, client documents, emails, image URLs, base64 data, or raw model outputs. The evaluator is deterministic and does not call the gateway. Secret-like model IDs are redacted in returned model rows before any snapshot is stored.

## Related Files

- `app/backend/services/model_gateway_probe_evaluation.py`
- `app/backend/services/model_gateway_live_probe.py`
- `app/backend/tests/test_model_gateway_probe_evaluation.py`
- `app/backend/services/model_gateway_health_plan.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/MODEL_GATEWAY_HEALTH_PLAN.md`
- `docs/MODEL_GATEWAY_PROBE_RUNBOOK_GATE.md`
- `docs/AI_MODEL_STRATEGY.md`
