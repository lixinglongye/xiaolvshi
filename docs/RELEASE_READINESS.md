# Release Readiness

The project now has a deterministic release readiness checklist for maintainer-driven releases.

## Endpoint

```http
GET /api/v1/maintenance/release-readiness
POST /api/v1/maintenance/release-readiness
```

`GET` returns the checklist with every check marked `not_run`. `POST` accepts explicit validation results:

```json
{
  "backend-tests": "pass",
  "frontend-typecheck": "pass",
  "frontend-build": "pass",
  "secret-scan": "pass",
  "model-capability-matrix": "pass",
  "model-configuration-audit": "pass",
  "model-default-optimization": "pass",
  "model-ops-readiness": "pass",
  "model-runtime-router": "pass",
  "model-reasoning-policy": "pass",
  "model-request-policy": "pass",
  "model-route-telemetry": "pass",
  "model-route-guardrails": "pass",
  "model-task-inference": "pass",
  "model-callsite-audit": "pass",
  "model-escalation-policy": "pass",
  "model-cost-forecast": "pass",
  "model-cost-guardrails": "pass",
  "model-routing-replay": "pass",
  "model-fallback-chains": "pass",
  "deep-review-release-decision": "pass",
  "document-preflight": "pass",
  "extraction-quality": "pass",
  "privacy-redaction": "pass",
  "instruction-injection-audit": "pass",
  "feedback-triage": "pass",
  "feedback-roadmap-alignment": "pass",
  "user-needs-radar": "pass",
  "legal-review-benchmark": "pass",
  "legal-knowledge-audit": "pass",
  "legal-rag-evaluation": "pass"
}
```

The service does not run shell commands itself. It only evaluates results supplied by a maintainer or CI job.

## Required checks

- Backend regression tests.
- Frontend TypeScript check.
- Frontend production build.
- Secret and credential scan.
- Gemini model capability matrix coverage.
- Model configuration audit coverage.
- Model default optimization coverage.
- Model operations readiness coverage.
- Runtime model router coverage.
- Gemini reasoning effort policy coverage.
- Generation request parameter policy coverage.
- Model route telemetry coverage.
- Model route guardrail coverage.
- Model task inference coverage.
- Model callsite task audit coverage.
- Cheap-first model escalation policy coverage.
- Model cost forecast coverage.
- Model cost guardrail coverage.
- Model routing replay coverage.
- Model fallback chain coverage.
- Deep-review release decision coverage.
- Document preflight routing coverage.
- Extraction quality audit coverage.
- Privacy redaction coverage.
- Instruction injection audit coverage.
- Feedback triage coverage.
- Feedback roadmap alignment coverage.
- User needs radar coverage.
- Legal review benchmark coverage.
- Legal knowledge seed audit coverage.
- Legal RAG evaluation coverage.

Optional evidence checks, such as OSS maintenance evidence, are tracked but do not block releases.

## Status values

- `manual_validation_required`: one or more required checks have not been run.
- `blocked`: one or more required checks failed.
- `ready_for_release_candidate`: every required check passed or was explicitly waived.

## Related files

- `app/backend/services/release_readiness.py`
- `app/backend/routers/maintenance.py`
- `app/backend/tests/test_release_readiness.py`
