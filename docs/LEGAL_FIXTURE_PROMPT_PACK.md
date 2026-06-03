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

1. Fetch `/prompt-pack`.
2. Run each prompt through the configured OpenAI-compatible gateway, starting with the cheap trial model where appropriate.
3. Submit model output to `/fixture-smoke`.
4. Submit the same observations to `/fixture-improvements` when coverage is weak.

## Safety

- Prompt rows include only synthetic local fixture text.
- Do not commit real client documents or model outputs into tests or docs.
- Uploaded document text must still pass privacy and instruction-injection preflight before any real review.

## Related Files

- `app/backend/services/legal_fixture_prompt_pack.py`
- `app/backend/services/legal_review_benchmark.py`
- `app/backend/tests/test_legal_fixture_prompt_pack.py`
- `docs/LEGAL_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_FIXTURE_IMPROVEMENT.md`
