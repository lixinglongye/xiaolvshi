# ModelOps Request Execution Observation Gate

This gate reviews sanitized post-run request metadata against the request
execution preflight. It is for cheap-first ModelOps evidence after a maintainer
or external runner has already executed a reviewed request. The gate itself does
not execute any request.

## Purpose

- Confirms every observation maps to a request execution preflight row.
- Checks whether high-frequency observations stayed on cheap-first Gemini
  models such as Flash-Lite or the default Gemini embedding model.
- Compares observed cost metadata with the preflight request limit.
- Records fallback use, latency review states, and coarse error categories.
- Shows whether local downgrade behavior from preflight was followed.
- Rejects raw run fields such as headers, messages, prompts, request bodies,
  legal text, model output, gateway responses, emails, and credentials.

## Endpoints

```http
GET /api/v1/aihub/models/request-execution-observation-gate
POST /api/v1/aihub/models/request-execution-observation-gate
```

`GET /api/v1/aihub/models` also includes the result as
`request_execution_observation_gate`.

## POST Payload

The POST endpoint accepts metadata only. Example:

```json
{
  "preflight": {
    "requests": [
      {
        "id": "fast-intake",
        "task": "fast",
        "model": "gemini-2.5-flash-lite",
        "estimated_input_tokens": 1200,
        "estimated_output_tokens": 350,
        "max_cost_usd": 0.01
      }
    ]
  },
  "observations": [
    {
      "request_id": "fast-intake",
      "task": "fast",
      "resolved_model": "gemini-2.5-flash-lite",
      "status": "success",
      "observed_input_tokens": 1180,
      "observed_output_tokens": 220,
      "observed_cost_usd": 0.0002,
      "latency_ms": 900,
      "fallback_used": false,
      "error_category": "none"
    }
  ]
}
```

Do not send prompts, legal documents, headers, request bodies, response bodies,
gateway responses, model outputs, user identifiers, or credentials.

## Release Readiness

Release readiness tracks this gate as optional
`modelops-request-execution-observation-gate` evidence. Not running it does not
block a release candidate, but a submitted failed observation gate blocks
release review until the observation is fixed or waived.

## Boundaries

The observation gate does not call NewAPI, Gemini, OpenAI, Google, gateways,
app AI endpoints, models, or the network. It does not write configuration,
change defaults, shift traffic, replay requests, or validate live account
inventory.

It returns request IDs, task labels, sanitized model IDs, status categories,
token counts, costs, latency, fallback flags, reason codes, release actions,
and privacy/claim boundaries only. It does not return raw prompts, messages,
request bodies, response bodies, headers, raw payloads, legal text, model
outputs, gateway responses, emails, user identifiers, API keys, Authorization
headers, or credentials.

## Validation

```bash
cd app/backend
python -m pytest tests/test_model_ops_request_execution_observation_gate.py tests/test_model_ops_request_execution_preflight.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q

cd ../frontend
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_request_execution_observation_gate.py`
- `app/backend/tests/test_model_ops_request_execution_observation_gate.py`
- `app/backend/services/model_ops_request_execution_preflight.py`
- `app/backend/routers/aihub.py`
- `app/backend/services/model_ops_readiness.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
