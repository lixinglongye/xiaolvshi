# ModelOps Request Execution Preflight

This gate reviews sanitized request execution metadata before a NewAPI/Gemini
runtime call is made. It is intended for cheap-first ModelOps review, not for
live gateway validation.

## Purpose

- Confirms high-frequency requests stay on cheap-first task defaults.
- Shows when the runtime router locally downgrades an explicit model request to
  the recommended task model.
- Checks fallback chains so low-cost Gemini candidates appear before premium or
  review-only models.
- Estimates request cost from sanitized input/output token counts and local
  catalog pricing.
- Compares estimated cost against task cost bounds and caller-supplied
  `max_cost_usd`.
- Exposes review-required premium exceptions separately from ready cheap-first
  requests.
- Blocks raw payload fields such as headers, messages, prompts, request bodies,
  legal text, model output, emails, and credentials.

## Endpoints

```http
GET /api/v1/aihub/models/request-execution-preflight
POST /api/v1/aihub/models/request-execution-preflight
```

`GET /api/v1/aihub/models` also includes the result as
`request_execution_preflight`.

## POST Payload

The POST endpoint accepts only metadata. Example:

```json
{
  "requests": [
    {
      "id": "fast-intake",
      "task": "fast",
      "model": "gemini-2.5-flash-lite",
      "estimated_input_tokens": 1200,
      "estimated_output_tokens": 350,
      "max_tokens": 512,
      "max_cost_usd": 0.01,
      "fallback_chain": ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
    }
  ]
}
```

Do not send prompts, legal documents, headers, request bodies, model responses,
or credentials to this endpoint.

## Boundaries

The preflight does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, models, or the network. It does not write configuration, change
runtime defaults, shift traffic, or validate live account inventory.

It returns request IDs, task IDs, sanitized model IDs, route decisions,
estimated token counts, local cost estimates, fallback order summaries,
reason codes, release actions, and privacy/claim boundaries only. It does not
return raw prompts, request bodies, response bodies, messages, headers, raw
payloads, legal text, model outputs, gateway responses, emails, user
identifiers, API keys, Authorization headers, or credentials.

## Validation

Release readiness tracks this gate as the required
`modelops-request-execution-preflight` check. It must be passed or explicitly
waived before a release candidate can claim request-level Gemini/NewAPI
execution readiness.

```bash
cd app/backend
python -m pytest tests/test_model_ops_request_execution_preflight.py tests/test_model_ops_readiness.py tests/test_model_gateway_request_compatibility_gate.py tests/test_model_request_cost_bounds.py tests/test_frontend_ui_regression_gate.py tests/test_continuous_update_ledger.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_request_execution_preflight.py`
- `app/backend/tests/test_model_ops_request_execution_preflight.py`
- `app/backend/routers/aihub.py`
- `app/backend/services/model_ops_readiness.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
