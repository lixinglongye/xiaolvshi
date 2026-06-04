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

Recent integrated batches moved case workbench persistence planning, legal
source durable index planning, billing quota migration planning, validated
repository implementations, service-level runtime/RAG/entitlement bindings,
authenticated runtime/RAG/billing usage routes, and typed frontend API clients
from the queue into shipped evidence. The latest frontend batch also ships the
main-app runtime router discovery smoke, a case overview runtime state/event
panel, a metadata-only legal RAG research panel, and a global billing quota
badge. The current follow-up evidence adds a read-only billing report preflight
route, privacy-safe case edit runtime events for material/evidence/fact/task
changes, metadata-only Legal RAG context cache/copy controls, a best-effort
document-generation quota consumption attempt, server-side generated_documents
CRUD quota guards, case evidence-catalog/civil-complaint quota guards,
deep-review first-principles document-generation quota guards,
selected-source Legal RAG request metadata propagation, metadata-level
selected-source citation validation, a metadata-only maintenance self-check
route for selected-source validation, a local-only billing payment
reconciliation policy, task runtime notification summaries, a deterministic
laptop-safe legal document benchmark suite, a LegalBench/LexGLUE/COLIEE
research registry mapped to low-resource local tests, and a maintenance UI
section for that registry. The latest adoption-research bridge joins public
legal-AI research, professional AI governance/adoption signals, existing user
needs, product feature gaps, cheap-first validation commands, and release gates
without storing survey free text, raw benchmark samples, legal text, model
outputs, or secrets.
The latest model-ops batch adds a route telemetry operations summary that turns
sanitized persisted route aggregates into release-review checks for failures,
premium-model drift, over-budget pressure, operator-review load, unknown
models, and cheap-first downgrade evidence.
The follow-up triage queue converts those checks into prioritized maintainer
actions, including daily hotspots and missing staging telemetry, without
copying raw route events or model payloads.
The newest remediation plan maps those triage actions to operator-reviewed
cheap-first repair steps, env suggestions, and validation commands without
writing config or calling NewAPI/Gemini.
This batch also adds deep-review selected-source report binding, quota delivery
decisions for export/client delivery/account-plan review, deterministic feedback
issue clustering, metadata-only evidence bundle integrity checks, privacy
retention rules, release-claim compliance checks, case export readiness checks,
and admin audit policy evidence. The medium/large update count is now at or
above 100, but the goal is still not complete because the 24-hour continuous
validation window remains unproven.
These are reviewable product slices; they do not finish real payment provider
settlement or webhook verification, automatic deep-review report binding for
selected-source validation, raw contract extraction, or a database-backed team
workspace.

## Completion Policy

The ledger must not mark the goal complete until both conditions are true:

1. A full 24-hour window is backed by timestamped commits, test runs, or validation records.
2. At least 100 medium/large updates are reviewable in the repository.

The second condition is currently satisfied by repository evidence. The first
condition is still unsatisfied, so `completion_ready` remains `false`.

Small legal fixture tests can count only when they produce repository-backed evidence such as a service, test, documentation update, endpoint, or reviewer-facing UI change. Local-only experiments, raw model outputs, account credentials, and client documents must not be committed.

`docs/CONTINUOUS_SESSION_EVIDENCE.md` defines the reviewer-facing contract for
the 24-hour session validator, and
`POST /api/v1/maintenance/continuous-session-evidence` evaluates explicit
session metadata. The ledger should continue to expose the 100+ update count
separately from the continuous-time proof so a reviewer can see that update
volume is satisfied while the time-window gate remains open. The validator
joins timestamped commits, tests, pushes, review actions, credential scans, and
low-resource legal fixture records without copying raw legal text or model
output into repository evidence.

`docs/CONTINUOUS_SESSION_TIMELINE.md` defines the implemented reviewer timeline
for `GET`/`POST` `/api/v1/maintenance/continuous-session-timeline`. That
endpoint consumes metadata only and merges the ledger, session validator,
heartbeat, low-resource legal fixture, and release review evidence streams. It
must not store secrets, account data, emails, raw legal text, raw gateway
payloads, or model original outputs, and it must keep `completion_ready` blocked
until the 24-hour window is actually proven.

`docs/GIT_HISTORY_EVIDENCE.md` defines the implemented reviewer contract for
`GET /api/v1/maintenance/git-history-evidence`. That endpoint computes real
commit cadence from Git commit metadata, including commit count, longest
cadence window, and maximum adjacent-commit gap. The ledger cites those metrics
as cadence evidence only. It must not treat commit metadata as automatic proof
that tests ran, commits were pushed, credential scans passed, or low-resource
legal fixtures executed.

`docs/VALIDATION_EVENT_EVIDENCE.md` defines the upcoming metadata-only contract
for `GET`/`POST` `/api/v1/maintenance/validation-event-evidence`. That endpoint
can add non-git validation rows for input validation tests, `credential_scan`,
`push`, `review`/`release_review`, and `legal_fixture` events. Accepted records
should contain only timestamps, opaque check/run/validation IDs, optional
commit hashes, statuses, labels, and repository evidence paths. They must not
store raw stdout, raw stderr, logs, complete legal text, raw model output,
credentials, emails, or passwords, and they do not make the 24-hour target
complete by themselves.

`docs/CONTINUOUS_SESSION_REVIEW_PACKET.md` defines the upcoming
`GET`/`POST` `/api/v1/maintenance/continuous-session-review-packet` endpoint.
That endpoint packages the ledger, continuous-session timeline, git-history
cadence, and validation-event evidence into a metadata-only reviewer/support
packet. The packet may expose section statuses, hashes, repository
`evidence_paths`, blockers, review questions, and the privacy boundary, but not
raw logs, stdout, stderr, complete legal text, raw model output, credentials,
or emails. It is an evidence index only and must not claim the 24-hour target is
ready unless real timestamped events and the 100+ update evidence both pass the
joined gate.

`docs/CONTINUOUS_SESSION_RUN_MONITOR.md` defines the implemented
`GET`/`POST` `/api/v1/maintenance/continuous-session-run-monitor` endpoint.
That endpoint monitors an active maintenance run by joining ledger, timeline,
and review-packet metadata into elapsed-hour, current-gap, checkpoint,
required-evidence, blocker, and next-action fields. It is metadata-only and
does not prove 24h completion by itself. The ledger must treat it as an
operational monitor until real timestamped events pass the joined evidence
gate. It must not store raw logs, legal text, model outputs, credentials, or
emails.

`docs/GEMINI_NEWAPI_MODEL_SELECTOR.md` defines the metadata-only
`GET`/`POST` `/api/v1/maintenance/gemini-newapi-model-selector` endpoint. It
indexes Gemini/NewAPI model id normalization, task labels, cost tiers, candidate
chains, warnings, and evidence paths for cheap-first selection review. It must
not store API keys, gateway credentials, prompts, raw legal text, raw model
outputs, or emails, and it must not be counted as proof that NewAPI was called
or that the 24-hour continuous window is complete.

`docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md` defines the metadata-only
`GET`/`POST` `/api/v1/maintenance/gemini-newapi-selector-replay` endpoint. It
replays deterministic selector scenarios for fast/classification/OCR
cheap-first behavior, review/document_generation balanced-after-precheck,
large_pdf/final_review premium exceptions, unknown Gemini-like catalog review,
and high-frequency explicit premium blocking or warning. Submitted rationale is
not echoed. It stores selector regression metadata only and cannot prove live
NewAPI execution or 24-hour completion.

## Low-Resource Test Path

For small machines, use the existing quick suite first:

```http
GET /api/v1/maintenance/legal-review-benchmark/quick-suite?fixture_limit=2
```

The runtime route discovery smoke can run from `app/backend`:

```powershell
python -m pytest tests/test_runtime_router_discovery.py -q
```

This keeps:

- `max_parallel_requests` at `1`.
- Network access disabled by default.
- Public benchmark sources as metadata only until license and attribution review pass.
- Model calls manual and serial.

For 24-hour evidence, each small legal-document run should add only a compact
metadata record: fixture IDs, route labels, coverage score, command label,
timestamp, and repository evidence paths. This lets the same low-resource tests
support both product quality checks and the continuous maintenance timeline.
Commit metadata can sit beside those records to show cadence, but it cannot
replace the fixture record itself.

## Related Files

- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/continuous_session_evidence.py`
- `app/backend/services/continuous_session_run_monitor.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/tests/test_continuous_session_evidence.py`
- `docs/GIT_HISTORY_EVIDENCE.md`
- `docs/VALIDATION_EVENT_EVIDENCE.md`
- `docs/CONTINUOUS_SESSION_REVIEW_PACKET.md`
- `docs/CONTINUOUS_SESSION_RUN_MONITOR.md`
- `docs/GEMINI_NEWAPI_MODEL_SELECTOR.md`
- `docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md`
- `docs/LEGAL_ADOPTION_RESEARCH_BRIDGE.md`
- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/CONTINUOUS_SESSION_TIMELINE.md`
- `app/backend/main.py`
- `app/backend/routers/maintenance.py`
- `app/backend/alembic/versions/b7a2c9d4e6f1_repository_persistence_indexes.py`
- `app/backend/models/billing_quota_idempotency_keys.py`
- `app/backend/models/billing_quota_usage_counters.py`
- `app/backend/models/case_workbench_section_states.py`
- `app/backend/models/case_workbench_state_events.py`
- `app/backend/models/legal_source_index_entries.py`
- `app/backend/services/release_readiness.py`
- `app/backend/services/billing_entitlement_gap.py`
- `app/backend/routers/billing_usage.py`
- `app/backend/services/billing_quota_migration_plan.py`
- `app/backend/services/billing_quota_persistence_plan.py`
- `app/backend/services/billing_quota_repository.py`
- `app/backend/services/billing_entitlement_quota_binding.py`
- `app/backend/services/billing_usage_quota_policy.py`
- `app/backend/services/billing_payment_reconciliation.py`
- `app/backend/routers/generated_documents.py`
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
- `app/backend/services/gemini_newapi_cheap_first_calibration.py`
- `app/backend/services/route_telemetry_repository.py`
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
- `app/backend/services/model_default_recommendation_snapshot.py`
- `app/backend/services/model_price_refresh_monitor.py`
- `app/backend/services/model_cost_regression_snapshots.py`
- `app/backend/services/route_telemetry_persistence_plan.py`
- `app/backend/services/ocr_import_readiness_policy.py`
- `app/backend/services/small_legal_document_corpus_expansion.py`
- `app/backend/services/legal_document_template_matrix.py`
- `app/backend/services/legal_document_benchmark_suite.py`
- `app/backend/services/legal_rag_request_metadata.py`
- `app/backend/routers/case_intelligence.py`
- `app/backend/services/case_intelligence.py`
- `app/backend/services/case_ai_workbench.py`
- `app/backend/services/legal_document_export_readiness.py`
- `app/backend/services/legal_external_research_digest.py`
- `app/backend/services/product_feature_gap_radar.py`
- `app/backend/tests/test_billing_entitlement_gap.py`
- `app/backend/tests/test_billing_usage_router.py`
- `app/backend/tests/test_billing_quota_migration_plan.py`
- `app/backend/tests/test_billing_quota_persistence_plan.py`
- `app/backend/tests/test_billing_quota_repository.py`
- `app/backend/tests/test_billing_entitlement_quota_binding.py`
- `app/backend/tests/test_billing_usage_quota_policy.py`
- `app/backend/tests/test_billing_payment_reconciliation.py`
- `app/backend/tests/test_generated_documents_quota.py`
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
- `app/backend/tests/test_gemini_newapi_cheap_first_calibration.py`
- `app/backend/tests/test_route_telemetry_repository.py`
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
- `app/backend/tests/test_model_default_recommendation_snapshot.py`
- `app/backend/tests/test_model_price_refresh_monitor.py`
- `app/backend/tests/test_model_cost_regression_snapshots.py`
- `app/backend/tests/test_route_telemetry_persistence_plan.py`
- `app/backend/tests/test_ocr_import_readiness_policy.py`
- `app/backend/tests/test_small_legal_document_corpus_expansion.py`
- `app/backend/tests/test_legal_document_template_matrix.py`
- `app/backend/tests/test_legal_document_benchmark_suite.py`
- `app/backend/tests/test_legal_rag_request_metadata.py`
- `app/backend/tests/test_legal_document_export_readiness.py`
- `app/backend/tests/test_legal_external_research_digest.py`
- `app/backend/tests/test_product_feature_gap_radar.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/lib/billingUsageApi.ts`
- `app/frontend/src/lib/legalRagApi.ts`
- `app/frontend/src/lib/workbenchRuntimeApi.ts`
- `app/frontend/src/components/billing/BillingUsageBadge.tsx`
- `app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx`
- `app/frontend/src/components/cases/LegalRagResearchPanel.tsx`
- `app/frontend/src/components/Layout.tsx`
- `app/frontend/src/pages/CaseDetailPage.tsx`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
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
- `docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md`
- `docs/CONTRACT_CLAUSE_EXTRACTION_SCHEMA.md`
- `docs/DEADLINE_VALIDATION_POLICY.md`
- `docs/DOCUMENT_DELIVERY_PACKAGE_MANIFEST.md`
- `docs/DOCUMENT_VERSION_DIFF_CHECKLIST.md`
- `docs/EVIDENCE_EXHIBIT_PACKAGE_POLICY.md`
- `docs/FEEDBACK_LIFECYCLE_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md`
- `docs/LEGAL_RAG_FAILURE_FIXTURES.md`
- `docs/LEGAL_SOURCE_INGESTION_METADATA.md`
- `docs/LEGAL_SOURCE_FRESHNESS_POLICY.md`
- `docs/LEGAL_SOURCE_DURABLE_INDEX_PLAN.md`
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
