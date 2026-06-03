# Legal Fixture Local Run Review

The local run review endpoint is the lowest-friction path for small laptop benchmark runs. It accepts local OpenAI-compatible gateway responses, normalizes them, scores fixture smoke coverage, builds the cheap-first run report, and returns the release evidence bundle in one deterministic response.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/local-run-review
POST /api/v1/maintenance/legal-review-benchmark/local-run-review
```

`GET` returns the same response payload shape used by `/local-response-normalizer`.

`POST` accepts a response map, a response list, or a single response row:

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
              "content": "{\"fixture_id\":\"fixture-service-agreement-small\",\"route\":\"fast\",\"output_text\":\"risk_matrix liability_cap missing_sla replacement_clause\"}"
            }
          }
        ]
      }
    }
  }
}
```

## What It Returns

- `normalizer_summary` and `response_summaries` from local response normalization.
- `smoke_result` for the supplied fixture observations.
- `run_report` with cheap-first release and escalation decisions.
- `evidence_bundle` with archiveable component status and release-safe claims.
- `run_report_payload` for maintainers who still want to post to `/fixture-smoke`, `/fixture-run-report`, or `/fixture-evidence-bundle` separately.
- combined `checks`, `blocking_check_ids`, `warning_check_ids`, and `recommended_actions`.

## Status Meaning

- `ready`: all bundled fixtures passed and the evidence bundle is ready.
- `needs_escalation`: at least one observed or missing fixture blocks cheap-first release evidence.
- `review_recommended`: no hard blocker was found, but warnings need maintainer review.
- `not_run`: no scorable fixture output was supplied.
- `fail`: response content could not be normalized or no observations were produced.

Running only one or two small fixtures is valid on low-resource machines, but the result should usually be treated as review evidence rather than release-ready evidence because unrun fixtures remain `not_run`.

## Workflow

1. Fetch `/local-run-package?fixture_limit=1` or `2`.
2. Run the generated request files one at a time with local `APP_AI_BASE_URL` and `APP_AI_KEY`.
3. Paste the local gateway JSON responses into `/local-run-review`.
4. Review `status`, `release_decision`, `run_report.fixture_reports`, and `recommended_actions`.
5. Archive the returned `run_report` and `evidence_bundle` only after checking that no real client data or raw gateway envelopes were included.

## Safety

- The service never calls a model or gateway.
- It does not return Authorization headers, prompts, or full gateway envelopes.
- Secret-like values in extracted content are redacted by the shared response normalizer.
- Do not commit normalized model output, public benchmark raw examples, client documents, emails, or API keys.

## Validation

```bash
python -m pytest tests/test_legal_fixture_local_run_review.py tests/test_legal_fixture_response_normalizer.py -q
```

## Related Files

- `app/backend/services/legal_fixture_local_run_review.py`
- `app/backend/tests/test_legal_fixture_local_run_review.py`
- `app/backend/services/legal_fixture_response_normalizer.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/backend/routers/maintenance.py`
- `docs/LEGAL_FIXTURE_LOCAL_RUN_PACKAGE.md`
- `docs/LEGAL_FIXTURE_RESPONSE_NORMALIZER.md`
- `docs/LEGAL_FIXTURE_RUN_REPORT.md`
- `docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md`
