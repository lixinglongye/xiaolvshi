# Legal Fixture Response Normalizer

The response normalizer converts manual OpenAI-compatible gateway responses from local fixture runs into payloads for fixture-smoke and fixture-run-report.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/local-response-normalizer
POST /api/v1/maintenance/legal-review-benchmark/local-response-normalizer
```

## Payload

```json
{
  "responses": {
    "fixture-service-agreement-small": {
      "phase": "cheap_first",
      "model": "gemini-2.5-flash-lite",
      "http_status": 200,
      "latency_ms": 1200,
      "estimated_cost_usd": 0.0003,
      "gateway_response": {
        "model": "gemini-2.5-flash-lite",
        "choices": [
          {
            "message": {
              "content": "{\"fixture_id\":\"fixture-service-agreement-small\",\"route\":\"fast\",\"release_decision\":\"warn\",\"route_reason\":\"local smoke run\"}"
            }
          }
        ]
      }
    }
  }
}
```

The service also accepts a list of rows or a single row with `fixture_id` and either `gateway_response`, `response`, `content`, `output_text`, or `text`.

## What It Returns

- `observations`: fixture-smoke compatible observations keyed by fixture ID.
- `run_report_payload`: combined `observations` and `run_metadata` for `/fixture-run-report`.
- `response_summaries`: HTTP status, model, route, content length, JSON parse status, and redaction status.
- `checks`: known fixture, content present, HTTP status, route present, and secret redaction checks.

## Workflow

1. Fetch `/local-run-package` and run one request at a time.
2. Paste the local gateway JSON response into `/local-response-normalizer`.
3. Post `run_report_payload.observations` to `/fixture-smoke`.
4. Post `run_report_payload` to `/fixture-run-report`.
5. Post the same payload to `/fixture-evidence-bundle`.

## Safety

- The normalizer never calls a gateway or app AI endpoint.
- It omits gateway headers, request prompts, and full response envelopes from its output.
- Secret-like values in extracted content are replaced with `[redacted-secret]`.
- Do not commit normalized model output; use it only as local smoke-test input.

## Validation

```bash
python -m pytest tests/test_legal_fixture_response_normalizer.py tests/test_legal_fixture_local_run_package.py -q
```

## Related Files

- `app/backend/services/legal_fixture_response_normalizer.py`
- `app/backend/tests/test_legal_fixture_response_normalizer.py`
- `app/backend/services/legal_fixture_local_run_package.py`
- `app/backend/routers/maintenance.py`
- `docs/LEGAL_FIXTURE_LOCAL_RUN_PACKAGE.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
