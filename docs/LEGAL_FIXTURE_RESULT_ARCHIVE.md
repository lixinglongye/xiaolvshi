# Legal Fixture Result Archive

The result archive endpoint converts normalized cheap-first fixture observations into a repository-safe evidence summary.

## Endpoints

```http
GET /api/v1/maintenance/legal-review-benchmark/result-archive
POST /api/v1/maintenance/legal-review-benchmark/result-archive
```

`GET` returns an empty archive template. `POST` accepts the same shape used by fixture run reports:

```json
{
  "observations": {
    "fixture-service-agreement-small": {
      "route": "legal_review",
      "output_text": "normalized model output used for scoring only"
    }
  },
  "run_metadata": {
    "fixture-service-agreement-small": {
      "phase": "cheap_first",
      "model": "gemini-2.5-flash-lite",
      "estimated_cost_usd": 0.000123,
      "http_status": 200
    }
  }
}
```

The service does not call models, gateways, or public benchmark sources. It reuses the deterministic fixture smoke evaluator, run report, and evidence bundle.

## Archive Policy

The archive response keeps:

- Fixture IDs and titles.
- Smoke status and score.
- Observed route and expected routes.
- Matched/missing signal counts.
- Recommended next step.
- Sanitized run metadata: model, phase, estimated cost, and HTTP status.
- Release decision, release claims, and validation commands.

The archive response excludes:

- Raw model output text.
- Raw gateway JSON responses.
- API keys, authorization headers, and secret-like fields.
- Real client documents, emails, or uploaded document content.

## Low-Resource Use

Run one or two cheap-first fixture requests, normalize the responses through `/local-response-normalizer`, then submit the normalized payload here. This produces a compact release-evidence record without storing raw output.

## Related Files

- `app/backend/services/legal_fixture_result_archive.py`
- `app/backend/tests/test_legal_fixture_result_archive.py`
- `app/backend/services/legal_fixture_run_report.py`
- `app/backend/services/legal_fixture_evidence_bundle.py`
- `app/backend/routers/maintenance.py`
