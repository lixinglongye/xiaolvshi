# OSS Maintenance Evidence

Maintenance evidence now includes a legal document benchmark coverage matrix. It helps reviewers see which tiny synthetic legal-document fixtures exist, which document types are still missing, and why broad coverage claims remain blocked until more low-resource fixtures are added.

The current matrix target set is locally complete after adding evidence-catalog, settlement-agreement, and legal-opinion fixtures. OSS support claims should still describe this as synthetic local regression evidence, not external adoption, public benchmark scores, or real client-document coverage.

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

`docs/ROUTE_TELEMETRY_OPS_SUMMARY.md` documents the implemented
`GET /api/v1/maintenance/route-telemetry-ops-summary` endpoint. It summarizes
sanitized persisted route telemetry aggregates for failure, premium-model,
over-budget, operator-review, unknown-model, and downgrade review, while
excluding prompts, legal text, credentials, raw payloads, emails, and raw model
outputs.

`docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md` documents the implemented
`GET /api/v1/maintenance/route-telemetry-triage` endpoint. It turns those
summary checks into maintainer actions for cheap-first drift, daily hotspots,
unknown models, and missing staging telemetry, without storing raw route events
or model payloads.

`docs/ROUTE_TELEMETRY_REMEDIATION_PLAN.md` documents the implemented
`GET /api/v1/maintenance/route-telemetry-remediation` endpoint. It maps triage
items to reviewed remediation steps, env suggestions, and validation commands
without writing configuration or calling NewAPI/Gemini.

`docs/CONTINUOUS_SESSION_EVIDENCE.md` documents the backend validator and
reviewer contract for continuous 24-hour session validation. Support forms
should distinguish the already reviewable 100+ update evidence from the
still-unproven 24-hour continuous window.

`docs/CONTINUOUS_SESSION_TIMELINE.md` documents the implemented reviewer timeline
for `GET`/`POST` `/api/v1/maintenance/continuous-session-timeline`. The
timeline merges ledger, session validator, heartbeat, low-resource legal
fixture, and release review metadata only. It must not store secrets, account
data, emails, raw legal text, raw prompts, gateway payloads, or model original
outputs, and support forms must not cite it as 24-hour proof until real
timestamped records pass the gate.

`docs/GIT_HISTORY_EVIDENCE.md` documents the implemented reviewer contract for
`GET /api/v1/maintenance/git-history-evidence`. That evidence may support a
commit-cadence statement by computing commit count, longest cadence window, and
maximum adjacent-commit gap from Git commit metadata. It must not be used as
automatic proof of test execution, remote push history, credential scanning, or
low-resource legal fixture execution.

`docs/VALIDATION_EVENT_EVIDENCE.md` documents the upcoming metadata-only
`GET`/`POST` `/api/v1/maintenance/validation-event-evidence` endpoint for
non-git validation events: input validation tests, credential scans, pushes,
reviews/release reviews, and legal fixture checks. Support applications may
cite it only as a reviewer-safe evidence source after records exist; it must
not include raw stdout, raw stderr, logs, full legal text, raw model output,
secrets, emails, or passwords, and it must not be described as completing the
24-hour target.

`docs/CONTINUOUS_SESSION_REVIEW_PACKET.md` documents the upcoming
`GET`/`POST` `/api/v1/maintenance/continuous-session-review-packet` endpoint.
Support applications may use it as a metadata-only reviewer packet that indexes
ledger, timeline, git cadence, and validation-event evidence with section
statuses, hashes, `evidence_paths`, blockers, review questions, and a privacy
boundary. It must not include raw logs/stdout/stderr, complete legal text, raw
model output, credentials, or emails, and it must not be cited as standalone
proof that the 24-hour session is complete.

`docs/CONTINUOUS_SESSION_RUN_MONITOR.md` documents the implemented
`GET`/`POST` `/api/v1/maintenance/continuous-session-run-monitor` endpoint.
Support applications may cite it only as a metadata-only active-run monitor for
elapsed hours, current checkpoint gaps, missing evidence types, blockers, and
next actions. It does not prove 24h completion; that claim still requires real
timestamped events joined through the timeline and review packet. It must not
store raw logs, legal text, model outputs, credentials, or emails.

`docs/GEMINI_NEWAPI_MODEL_SELECTOR.md` documents the metadata-only
`GET`/`POST` `/api/v1/maintenance/gemini-newapi-model-selector` selector
evidence endpoint. Support applications may cite it only as a model selection
audit for normalized Gemini/NewAPI ids, task labels, cost tiers, cheap-first
candidate chains, warnings, and evidence paths. It is not a live NewAPI probe,
does not store prompts or raw model output, and does not prove the 24-hour
maintenance window.

`docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md` documents the companion metadata-only
`GET`/`POST` `/api/v1/maintenance/gemini-newapi-selector-replay` endpoint.
Support applications may cite it only as selector regression evidence for fixed
cheap-first, balanced-after-precheck, catalog-review, premium-exception, and
high-frequency premium-block scenarios. It does not call NewAPI, store
credentials, prompts, raw legal text, raw model outputs, or emails, and does
not prove the 24-hour maintenance window.

`docs/LEGAL_ADOPTION_RESEARCH_BRIDGE.md` documents the metadata-only
`GET /api/v1/maintenance/legal-review-benchmark/adoption-research-bridge`
endpoint. Support applications may cite it only as a repository-backed mapping
from public research/adoption signals to local user needs, product gaps,
cheap-first validation commands, and release checks. It must not be described
as proof of law-firm adoption, survey results, productivity gains, public
benchmark scores, live NewAPI calls, or external ecosystem importance.

## Why this exists

Support applications often ask for proof of active maintenance, review duties, release management, and ecosystem importance. The service intentionally ties each claim to repository artifacts so the maintainer can avoid unverifiable statements.

It is safe to say this repository has active development, reviewability controls, tests, documentation, and release-readiness logic. It is not safe to claim external adoption, third-party pull-request volume, issue triage volume, or production releases unless those records exist publicly in GitHub.

Recent UI evidence includes runtime router discovery smoke, the case workbench
state event panel, the legal RAG research panel, and the billing usage workspace
badge. Current follow-up evidence adds billing report preflight, privacy-safe
case edit runtime events, metadata-only Legal RAG context cache/copy controls,
and a best-effort document-generation quota consumption attempt. New backend and
full-stack evidence also adds generated_documents CRUD quota guards,
case evidence-catalog/civil-complaint quota guards, selected-source Legal RAG
request metadata, deep-review first-principles document-generation quota guards,
metadata-level selected-source citation validation, a metadata-only
selected-source validation maintenance route, a local-only billing payment
reconciliation policy, task runtime notification summaries, a deterministic
laptop-safe legal document benchmark suite, a LegalBench/LexGLUE/COLIEE
research registry mapped to local low-resource validation, and a maintenance UI
section for that registry. The latest product-research evidence adds a legal
adoption research bridge that maps public legal-AI papers and professional AI
governance/adoption signals to local user needs, product gaps, cheap-first
validation commands, and release checks without storing raw survey or benchmark
content. The latest safety and reviewer-readiness evidence adds deep-review
selected-source report binding, quota delivery decisions, feedback issue
clustering, evidence bundle integrity checks, privacy retention rules,
release-claim compliance checks, case export readiness, and admin audit policy.
Future claims for real payment provider settlement/webhook
verification, automatic deep-review report binding for selected-source
validation, public benchmark scores, and external benchmark adoption should
still stay out of support applications until matching merged evidence exists.

## Evidence categories

- Model operations: model catalog, configuration audit, default optimization, default recommendation snapshots, Gemini/NewAPI cheap-first policy, Gemini/NewAPI model selector evidence, Gemini/NewAPI selector replay evidence, Gemini/NewAPI cheap-first calibration, price-refresh monitoring, cost regression snapshots, gateway compatibility, gateway health planning, sanitized gateway probe evaluation, Gemini lifecycle policy, model-ops readiness, budget policy, task inference, runtime routing, reasoning effort policy, request parameter policy, request cost bounds, cache policy, route telemetry, route telemetry persistence planning, privacy-safe route telemetry repository, route guardrails, callsite audit, fallback chains, routing replay, usage-safe telemetry.
- Quality control: deep-review quality gates, legal document template coverage, contract clause extraction schema, legal document export readiness, case export readiness checks, legal-review benchmark cases, legal document benchmark fixtures, deterministic legal document benchmark suite checks, LegalBench/LexGLUE/COLIEE research registry mapping and UI evidence, legal adoption research bridge evidence, small legal corpus expansion, RAG failure fixtures, durable legal source index planning, metadata-only legal source index persistence, legal RAG index binding and route exposure, metadata-only Legal RAG research context cache/copy controls, selected-source Legal RAG request metadata, citation validation, deep-review binding, and maintenance self-checks, external legal-AI research digests, research-backed legal AI backlog planning, resource-capped public benchmark samplers, quick laptop-safe legal fixture suites, fixture-level Gemini/NewAPI model matrices, cheap-first legal fixture prompt packs, safe gateway request manifests, laptop-safe fixture run plans, one-at-a-time local run packages, response normalizers, one-step local run reviews, archive-safe fixture result summaries, cheap-first fixture run reports, release evidence bundles, lightweight synthetic legal document fixtures, and fixture-driven prompt/schema improvement planning.
- Document intake: OCR import readiness states, retry policy, scanned-page detection, and manual-review routing.
- Review operations: citation, evidence, source freshness, evidence exhibit packages, evidence bundle integrity, legal grounding quick audits, selected-source request metadata, the case evidence graph contract, the case workbench payload contract, case workbench persistence planning, case workbench state repository persistence, case workbench runtime binding and routes, privacy-safe case edit runtime events, task runtime notification summaries, the case intake completeness checklist, matter intake readiness, case timeline deadline risk, deadline validation, lawyer review workflow, document delivery package manifests, document version diff checklists, the client delivery risk checklist, quota delivery decisions, and client delivery transparency.
- Security and collaboration: least-privilege case team roles, case role permission matrices, client-only scopes, sensitive-operation approvals, privacy retention rules, release-claim compliance checks, admin audit policy, privacy-minimized matter audit retention, and access audit requirements.
- Release management: risk scoring and unified release decision.
- Product visibility: frontend report page, case detail page, report mapping, legal RAG research panel, and API types.
- Maintenance planning: user research, maintenance notes, feedback lifecycle policy, adoption research bridge evidence, heartbeat evidence, continuous session evidence validator, continuous session timeline contract, continuous session review packet, continuous session run monitor, validation-event metadata evidence, git-history commit-cadence evidence, billing entitlement gap evidence, billing usage quota policy, billing quota persistence planning, billing quota migration planning, billing quota repository persistence, billing entitlement quota binding, billing quota consumption route, billing report preflight route, generated_documents CRUD quota guards, case generation quota guards, deep-review document generation quota guards, local payment reconciliation policy, document-generation quota consumption attempt, typed runtime API clients, runtime router discovery smoke, case workbench state event UI, legal RAG research UI, legal benchmark registry UI, billing usage workspace badge, product feature gap radar, and the continuous update ledger.

## Related files

- `app/backend/services/maintenance_evidence.py`
- `app/backend/alembic/versions/b7a2c9d4e6f1_repository_persistence_indexes.py`
- `app/backend/models/billing_quota_idempotency_keys.py`
- `app/backend/models/billing_quota_usage_counters.py`
- `app/backend/models/case_workbench_section_states.py`
- `app/backend/models/case_workbench_state_events.py`
- `app/backend/models/legal_source_index_entries.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/continuous_session_evidence.py`
- `app/backend/services/continuous_session_run_monitor.py`
- `app/backend/services/billing_entitlement_gap.py`
- `app/backend/routers/billing_usage.py`
- `app/backend/services/billing_quota_migration_plan.py`
- `app/backend/services/billing_quota_persistence_plan.py`
- `app/backend/services/billing_quota_repository.py`
- `app/backend/services/billing_entitlement_quota_binding.py`
- `app/backend/services/billing_payment_reconciliation.py`
- `app/backend/services/billing_usage_quota_policy.py`
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
- `app/backend/services/legal_document_benchmark_suite.py`
- `app/backend/services/legal_adoption_research_bridge.py`
- `app/backend/services/legal_rag_failure_fixtures.py`
- `app/backend/services/legal_source_ingestion_metadata.py`
- `app/backend/services/legal_source_freshness_policy.py`
- `app/backend/services/legal_source_durable_index_plan.py`
- `app/backend/services/legal_source_index_repository.py`
- `app/backend/services/legal_rag_index_binding.py`
- `app/backend/routers/legal_rag.py`
- `app/backend/services/legal_rag_request_metadata.py`
- `app/backend/routers/case_intelligence.py`
- `app/backend/services/case_intelligence.py`
- `app/backend/services/case_ai_workbench.py`
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
- `app/backend/tests/test_billing_payment_reconciliation.py`
- `app/backend/tests/test_billing_usage_quota_policy.py`
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
- `app/backend/tests/test_legal_document_benchmark_suite.py`
- `app/backend/tests/test_legal_rag_failure_fixtures.py`
- `app/backend/tests/test_legal_source_ingestion_metadata.py`
- `app/backend/tests/test_legal_source_freshness_policy.py`
- `app/backend/tests/test_legal_source_durable_index_plan.py`
- `app/backend/tests/test_legal_source_index_repository.py`
- `app/backend/tests/test_legal_rag_index_binding.py`
- `app/backend/tests/test_legal_rag_router.py`
- `app/backend/tests/test_legal_rag_request_metadata.py`
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
- `app/frontend/src/components/billing/BillingUsageBadge.tsx`
- `app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx`
- `app/frontend/src/components/cases/LegalRagResearchPanel.tsx`
- `app/frontend/src/components/Layout.tsx`
- `app/frontend/src/pages/CaseDetailPage.tsx`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/CONTINUOUS_SESSION_EVIDENCE.md`
- `docs/CONTINUOUS_SESSION_TIMELINE.md`
- `docs/CONTINUOUS_SESSION_REVIEW_PACKET.md`
- `docs/CONTINUOUS_SESSION_RUN_MONITOR.md`
- `docs/VALIDATION_EVENT_EVIDENCE.md`
- `docs/GIT_HISTORY_EVIDENCE.md`
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
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md`
- `docs/GEMINI_NEWAPI_MODEL_SELECTOR.md`
- `docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md`
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
