# Gemini Model Lifecycle Policy

The model lifecycle policy keeps Gemini/NewAPI defaults stable, cheap-first, and reviewable as gateway model names change.

## Endpoint

```http
GET /api/v1/aihub/models
```

The response includes `lifecycle_policy` next to gateway compatibility, default optimization, runtime router, fallback chains, and cost guardrails.

## Rules

- Stable Gemini catalog models can be unattended defaults when they fit the task budget.
- Preview models are explicit experiments and should not become defaults without maintainer review.
- `latest` aliases are allowed for one-off gateway experiments but should be pinned to concrete model IDs before release.
- Deprecated Gemini generations such as `gemini-1.x`, `gemini-1.5`, and `gemini-2.0` are blocked as defaults.
- Gateway-prefixed names such as `models/gemini-2.5-flash-lite`, `google/gemini-2.5-flash-lite`, and `openrouter/google/gemini-2.5-flash-lite` are canonicalized before lifecycle checks.

## Cheap-First Defaults

- `cheap`, `fast`, `ocr`, and `classification` roles should stay on stable lowest/low cost models.
- `review` roles can use stable low or medium cost models when legal analysis quality needs it.
- `pdf` and final-review roles are explicit premium exceptions and should remain bounded by operator review and release gates.

## Output

- `configured_roles`: current task/role defaults, canonical model, lifecycle state, cost tier, and allow-list decision.
- `catalog_lifecycle`: catalog status, default policy, preferred default role, and pricing source link for each Gemini model.
- `alias_policy`: gateway prefix and latest/deprecated alias rules.
- `checks`: pass/warn/fail results for deprecated defaults, preview/latest defaults, unknown lifecycle defaults, allow-list violations, and cheap-role cost drift.

## Validation

```bash
python -m pytest tests/test_model_lifecycle_policy.py tests/test_model_catalog.py tests/test_model_ops_readiness.py -q
```

## Safety

The policy only inspects model IDs, role names, task budgets, public documentation links, and catalog metadata. It never stores API keys, prompts, documents, user identifiers, emails, file names, or model outputs.

## Related Files

- `app/backend/services/model_lifecycle_policy.py`
- `app/backend/tests/test_model_lifecycle_policy.py`
- `app/backend/services/model_catalog.py`
- `app/backend/services/model_ops_readiness.py`
- `app/backend/routers/aihub.py`
- `app/frontend/src/lib/modelOpsApi.ts`
- `app/frontend/src/pages/ModelOpsPage.tsx`
- `docs/AI_MODEL_STRATEGY.md`
- `docs/MODEL_GATEWAY_COMPATIBILITY.md`
- `docs/MODEL_DEFAULT_OPTIMIZATION.md`
