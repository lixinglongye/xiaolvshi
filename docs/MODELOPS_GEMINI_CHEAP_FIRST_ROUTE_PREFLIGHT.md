# ModelOps Gemini Cheap-First Route Preflight

`modelops-gemini-cheap-first-route-preflight` is metadata-only release-review
evidence for Gemini/NewAPI route defaults. It joins current official-source
refresh notes, local catalog rows, task defaults, alias capability coverage,
the Gemini variant matrix, and the cheap-first coverage gate before maintainers
change any `APP_AI_*` default.

## What It Checks

- High-frequency tasks (`fast`, `routing`, `classification`, `ocr`, `agentic`,
  and `grounded-research`) remain on stable Flash-Lite cheap-first defaults.
- Review and document-generation stay on a cheap precheck before a balanced
  model is used.
- PDF and image routes stay operator-reviewed premium exceptions.
- Preview, Pro, image, unknown, unpriced, retired, or explicit-only variants
  are visible for review but are not default-promotion candidates.
- OpenAI-compatible gateway aliases are normalized through the alias capability
  coverage signal before a gateway-prefixed model id is trusted.

## Official Sources To Refresh

- Gemini model list: https://ai.google.dev/gemini-api/docs/models
- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- Vertex AI model versions: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions

The preflight records source ids and URLs only. It does not claim the official
refresh has already been completed.

## Endpoints

```http
GET /api/v1/aihub/models/gemini-cheap-first-route-preflight
POST /api/v1/aihub/models/gemini-cheap-first-route-preflight
GET /api/v1/aihub/models
```

`/api/v1/aihub/models` includes the preflight under
`gemini_cheap_first_route_preflight`, and ModelOps readiness consumes it as the
`gemini-cheap-first-route-preflight` component.

## ModelOps Review Form

The ModelOps page exposes the POST route as a review form for sanitized
`observed_models` metadata. Maintainers can paste model ids from a gateway
inventory review and immediately re-run the route preflight without calling a
gateway or replacing the aggregate `/api/v1/aihub/models` payload.

The form blocks copied credentials, contact details, request/response bodies,
prompts, raw document text, raw model output, gateway responses, and other
non-metadata fields before submission. A successful review only refreshes the
route rows, variant rows, source rows, checks, and privacy/claim boundary shown
inside the Gemini cheap-first route preflight panel.

## Safety Boundary

This evidence does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI
endpoints, or the network. It does not write configuration, shift traffic, or
include request bodies, response bodies, headers, prompts, raw payloads, legal
text, model outputs, gateway responses, credentials, emails, or user
identifiers.

Allowed output is limited to source ids and URLs, model ids, task labels, cost
tiers, route modes, checks, reason codes, and validation commands.

## Validation

Run the backend evidence tests:

```bash
python -m pytest tests/test_model_ops_gemini_cheap_first_route_preflight.py tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py tests/test_frontend_ui_regression_gate.py -q
```

Run the frontend contract checks:

```bash
npm run typecheck
npm run ui:regression
```

## Related Files

- `app/backend/services/model_ops_gemini_cheap_first_route_preflight.py`
- `app/backend/tests/test_model_ops_gemini_cheap_first_route_preflight.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/services/model_ops_cheap_first_release_decision.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `app/frontend/scripts/ui-regression.mjs`
