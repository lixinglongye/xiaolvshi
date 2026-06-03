# Legal Fixture Local Run Package

The local run package bundles the smallest manual NewAPI/Gemini fixture smoke run into one response for low-resource machines.

## Endpoint

```http
GET /api/v1/maintenance/legal-review-benchmark/local-run-package
GET /api/v1/maintenance/legal-review-benchmark/local-run-package?fixture_limit=1
```

`fixture_limit` is clamped to `1-4`. The default is `2` so maintainers can run a cheap-first smoke check on a laptop before spending on a larger fixture plan.

## What It Contains

- `request_files`: JSON request bodies for selected synthetic fixtures.
- `run_steps`: one-at-a-time PowerShell and curl command templates.
- `observation_template`: normalized fixture-smoke payload slots.
- `run_report_payload_template`: combined observations plus run metadata for `/fixture-run-report`.
- `local-response-normalizer`: the follow-up endpoint that can extract `choices[0].message.content` from gateway responses.
- `follow_up_endpoints`: fixture-smoke, fixture-run-report, and fixture-evidence-bundle.
- `checks`: deterministic package readiness checks.

## Workflow

1. Fetch `/local-run-package?fixture_limit=1` or `2`.
2. Save each `request_files[].body` locally using its `file_name`.
3. Keep `APP_AI_BASE_URL` as an OpenAI-compatible `/v1` base URL and keep `APP_AI_KEY` in the local shell environment.
4. Run each `run_steps[].command_templates.powershell` or `curl` command one at a time.
5. Paste the gateway response into `/local-response-normalizer`.
6. Submit `run_report_payload.observations` to `/fixture-smoke`.
7. Submit `run_report_payload` to `/fixture-run-report` and `/fixture-evidence-bundle`.
8. Escalate only selected fixtures that fail smoke coverage or keep high-priority improvement actions.

## Safety

- The package never calls a model or gateway.
- Request files contain synthetic fixture prompts only and no Authorization headers.
- Command templates read keys from environment variables and include no real secret values.
- Do not commit raw gateway outputs, client documents, public benchmark raw examples, emails, or API keys.

## Validation

```bash
python -m pytest tests/test_legal_fixture_local_run_package.py tests/test_legal_fixture_quick_suite.py -q
python -m pytest tests/test_legal_fixture_response_normalizer.py tests/test_legal_fixture_local_run_package.py -q
python -m pytest tests/test_legal_fixture_gateway_manifest.py tests/test_legal_fixture_run_plan.py -q
```

## Related Files

- `app/backend/services/legal_fixture_local_run_package.py`
- `app/backend/services/legal_fixture_response_normalizer.py`
- `app/backend/tests/test_legal_fixture_local_run_package.py`
- `app/backend/tests/test_legal_fixture_response_normalizer.py`
- `app/backend/services/legal_fixture_quick_suite.py`
- `app/backend/services/legal_fixture_gateway_manifest.py`
- `app/backend/services/legal_fixture_run_plan.py`
- `app/backend/routers/maintenance.py`
- `docs/LEGAL_FIXTURE_QUICK_SUITE.md`
- `docs/LEGAL_FIXTURE_RESPONSE_NORMALIZER.md`
- `docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md`
- `docs/LEGAL_FIXTURE_RUN_PLAN.md`
