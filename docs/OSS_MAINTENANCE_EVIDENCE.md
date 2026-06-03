# OSS Maintenance Evidence

This project includes a small maintenance evidence endpoint for open-source support applications and reviewer-facing project summaries.

## Endpoint

```http
GET /api/v1/maintenance/oss-evidence?language=en
GET /api/v1/maintenance/oss-evidence?language=zh
```

The response includes:

- `project`: repository URL and project domain.
- `maintainer_role`: the role claimed for this repository.
- `evidence_score`: a deterministic score based on reviewable maintenance signals.
- `signals`: code, test, documentation, and release-management evidence paths.
- `responsibilities`: ongoing maintainer duties.
- `release_management`: current release-readiness controls.
- `application_guardrails`: claims that must be manually verified before submitting a support form.
- `form_answer`: a concise English or Chinese paragraph suitable for support application fields.

The frontend `/maintenance` page renders the OSS evidence, release readiness, user needs radar, research backlog, legal benchmark fixtures, and model-routing evidence in one reviewer-facing surface. The backend also exposes `/api/v1/maintenance/continuous-update-ledger` as progress evidence for long-running maintenance targets and `/api/v1/maintenance/product-feature-gaps` as the incomplete product capability register.

## Why this exists

Support applications often ask for proof of active maintenance, review duties, release management, and ecosystem importance. The service intentionally ties each claim to repository artifacts so the maintainer can avoid unverifiable statements.

It is safe to say this repository has active development, reviewability controls, tests, documentation, and release-readiness logic. It is not safe to claim external adoption, third-party pull-request volume, issue triage volume, or production releases unless those records exist publicly in GitHub.

## Evidence categories

- Model operations: model catalog, configuration audit, default optimization, default recommendation snapshots, Gemini/NewAPI cheap-first policy, price-refresh monitoring, cost regression snapshots, gateway compatibility, gateway health planning, sanitized gateway probe evaluation, Gemini lifecycle policy, model-ops readiness, budget policy, task inference, runtime routing, reasoning effort policy, request parameter policy, request cost bounds, cache policy, route telemetry, route telemetry persistence planning, route guardrails, callsite audit, fallback chains, routing replay, usage-safe telemetry.
- Quality control: deep-review quality gates, legal document template coverage, contract clause extraction schema, legal document export readiness, legal-review benchmark cases, legal document benchmark fixtures, small legal corpus expansion, RAG failure fixtures, durable legal source index planning, metadata-only legal source index persistence, legal RAG index binding and route exposure, external legal-AI research digests, research-backed legal AI backlog planning, resource-capped public benchmark samplers, quick laptop-safe legal fixture suites, fixture-level Gemini/NewAPI model matrices, cheap-first legal fixture prompt packs, safe gateway request manifests, laptop-safe fixture run plans, one-at-a-time local run packages, response normalizers, one-step local run reviews, archive-safe fixture result summaries, cheap-first fixture run reports, release evidence bundles, lightweight synthetic legal document fixtures, and fixture-driven prompt/schema improvement planning.
- Document intake: OCR import readiness states, retry policy, scanned-page detection, and manual-review routing.
- Review operations: citation, evidence, source freshness, evidence exhibit packages, legal grounding quick audits, the case evidence graph contract, the case workbench payload contract, case workbench persistence planning, case workbench state repository persistence, case workbench runtime binding and routes, the case intake completeness checklist, matter intake readiness, case timeline deadline risk, deadline validation, lawyer review workflow, document delivery package manifests, document version diff checklists, the client delivery risk checklist, and client delivery transparency.
- Security and collaboration: least-privilege case team roles, case role permission matrices, client-only scopes, sensitive-operation approvals, privacy-minimized matter audit retention, and access audit requirements.
- Release management: risk scoring and unified release decision.
- Product visibility: frontend report page, report mapping, and API types.
- Maintenance planning: user research, maintenance notes, feedback lifecycle policy, heartbeat evidence, billing entitlement gap evidence, billing usage quota policy, billing quota persistence planning, billing quota migration planning, billing quota repository persistence, billing entitlement quota binding, billing quota consumption route, typed runtime API clients, product feature gap radar, and the continuous update ledger.

## Related files

- `app/backend/services/maintenance_evidence.py`
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
- `app/backend/services/case_intake_completeness.py`
- `app/backend/services/case_role_permission_matrix.py`
- `app/backend/services/case_workbench_payload.py`
- `app/backend/routers/case_workbench_runtime.py`
- `app/backend/services/case_workbench_persistence_plan.py`
- `app/backend/services/case_workbench_state_repository.py`
- `app/backend/services/case_workbench_runtime_binding.py`
- `app/backend/services/case_timeline_deadline_risk.py`
- `app/backend/services/case_team_access_policy.py`
- `app/backend/services/case_task_notification_policy.py`
- `app/backend/services/client_delivery_risk_checklist.py`
- `app/backend/services/client_delivery_transparency_policy.py`
- `app/backend/services/contract_clause_extraction_schema.py`
- `app/backend/services/deadline_validation_policy.py`
- `app/backend/services/document_delivery_package_manifest.py`
- `app/backend/services/document_version_diff_checklist.py`
- `app/backend/services/evidence_exhibit_package_policy.py`
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
- `app/backend/services/lawyer_review_workflow_policy.py`
- `app/backend/services/maintenance_heartbeat_evidence.py`
- `app/backend/services/matter_audit_retention_policy.py`
- `app/backend/services/matter_intake_readiness_policy.py`
- `app/backend/services/model_price_refresh_monitor.py`
- `app/backend/services/model_cost_regression_snapshots.py`
- `app/backend/services/route_telemetry_persistence_plan.py`
- `app/backend/services/ocr_import_readiness_policy.py`
- `app/backend/services/product_feature_gap_radar.py`
- `app/backend/services/legal_external_research_digest.py`
- `app/backend/services/legal_document_export_readiness.py`
- `app/backend/services/legal_document_template_matrix.py`
- `app/backend/services/legal_research_backlog.py`
- `app/backend/routers/maintenance.py`
- `app/backend/tests/test_maintenance_evidence.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/tests/test_billing_entitlement_gap.py`
- `app/backend/tests/test_billing_usage_router.py`
- `app/backend/tests/test_billing_quota_migration_plan.py`
- `app/backend/tests/test_billing_quota_persistence_plan.py`
- `app/backend/tests/test_billing_quota_repository.py`
- `app/backend/tests/test_billing_entitlement_quota_binding.py`
- `app/backend/tests/test_billing_usage_quota_policy.py`
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/tests/test_case_intake_completeness.py`
- `app/backend/tests/test_case_role_permission_matrix.py`
- `app/backend/tests/test_case_workbench_payload.py`
- `app/backend/tests/test_case_workbench_runtime_router.py`
- `app/backend/tests/test_case_workbench_persistence_plan.py`
- `app/backend/tests/test_case_workbench_state_repository.py`
- `app/backend/tests/test_case_workbench_runtime_binding.py`
- `app/backend/tests/test_case_timeline_deadline_risk.py`
- `app/backend/tests/test_case_team_access_policy.py`
- `app/backend/tests/test_case_task_notification_policy.py`
- `app/backend/tests/test_client_delivery_risk_checklist.py`
- `app/backend/tests/test_client_delivery_transparency_policy.py`
- `app/backend/tests/test_contract_clause_extraction_schema.py`
- `app/backend/tests/test_deadline_validation_policy.py`
- `app/backend/tests/test_document_delivery_package_manifest.py`
- `app/backend/tests/test_document_version_diff_checklist.py`
- `app/backend/tests/test_evidence_exhibit_package_policy.py`
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
- `app/backend/tests/test_lawyer_review_workflow_policy.py`
- `app/backend/tests/test_maintenance_heartbeat_evidence.py`
- `app/backend/tests/test_matter_audit_retention_policy.py`
- `app/backend/tests/test_matter_intake_readiness_policy.py`
- `app/backend/tests/test_model_price_refresh_monitor.py`
- `app/backend/tests/test_model_cost_regression_snapshots.py`
- `app/backend/tests/test_route_telemetry_persistence_plan.py`
- `app/backend/tests/test_ocr_import_readiness_policy.py`
- `app/backend/tests/test_product_feature_gap_radar.py`
- `app/backend/tests/test_legal_external_research_digest.py`
- `app/backend/tests/test_legal_document_export_readiness.py`
- `app/backend/tests/test_legal_document_template_matrix.py`
- `app/backend/tests/test_legal_research_backlog.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/lib/billingUsageApi.ts`
- `app/frontend/src/lib/legalRagApi.ts`
- `app/frontend/src/lib/workbenchRuntimeApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/BILLING_QUOTA_MIGRATION_PLAN.md`
- `docs/BILLING_QUOTA_PERSISTENCE_PLAN.md`
- `docs/BILLING_USAGE_QUOTA_POLICY.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CASE_INTAKE_COMPLETENESS.md`
- `docs/CASE_ROLE_PERMISSION_MATRIX.md`
- `docs/CASE_WORKBENCH_PAYLOAD.md`
- `docs/CASE_WORKBENCH_PERSISTENCE_PLAN.md`
- `docs/CASE_TIMELINE_DEADLINE_RISK.md`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
- `docs/CASE_TASK_NOTIFICATION_POLICY.md`
- `docs/CLIENT_DELIVERY_RISK_CHECKLIST.md`
- `docs/EVIDENCE_EXHIBIT_PACKAGE_POLICY.md`
- `docs/CONTRACT_CLAUSE_EXTRACTION_SCHEMA.md`
- `docs/DOCUMENT_DELIVERY_PACKAGE_MANIFEST.md`
- `docs/DOCUMENT_VERSION_DIFF_CHECKLIST.md`
- `docs/FEEDBACK_LIFECYCLE_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/LEGAL_RAG_FAILURE_FIXTURES.md`
- `docs/LEGAL_SOURCE_INGESTION_METADATA.md`
- `docs/LEGAL_SOURCE_FRESHNESS_POLICY.md`
- `docs/LEGAL_SOURCE_DURABLE_INDEX_PLAN.md`
- `docs/LAWYER_REVIEW_WORKFLOW_POLICY.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/MATTER_AUDIT_RETENTION_POLICY.md`
- `docs/MATTER_INTAKE_READINESS_POLICY.md`
- `docs/MODEL_PRICE_REFRESH_MONITOR.md`
- `docs/MODEL_COST_REGRESSION_SNAPSHOTS.md`
- `docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md`
- `docs/OCR_IMPORT_READINESS_POLICY.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md`
- `docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md`
- `docs/SMALL_LEGAL_DOCUMENT_CORPUS_EXPANSION.md`
- `docs/LEGAL_DOCUMENT_EXPORT_READINESS.md`
- `docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md`
- `docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md`
- `docs/DEADLINE_VALIDATION_POLICY.md`
- `docs/MODEL_DEFAULT_RECOMMENDATION_SNAPSHOT.md`
- `docs/USER_RESEARCH_AND_MAINTENANCE.md`
- `docs/LEGAL_RESEARCH_BACKLOG.md`
