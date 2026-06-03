# Model Routing Replay

The project now has a deterministic routing replay suite for Gemini/OpenAI-compatible model routing.

## Purpose

Cheap-first routing is only useful if route changes can be reviewed before they increase model spend. The replay suite runs fixed legal workflow scenarios against the current escalation policy and checks:

- expected routing decision,
- selected model cost tier,
- premium operator-review requirements,
- hard-stop scenarios that should spend no model budget.

The replay does not call an AI model. It only evaluates routing metadata from `model_escalation_policy.py` and priced model metadata from `model_catalog.py`.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `routing_replay` next to:

- `budget_policy`
- `capability_matrix`
- `escalation_policy`
- `cost_forecast`
- `cost_guardrails`
- `models`
- `usage`

The frontend `/model-ops` page shows replay status, scenario counts, cheap starts, premium reviews, hard stops, and per-scenario actions.

## Replay Scenarios

Current scenarios cover:

- fast preflight without warnings starts on `gemini-2.5-flash-lite`,
- low-confidence fast routing verifies on the balanced model,
- classification schema failure retries on the balanced model,
- uncertain OCR verifies extraction with the balanced model,
- citation audit failure can escalate to premium only with operator review,
- weak citations keep an operator-review gate before premium verification,
- high privacy risk hard-stops before more model spend,
- clean large PDF review uses the explicit premium exception path,
- failed PDF extraction quality hard-stops before costly review.

## Release Gate

Release readiness now includes:

```text
model-routing-replay -> python -m pytest tests/test_model_routing_replay.py -q
```

This makes route drift visible before a maintainer marks a release candidate ready.

## Safety

Replay fixtures store only task names, deterministic quality signals, expected decisions, and model metadata. They do not store prompts, uploaded documents, user identifiers, API keys, passwords, or raw model output.

## Related files

- `app/backend/services/model_routing_replay.py`
- `app/backend/tests/test_model_routing_replay.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
