# Model Fallback Chains

The project now has deterministic fallback chains for Gemini/OpenAI-compatible routing.

## Purpose

NewAPI and other OpenAI-compatible gateways can expose different Gemini model availability over time. A routing policy should therefore show not only the default model, but also the next acceptable model when a step is unavailable, too weak, or blocked by a deterministic quality check.

Fallback chains answer:

- Which model is the task primary?
- Which model can verify or retry after a quality signal?
- Which premium steps require operator review?
- Which tasks are explicit premium or media exceptions?
- Whether the primary model still fits the task cost budget.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `fallback_chains` next to:

- `budget_policy`
- `capability_matrix`
- `escalation_policy`
- `routing_replay`
- `cost_forecast`
- `cost_guardrails`
- `models`
- `usage`

The frontend `/model-ops` page shows chain status, cheap primaries, premium exception tasks, operator-review steps, hard stops, and per-task fallback models.

## Chain Sources

Core runtime tasks use `model_escalation_policy.py` because those steps match the actual cheap-first cascade:

- `fast`
- `ocr`
- `review`
- `pdf`
- `classification`

Explicit Gemini capability tasks use `model_capability_matrix.py` because they are selected by capability rather than a runtime alias:

- `grounded-research`
- `agentic`
- `image`

## Checks

Each chain checks:

- `primary-model`: the task has a starting model.
- `primary-budget`: non-exception primaries stay within the task cost tier.
- `premium-operator-review`: premium fallbacks outside PDF/image require operator review.
- `runtime-default`: configured runtime defaults align with the chain primary for aliased tasks.

## Safety

Fallback chains store only routing metadata. They do not store prompts, documents, file names, API keys, emails, user identifiers, or raw model output.

## Related files

- `app/backend/services/model_fallback_chains.py`
- `app/backend/tests/test_model_fallback_chains.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
