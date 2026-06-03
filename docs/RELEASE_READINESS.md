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
  "model-default-recommendation-snapshot": "pass",
  "gemini-newapi-cheap-first-policy": "pass",
  "model-price-refresh-monitor": "pass",
  "model-gateway-compatibility": "pass",
  "model-gateway-health-plan": "pass",
  "model-gateway-probe-evaluation": "pass",
  "model-lifecycle-policy": "pass",
  "model-ops-readiness": "pass",
  "model-runtime-router": "pass",
  "model-reasoning-policy": "pass",
  "model-request-policy": "pass",
  "model-request-cost-bounds": "pass",
  "model-cache-policy": "pass",
  "model-route-telemetry": "pass",
  "model-route-guardrails": "pass",
  "model-task-inference": "pass",
  "model-callsite-audit": "pass",
  "model-escalation-policy": "pass",
  "model-cost-forecast": "pass",
  "model-cost-regression-snapshots": "pass",
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
- Gemini/NewAPI default recommendation snapshot coverage.
- Gemini/NewAPI cheap-first policy coverage.
- Gemini and gateway price refresh monitor coverage.
- Model gateway compatibility coverage.
- Model gateway health plan coverage.
- Model gateway probe evaluation coverage.
- Gemini model lifecycle policy coverage.
- Model operations readiness coverage.
- Runtime model router coverage.
- Gemini reasoning effort policy coverage.
- Generation request parameter policy coverage.
- Model request cost bounds coverage.
- Model cache policy coverage.
- Model route telemetry coverage.
- Model route guardrail coverage.
- Model task inference coverage.
- Model callsite task audit coverage.
- Cheap-first model escalation policy coverage.
- Model cost forecast coverage.
- Model cost regression snapshot coverage.
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
- Legal review benchmark coverage, including research-backed legal AI backlog planning, legal document benchmark fixtures, small legal corpus expansion, RAG failure fixtures, resource-capped public benchmark samplers, quick laptop-safe fixture suites, fixture-level Gemini/NewAPI model matrices, cheap-first fixture prompt packs, safe gateway request manifests, laptop-safe fixture run plans, one-step local run reviews, archive-safe fixture result summaries, cheap-first fixture run reports, release evidence bundles, lightweight synthetic document fixtures, and fixture-driven improvement plans.
- Legal knowledge seed audit coverage.
- Legal RAG evaluation and grounding quick-audit coverage.

Optional evidence checks, such as OSS maintenance evidence, product feature gap radar, billing entitlement gap evidence, case evidence graph contracts, matter intake readiness, deadline validation, client delivery transparency, route telemetry persistence planning, maintenance heartbeat evidence, and the continuous update ledger, are tracked but do not block releases.

## Status values

- `manual_validation_required`: one or more required checks have not been run.
- `blocked`: one or more required checks failed.
- `ready_for_release_candidate`: every required check passed or was explicitly waived.

## Related files

- `app/backend/services/release_readiness.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/billing_entitlement_gap.py`
- `app/backend/services/case_evidence_graph.py`
- `app/backend/services/client_delivery_transparency_policy.py`
- `app/backend/services/deadline_validation_policy.py`
- `app/backend/services/gemini_newapi_cheap_first_policy.py`
- `app/backend/services/legal_document_benchmark_fixtures.py`
- `app/backend/services/legal_rag_failure_fixtures.py`
- `app/backend/services/small_legal_document_corpus_expansion.py`
- `app/backend/services/matter_intake_readiness_policy.py`
- `app/backend/services/model_default_recommendation_snapshot.py`
- `app/backend/services/model_price_refresh_monitor.py`
- `app/backend/services/model_cost_regression_snapshots.py`
- `app/backend/services/route_telemetry_persistence_plan.py`
- `app/backend/services/maintenance_heartbeat_evidence.py`
- `app/backend/services/product_feature_gap_radar.py`
- `app/backend/services/legal_fixture_result_archive.py`
- `app/backend/services/legal_research_backlog.py`
- `app/backend/routers/maintenance.py`
- `app/backend/tests/test_release_readiness.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/tests/test_billing_entitlement_gap.py`
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/tests/test_client_delivery_transparency_policy.py`
- `app/backend/tests/test_deadline_validation_policy.py`
- `app/backend/tests/test_gemini_newapi_cheap_first_policy.py`
- `app/backend/tests/test_legal_document_benchmark_fixtures.py`
- `app/backend/tests/test_legal_rag_failure_fixtures.py`
- `app/backend/tests/test_small_legal_document_corpus_expansion.py`
- `app/backend/tests/test_matter_intake_readiness_policy.py`
- `app/backend/tests/test_model_default_recommendation_snapshot.py`
- `app/backend/tests/test_model_price_refresh_monitor.py`
- `app/backend/tests/test_model_cost_regression_snapshots.py`
- `app/backend/tests/test_route_telemetry_persistence_plan.py`
- `app/backend/tests/test_maintenance_heartbeat_evidence.py`
- `app/backend/tests/test_product_feature_gap_radar.py`
- `app/backend/tests/test_legal_fixture_result_archive.py`
- `app/backend/tests/test_legal_research_backlog.py`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md`
- `docs/DEADLINE_VALIDATION_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_RAG_FAILURE_FIXTURES.md`
- `docs/SMALL_LEGAL_DOCUMENT_CORPUS_EXPANSION.md`
- `docs/MATTER_INTAKE_READINESS_POLICY.md`
- `docs/MODEL_DEFAULT_RECOMMENDATION_SNAPSHOT.md`
- `docs/MODEL_PRICE_REFRESH_MONITOR.md`
- `docs/MODEL_COST_REGRESSION_SNAPSHOTS.md`
- `docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/LEGAL_RESEARCH_BACKLOG.md`
