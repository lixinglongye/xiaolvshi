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
  "feedback-lifecycle-policy": "pass",
  "user-needs-radar": "pass",
  "legal-review-benchmark": "pass",
  "legal-knowledge-audit": "pass",
  "legal-source-freshness-policy": "pass",
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
- Feedback lifecycle policy coverage.
- User needs radar coverage.
- Legal review benchmark coverage, including research-backed legal AI backlog planning, legal document benchmark fixtures, contract clause extraction schema, small legal corpus expansion, RAG failure fixtures, resource-capped public benchmark samplers, quick laptop-safe fixture suites, fixture-level Gemini/NewAPI model matrices, cheap-first fixture prompt packs, safe gateway request manifests, laptop-safe fixture run plans, one-step local run reviews, archive-safe fixture result summaries, cheap-first fixture run reports, release evidence bundles, lightweight synthetic document fixtures, and fixture-driven improvement plans.
- Legal knowledge seed audit coverage.
- Legal source freshness and jurisdiction policy coverage.
- Legal RAG evaluation and grounding quick-audit coverage.

Optional evidence checks, such as OSS maintenance evidence, product feature gap radar, billing entitlement gap evidence, billing usage quota policy, billing quota persistence planning, billing quota migration planning, billing quota repository persistence, billing entitlement quota binding, billing quota consumption route, case evidence graph contracts, case workbench payload contracts, case workbench persistence planning, case workbench state repository persistence, case workbench runtime binding, case workbench runtime router, frontend runtime API client bindings, case role permission matrices, matter intake readiness, deadline validation, contract clause extraction schemas, document delivery package manifests, document version diff checklists, legal source ingestion metadata, legal source durable index planning, legal source index repository persistence, legal RAG index binding, legal RAG index route, client delivery transparency, route telemetry persistence planning, maintenance heartbeat evidence, and the continuous update ledger, are tracked but do not block releases.

## Status values

- `manual_validation_required`: one or more required checks have not been run.
- `blocked`: one or more required checks failed.
- `ready_for_release_candidate`: every required check passed or was explicitly waived.

## Related files

- `app/backend/services/release_readiness.py`
- `app/backend/alembic/versions/b7a2c9d4e6f1_repository_persistence_indexes.py`
- `app/backend/models/billing_quota_idempotency_keys.py`
- `app/backend/models/billing_quota_usage_counters.py`
- `app/backend/models/case_workbench_section_states.py`
- `app/backend/models/case_workbench_state_events.py`
- `app/backend/models/legal_source_index_entries.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/billing_entitlement_gap.py`
- `app/backend/routers/billing_usage.py`
- `app/backend/services/billing_quota_migration_plan.py`
- `app/backend/services/billing_quota_persistence_plan.py`
- `app/backend/services/billing_quota_repository.py`
- `app/backend/services/billing_entitlement_quota_binding.py`
- `app/backend/services/billing_usage_quota_policy.py`
- `app/backend/services/case_evidence_graph.py`
- `app/backend/services/case_role_permission_matrix.py`
- `app/backend/services/case_workbench_payload.py`
- `app/backend/routers/case_workbench_runtime.py`
- `app/backend/services/case_workbench_persistence_plan.py`
- `app/backend/services/case_workbench_state_repository.py`
- `app/backend/services/case_workbench_runtime_binding.py`
- `app/backend/services/client_delivery_transparency_policy.py`
- `app/backend/services/contract_clause_extraction_schema.py`
- `app/backend/services/deadline_validation_policy.py`
- `app/backend/services/document_delivery_package_manifest.py`
- `app/backend/services/document_version_diff_checklist.py`
- `app/backend/services/feedback_lifecycle_policy.py`
- `app/backend/services/gemini_newapi_cheap_first_policy.py`
- `app/backend/services/legal_document_benchmark_fixtures.py`
- `app/backend/services/legal_rag_failure_fixtures.py`
- `app/backend/services/legal_source_ingestion_metadata.py`
- `app/backend/services/legal_source_freshness_policy.py`
- `app/backend/services/legal_source_durable_index_plan.py`
- `app/backend/services/legal_source_index_repository.py`
- `app/backend/services/legal_rag_index_binding.py`
- `app/backend/routers/legal_rag.py`
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
- `app/backend/tests/test_billing_usage_router.py`
- `app/backend/tests/test_billing_quota_migration_plan.py`
- `app/backend/tests/test_billing_quota_persistence_plan.py`
- `app/backend/tests/test_billing_quota_repository.py`
- `app/backend/tests/test_billing_entitlement_quota_binding.py`
- `app/backend/tests/test_billing_usage_quota_policy.py`
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/tests/test_case_role_permission_matrix.py`
- `app/backend/tests/test_case_workbench_payload.py`
- `app/backend/tests/test_case_workbench_runtime_router.py`
- `app/backend/tests/test_case_workbench_persistence_plan.py`
- `app/backend/tests/test_case_workbench_state_repository.py`
- `app/backend/tests/test_case_workbench_runtime_binding.py`
- `app/backend/tests/test_client_delivery_transparency_policy.py`
- `app/backend/tests/test_contract_clause_extraction_schema.py`
- `app/backend/tests/test_deadline_validation_policy.py`
- `app/backend/tests/test_document_delivery_package_manifest.py`
- `app/backend/tests/test_document_version_diff_checklist.py`
- `app/backend/tests/test_feedback_lifecycle_policy.py`
- `app/backend/tests/test_gemini_newapi_cheap_first_policy.py`
- `app/backend/tests/test_legal_document_benchmark_fixtures.py`
- `app/backend/tests/test_legal_rag_failure_fixtures.py`
- `app/backend/tests/test_legal_source_ingestion_metadata.py`
- `app/backend/tests/test_legal_source_freshness_policy.py`
- `app/backend/tests/test_legal_source_durable_index_plan.py`
- `app/backend/tests/test_legal_source_index_repository.py`
- `app/backend/tests/test_legal_rag_index_binding.py`
- `app/backend/tests/test_legal_rag_router.py`
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
- `app/frontend/src/lib/billingUsageApi.ts`
- `app/frontend/src/lib/legalRagApi.ts`
- `app/frontend/src/lib/workbenchRuntimeApi.ts`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/BILLING_QUOTA_MIGRATION_PLAN.md`
- `docs/BILLING_QUOTA_PERSISTENCE_PLAN.md`
- `docs/BILLING_USAGE_QUOTA_POLICY.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CASE_ROLE_PERMISSION_MATRIX.md`
- `docs/CASE_WORKBENCH_PAYLOAD.md`
- `docs/CASE_WORKBENCH_PERSISTENCE_PLAN.md`
- `docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md`
- `docs/CONTRACT_CLAUSE_EXTRACTION_SCHEMA.md`
- `docs/DEADLINE_VALIDATION_POLICY.md`
- `docs/DOCUMENT_DELIVERY_PACKAGE_MANIFEST.md`
- `docs/DOCUMENT_VERSION_DIFF_CHECKLIST.md`
- `docs/FEEDBACK_LIFECYCLE_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md`
- `docs/LEGAL_RAG_FAILURE_FIXTURES.md`
- `docs/LEGAL_SOURCE_INGESTION_METADATA.md`
- `docs/LEGAL_SOURCE_FRESHNESS_POLICY.md`
- `docs/LEGAL_SOURCE_DURABLE_INDEX_PLAN.md`
- `docs/SMALL_LEGAL_DOCUMENT_CORPUS_EXPANSION.md`
- `docs/MATTER_INTAKE_READINESS_POLICY.md`
- `docs/MODEL_DEFAULT_RECOMMENDATION_SNAPSHOT.md`
- `docs/MODEL_PRICE_REFRESH_MONITOR.md`
- `docs/MODEL_COST_REGRESSION_SNAPSHOTS.md`
- `docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/LEGAL_RESEARCH_BACKLOG.md`
