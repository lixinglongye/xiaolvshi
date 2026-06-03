# Model Gateway Probe Evaluation

`model_gateway_probe_evaluation.py` evaluates sanitized NewAPI/Gemini/OpenAI-compatible gateway probe results after a maintainer manually runs the dry-run contracts from the gateway health plan.

## Endpoints

```http
GET /api/v1/aihub/models/gateway-probe-template
POST /api/v1/aihub/models/gateway-probe-evaluation
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
  }
}
```

The evaluator also accepts `model_ids` as a plain array and chat probe rows as an array. It only needs model IDs, HTTP status, JSON success, and latency.

## What It Reports

- observed gateway models and canonical local Gemini model IDs,
- unknown Gemini-like pass-through names needing catalog review,
- cheap-first candidate count,
- cheap chat probe pass/fail status,
- `.env` recommendations for cheap, fast, OCR, classification, review, and PDF roles,
- blockers when no known stable low-cost Gemini text model is available,
- warnings for failed probes, missing chat probes, and unknown Gemini model names.

## Workflow

1. Fetch `/api/v1/aihub/models` and review `gateway_health_plan`.
2. Run `GET {{APP_AI_BASE_URL}}/models` manually.
3. Run a tiny chat probe for the cheapest candidate.
4. Remove Authorization headers, prompts, documents, and raw model output.
5. Submit only sanitized model IDs and probe status in `/model-ops` or to `/gateway-probe-evaluation`.
6. Review `.env` recommendations before changing defaults.

## Validation

```bash
python -m pytest tests/test_model_gateway_probe_evaluation.py tests/test_model_gateway_health_plan.py tests/test_model_catalog.py -q
```

## Safety

Do not submit or commit API keys, Authorization headers, user prompts, client documents, emails, or raw model outputs. The evaluator is deterministic and does not call the gateway.

## Related Files

- `app/backend/services/model_gateway_probe_evaluation.py`
- `app/backend/tests/test_model_gateway_probe_evaluation.py`
- `app/backend/services/model_gateway_health_plan.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/MODEL_GATEWAY_HEALTH_PLAN.md`
- `docs/AI_MODEL_STRATEGY.md`
