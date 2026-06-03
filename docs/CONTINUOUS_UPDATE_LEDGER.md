# Continuous Update Ledger

This ledger records progress toward the long-running maintenance target without claiming completion before it is reviewable.

## Endpoint

```http
GET /api/v1/maintenance/continuous-update-ledger
```

The response includes:

- `status`: currently `in_progress`.
- `goal`: the 24-hour and 100+ medium/large update targets.
- `summary`: completed count, remaining count, category counts, and completion flags.
- `completed_updates`: shipped updates with code, test, doc, or UI evidence paths.
- `next_update_queue`: planned medium/large work, prioritized for cheap-first and low-resource validation.
- `low_resource_test_policy`: fixture limits, serial execution policy, and default benchmark endpoint.
- `validation_commands`: small pytest commands that can run on a local laptop.

## Completion Policy

The ledger must not mark the goal complete until both conditions are true:

1. A full 24-hour window is backed by timestamped commits, test runs, or validation records.
2. At least 100 medium/large updates are reviewable in the repository.

Small legal fixture tests can count only when they produce repository-backed evidence such as a service, test, documentation update, endpoint, or reviewer-facing UI change. Local-only experiments, raw model outputs, account credentials, and client documents must not be committed.

## Low-Resource Test Path

For small machines, use the existing quick suite first:

```http
GET /api/v1/maintenance/legal-review-benchmark/quick-suite?fixture_limit=2
```

This keeps:

- `max_parallel_requests` at `1`.
- Network access disabled by default.
- Public benchmark sources as metadata only until license and attribution review pass.
- Model calls manual and serial.

## Related Files

- `app/backend/services/continuous_update_ledger.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/routers/maintenance.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/billing_entitlement_gap.py`
- `app/backend/services/billing_quota_persistence_plan.py`
- `app/backend/services/billing_usage_quota_policy.py`
- `app/backend/services/case_evidence_graph.py`
- `app/backend/services/case_intake_completeness.py`
- `app/backend/services/case_role_permission_matrix.py`
- `app/backend/services/case_workbench_payload.py`
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
- `app/backend/services/lawyer_review_workflow_policy.py`
- `app/backend/services/maintenance_heartbeat_evidence.py`
- `app/backend/services/matter_audit_retention_policy.py`
- `app/backend/services/matter_intake_readiness_policy.py`
- `app/backend/services/model_default_recommendation_snapshot.py`
- `app/backend/services/model_price_refresh_monitor.py`
- `app/backend/services/model_cost_regression_snapshots.py`
- `app/backend/services/route_telemetry_persistence_plan.py`
- `app/backend/services/ocr_import_readiness_policy.py`
- `app/backend/services/small_legal_document_corpus_expansion.py`
- `app/backend/services/legal_document_template_matrix.py`
- `app/backend/services/legal_document_export_readiness.py`
- `app/backend/services/legal_external_research_digest.py`
- `app/backend/services/product_feature_gap_radar.py`
- `app/backend/tests/test_billing_entitlement_gap.py`
- `app/backend/tests/test_billing_quota_persistence_plan.py`
- `app/backend/tests/test_billing_usage_quota_policy.py`
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/tests/test_case_intake_completeness.py`
- `app/backend/tests/test_case_role_permission_matrix.py`
- `app/backend/tests/test_case_workbench_payload.py`
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
- `app/backend/tests/test_lawyer_review_workflow_policy.py`
- `app/backend/tests/test_maintenance_heartbeat_evidence.py`
- `app/backend/tests/test_matter_audit_retention_policy.py`
- `app/backend/tests/test_matter_intake_readiness_policy.py`
- `app/backend/tests/test_model_default_recommendation_snapshot.py`
- `app/backend/tests/test_model_price_refresh_monitor.py`
- `app/backend/tests/test_model_cost_regression_snapshots.py`
- `app/backend/tests/test_route_telemetry_persistence_plan.py`
- `app/backend/tests/test_ocr_import_readiness_policy.py`
- `app/backend/tests/test_small_legal_document_corpus_expansion.py`
- `app/backend/tests/test_legal_document_template_matrix.py`
- `app/backend/tests/test_legal_document_export_readiness.py`
- `app/backend/tests/test_legal_external_research_digest.py`
- `app/backend/tests/test_product_feature_gap_radar.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/BILLING_QUOTA_PERSISTENCE_PLAN.md`
- `docs/BILLING_USAGE_QUOTA_POLICY.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CASE_INTAKE_COMPLETENESS.md`
- `docs/CASE_ROLE_PERMISSION_MATRIX.md`
- `docs/CASE_WORKBENCH_PAYLOAD.md`
- `docs/CASE_TIMELINE_DEADLINE_RISK.md`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
- `docs/CASE_TASK_NOTIFICATION_POLICY.md`
- `docs/CLIENT_DELIVERY_RISK_CHECKLIST.md`
- `docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md`
- `docs/CONTRACT_CLAUSE_EXTRACTION_SCHEMA.md`
- `docs/DEADLINE_VALIDATION_POLICY.md`
- `docs/DOCUMENT_DELIVERY_PACKAGE_MANIFEST.md`
- `docs/DOCUMENT_VERSION_DIFF_CHECKLIST.md`
- `docs/EVIDENCE_EXHIBIT_PACKAGE_POLICY.md`
- `docs/FEEDBACK_LIFECYCLE_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/LEGAL_RAG_FAILURE_FIXTURES.md`
- `docs/LEGAL_SOURCE_INGESTION_METADATA.md`
- `docs/LEGAL_SOURCE_FRESHNESS_POLICY.md`
- `docs/LAWYER_REVIEW_WORKFLOW_POLICY.md`
- `docs/MAINTENANCE_HEARTBEAT_EVIDENCE.md`
- `docs/MATTER_AUDIT_RETENTION_POLICY.md`
- `docs/MATTER_INTAKE_READINESS_POLICY.md`
- `docs/MODEL_DEFAULT_RECOMMENDATION_SNAPSHOT.md`
- `docs/MODEL_PRICE_REFRESH_MONITOR.md`
- `docs/MODEL_COST_REGRESSION_SNAPSHOTS.md`
- `docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md`
- `docs/OCR_IMPORT_READINESS_POLICY.md`
- `docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md`
- `docs/SMALL_LEGAL_DOCUMENT_CORPUS_EXPANSION.md`
- `docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md`
- `docs/LEGAL_DOCUMENT_EXPORT_READINESS.md`
- `docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/USER_RESEARCH_AND_MAINTENANCE.md`
- `docs/RELEASE_READINESS.md`
