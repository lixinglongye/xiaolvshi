# Legal Fixture Prompt Pack

The legal fixture prompt pack converts the small synthetic legal document fixtures into cheap-first model prompt payloads.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/prompt-pack
```

The endpoint returns prompt rows only. It does not call a model, read API keys, or store observations.

## What Each Row Contains

- fixture ID and title,
- expected route and recommended task,
- recommended configured Gemini/NewAPI model,
- cheap trial model,
- request parameters,
- output JSON schema,
- estimated prompt tokens and request cost,
- follow-up endpoints for fixture smoke scoring and fixture improvement planning.

## Workflow

1. Fetch `/fixture-model-matrix` to confirm cheap-first and escalation candidates.
2. Fetch `/prompt-pack`.
3. Run each prompt through the configured OpenAI-compatible gateway, starting with the cheap trial model where appropriate.
4. Submit model output to `/fixture-smoke`.
5. Submit the same observations to `/fixture-improvements` when coverage is weak.

If a caller needs ready-to-fill request bodies instead of raw prompt rows, fetch `/gateway-manifest` for OpenAI-compatible chat payloads and local `/api/v1/aihub/gentxt` payloads with key placeholders.

If a caller needs a low-resource run order, fetch `/fixture-run-plan` to group those request bodies into serial cheap-first batches and conditional escalation steps.
After smoke observations exist, fetch `/fixture-run-report` to decide whether cheap-first model defaults can be preserved.

## Safety

- Prompt rows include only synthetic local fixture text.
- Do not commit real client documents or model outputs into tests or docs.
- Uploaded document text must still pass privacy and instruction-injection preflight before any real review.

## Related Files

- `app/backend/services/legal_fixture_prompt_pack.py`
- `app/backend/services/legal_fixture_model_matrix.py`
- `app/backend/services/legal_fixture_gateway_manifest.py`
- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/tests/test_legal_fixture_prompt_pack.py`
- `app/backend/tests/test_legal_fixture_model_matrix.py`
- `app/backend/tests/test_legal_fixture_gateway_manifest.py`
- `app/backend/tests/test_legal_fixture_run_plan.py`
- `app/backend/tests/test_legal_fixture_run_report.py`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_FIXTURE_MODEL_MATRIX.md`
- `docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md`
- `docs/LEGAL_FIXTURE_RUN_PLAN.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
- `docs/LEGAL_FIXTURE_IMPROVEMENT.md`
