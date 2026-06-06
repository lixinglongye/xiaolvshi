# Release Readiness

Recent optional evidence: `legal-document-benchmark-coverage`, `legal-document-benchmark-coverage-ui`, `frontend-ui-regression-gate`, and `legal-document-coverage-claim-policy` expose the local legal-document fixture coverage matrix in backend release checks, the maintenance UI, reviewer-facing UI regression gates, and a claim-review route. The checks are metadata-only and do not claim external benchmark scores, model-run accuracy, universal document support, or real client-document testing.

Additional optional evidence: `legal-document-benchmark-gap-fixtures` validates the synthetic evidence-catalog, settlement-agreement, and legal-opinion fixtures against the same low-resource benchmark suite.

Additional optional evidence: `legal-benchmark-research-refresh` records
metadata-only refresh evidence for LegalBench, LexGLUE, LegalBench-RAG, LexEval,
CaseGen, COLIEE, and adoption bridge mappings. It does not download datasets, claim public benchmark scores,
store external legal text, call models, or handle credentials.

Additional optional evidence: `model-route-legal-benchmark-risk-queue` records
metadata-only cheap-first model-route review against legal benchmark refresh and
user-need coverage. It does not call gateways, write model defaults, download
datasets, claim public benchmark scores, store raw legal text, or handle
credentials.

Additional optional evidence: `legal-rag-authority-citation-gate` records
metadata-only Legal RAG source authority and citation quality checks. It does
not call NewAPI, Gemini, or gateways, download datasets, store raw legal text,
prompts, model outputs, or credentials.

Additional optional evidence: `legal-rag-hallucination-triage-gate` records
metadata-only Legal RAG hallucination triage checks. It does not call NewAPI,
Gemini, or gateways, download datasets, store raw legal text, retrieved
snippets, prompts, model outputs, or credentials.

Additional required evidence: `gemini-newapi-model-alias-matrix` records
metadata-only alias normalization for OpenAI-compatible Gemini gateway model ids.
It does not call NewAPI, Gemini, or gateways, write configuration, shift traffic,
store raw payloads, prompts, legal text, model outputs, credentials, or emails.

Additional required evidence: `model-catalog-candidate-patch-plan` records
metadata-only catalog candidate stubs and required review checks for sanitized
unknown observed Gemini-like model ids. It does not edit `model_catalog.py`,
write configuration, call gateways or the network, shift traffic, or store raw
payloads, prompts, legal text, model outputs, credentials, or emails.

Additional required evidence: `model-gateway-request-compatibility-gate`
records metadata-only OpenAI-compatible Gemini/NewAPI request-shape checks for
task defaults, gateway model compatibility, request parameter caps,
reasoning-effort policy, JSON response-format requirements, and cheap-first cost
bounds. It does not call NewAPI, Gemini, OpenAI, Google, gateways, or the
network, write configuration, shift traffic, or store headers, request bodies,
prompts, raw legal text, model outputs, payloads, emails, or credentials.

Additional required evidence: `route-telemetry-repository` records sanitized
route decisions and derives `estimated_cost_usd` only for known Gemini/NewAPI
catalog model routes using local catalog token pricing. Unknown gateway model
ids keep `estimated_cost_usd` at `0` and continue through unknown model review.
Known catalog models without token pricing metadata are counted separately in
`unpriced_model_count` for maintainer pricing review. It does not call
gateways, write configuration, store raw payloads, prompts, legal text, model
outputs, credentials, or emails.

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
  "frontend-lint": "pass",
  "frontend-typecheck": "pass",
  "frontend-build": "pass",
  "frontend-ui-regression": "pass",
  "secret-scan": "pass",
  "model-capability-matrix": "pass",
  "model-configuration-audit": "pass",
  "model-default-optimization": "pass",
  "model-default-recommendation-snapshot": "pass",
  "gemini-newapi-cheap-first-policy": "pass",
  "gemini-newapi-model-selector": "pass",
  "gemini-newapi-model-alias-matrix": "pass",
  "gemini-newapi-selector-replay": "pass",
  "model-price-refresh-monitor": "pass",
  "model-catalog-candidate-patch-plan": "pass",
  "model-gateway-compatibility": "pass",
  "model-gateway-health-plan": "pass",
  "model-gateway-probe-evaluation": "pass",
  "model-lifecycle-policy": "pass",
  "model-ops-readiness": "pass",
  "model-runtime-router": "pass",
  "model-reasoning-policy": "pass",
  "model-request-policy": "pass",
  "model-gateway-request-compatibility-gate": "pass",
  "model-request-cost-bounds": "pass",
  "model-cache-policy": "pass",
  "model-route-telemetry": "pass",
  "route-telemetry-persistence-plan": "pass",
  "route-telemetry-repository": "pass",
  "route-telemetry-ops-summary": "pass",
  "route-telemetry-triage-queue": "pass",
  "route-telemetry-remediation-plan": "pass",
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
- Gemini/NewAPI model selector evidence coverage.
- Gemini/NewAPI selector replay evidence coverage.
- Gemini and gateway price refresh monitor coverage.
- Model gateway compatibility coverage.
- Model gateway health plan coverage.
- Model gateway probe evaluation coverage.
- Gemini model lifecycle policy coverage.
- Model operations readiness coverage.
- Runtime model router coverage.
- Gemini reasoning effort policy coverage.
- Generation request parameter policy coverage.
- Gateway request compatibility gate coverage.
- Model request cost bounds coverage.
- Model cache policy coverage.
- Model route telemetry coverage.
- Privacy-safe route telemetry repository coverage.
- Route telemetry operations summary coverage.
- Route telemetry triage queue coverage.
- Route telemetry remediation plan coverage.
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
- ModelOps cheap-first canary rollback drill coverage, requiring reviewable
  rehearsal metadata before any cheap-first default movement can claim rollback
  preparedness.
- ModelOps cheap-first canary change manifest coverage, requiring external
  change-set metadata, prerequisites, operator steps, rollback-drill status, and
  no-write/no-secret boundaries before any manual default edit is release-ready.

Optional evidence checks, such as OSS maintenance evidence, product feature gap radar, billing entitlement gap evidence, billing usage quota policy, billing quota persistence planning, billing quota migration planning, billing quota repository persistence, billing entitlement quota binding, billing quota consumption route, case evidence graph contracts, case workbench payload contracts, case workbench persistence planning, case workbench state repository persistence, case workbench runtime binding, case workbench runtime router, frontend runtime API client bindings, runtime router discovery smoke, case workbench frontend state events, legal RAG case research UI, billing usage workspace badge, case role permission matrices, matter intake readiness, deadline validation, contract clause extraction schemas, document delivery package manifests, document version diff checklists, legal source ingestion metadata, legal source durable index planning, legal source index repository persistence, legal RAG index binding, legal RAG index route, client delivery transparency, route telemetry persistence planning, maintenance heartbeat evidence, continuous session run monitor, and the continuous update ledger, are tracked but do not block releases. The route telemetry repository, operations summary, triage queue, and remediation plan are required because they provide the reviewable runtime evidence, maintainer actions, and operator-reviewed repair plan needed before model-routing release claims.

The `runtime-router-discovery-smoke` check is intentionally narrow: once its
test evidence is merged and passing, it should verify that the main FastAPI app
exposes the case workbench, legal RAG, and billing usage runtime paths in
OpenAPI. The related frontend checks use `npm run lint`, `npm run typecheck`,
`npm run build`, and `npm run ui:regression` to verify case workbench state event
panels, metadata-only legal RAG research panels, billing usage badge wiring,
maintenance evidence wiring, and model-ops wiring. The optional
`frontend-ui-regression-gate` records that `/maintenance` and `/model-ops`
still need browser-level network-mocked regression tests; it is not proof that
every browser state is automated.

Additional optional evidence now covers the billing report preflight route,
privacy-safe case edit runtime event binding, metadata-only legal RAG context
cache/copy controls, the document-generation quota consumption attempt,
server-side generated_documents CRUD quota guards, selected-source Legal RAG
request metadata, case evidence-catalog/civil-complaint quota guards,
deep-review first-principles document-generation quota guards, metadata-level
selected-source citation validation, a metadata-only selected-source validation
maintenance route, a local-only billing payment reconciliation policy, task
runtime notification summaries, a deterministic laptop-safe legal document
benchmark suite, a LegalBench/LexGLUE/LegalBench-RAG/LexEval/CaseGen/COLIEE research registry mapped to
low-resource local validation, a metadata-only legal benchmark research refresh
check, a maintenance UI section for that registry, and a metadata-only legal
adoption research bridge that maps public research and
professional AI governance/adoption signals to existing user needs, product
gaps, cheap-first validation commands, and release evidence.
New optional checks also cover deep-review selected-source report binding,
quota delivery decisions, deterministic feedback issue clustering, evidence
bundle integrity, privacy retention rules, release-claim compliance, case export
readiness, and admin audit policy.
The Gemini/NewAPI model selector evidence check verifies metadata-only model id
normalization, cheap-first task candidate chains, premium exception boundaries,
warnings, candidate eligibility, and evidence paths. The check must keep
`default_eligible` rows separate from `review-only` rows so preview, unpriced,
premium-over-budget, premium-exception-only, unknown, or deprecated candidates
cannot be treated as directly promotable defaults; it must not imply that
NewAPI was called or that 24-hour maintenance completion is proven.
The Gemini/NewAPI selector replay evidence check verifies deterministic
scenario coverage for fast/classification/OCR cheap-first behavior,
review/document_generation balanced-after-precheck, large_pdf/final_review
premium exceptions, unknown Gemini-like catalog review, and high-frequency
explicit premium blocking or warning. It stores only scenario ids, task labels,
model ids, canonical ids, cost tiers, decisions, checks, warnings, and evidence
paths; submitted rationale is not echoed and the check must not imply that
NewAPI was called or that 24-hour maintenance completion is proven.
The continuous session run monitor check verifies metadata-only active-run
monitoring for elapsed hours, current gaps, next checkpoints, missing required
evidence, blockers, and next actions. It must not imply that 24h maintenance
completion is proven. Release claims still require real timestamped events
joined through the timeline and review packet, and the monitor must not store
raw logs, legal text, model outputs, credentials, or emails.
The legal adoption research bridge is optional user-research evidence. It must
not imply law-firm adoption, survey results, productivity gains, public
benchmark scores, live NewAPI calls, or external ecosystem importance.
The legal benchmark research refresh is optional quality evidence. It must not
imply dataset downloads, external legal text validation, public benchmark
scores, model calls, credentials, or external adoption.
The model route legal benchmark risk queue is optional model-ops evidence. It
must not imply gateway execution, automatic default changes, public benchmark
performance, legal advice, raw legal-text handling, or credential handling.
The Legal RAG authority citation gate is optional quality evidence. It must not
imply live RAG accuracy, broad jurisdiction coverage, public benchmark
performance, dataset validation, NewAPI/Gemini/gateway execution, raw legal-text
handling, prompt retention, model-output retention, or credential handling.
The Gemini/NewAPI selector checks are required release controls. The continuous
session run monitor and adoption research bridge are optional release evidence.
None of these checks claim
real payment provider settlement or webhook verification, automatic deep-review
report binding for selected-source validation, public benchmark scores, or
external adoption.
The ModelOps cheap-first canary rollback drill is also a required model-ops
release control. It consumes approval packet metadata and exposes trigger
review, holdout confirmation, role, and rehearsal checklist evidence only; it
does not execute rollback, write configuration, call gateways, persist drill
state, or shift production traffic.
The ModelOps cheap-first canary change manifest is the next required release
control after rollback drill evidence. It records external change-set metadata,
prerequisites, operator steps, and validation commands only; it does not write
configuration, write env files, store secret values, call gateways, record
approver identity, apply the change, or shift traffic.

## Status values

- `manual_validation_required`: one or more required checks have not been run.
- `blocked`: one or more required checks failed.
- `ready_for_release_candidate`: every required check passed or was explicitly waived.

## Related files

- `app/backend/services/release_readiness.py`
- `app/backend/main.py`
- `app/backend/alembic/versions/b7a2c9d4e6f1_repository_persistence_indexes.py`
- `app/backend/models/billing_quota_idempotency_keys.py`
- `app/backend/models/billing_quota_usage_counters.py`
- `app/backend/models/case_workbench_section_states.py`
- `app/backend/models/case_workbench_state_events.py`
- `app/backend/models/legal_source_index_entries.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/continuous_session_run_monitor.py`
- `app/backend/services/model_route_legal_benchmark_risk_queue.py`
- `app/backend/services/legal_rag_authority_citation_gate.py`
- `app/backend/services/legal_benchmark_research_refresh.py`
- `app/backend/services/legal_adoption_research_bridge.py`
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
- `app/backend/services/legal_rag_request_metadata.py`
- `app/backend/routers/case_intelligence.py`
- `app/backend/services/case_intelligence.py`
- `app/backend/services/case_ai_workbench.py`
- `app/backend/services/small_legal_document_corpus_expansion.py`
- `app/backend/services/legal_document_benchmark_suite.py`
- `app/backend/services/matter_intake_readiness_policy.py`
- `app/backend/services/model_default_recommendation_snapshot.py`
- `app/backend/services/model_price_refresh_monitor.py`
- `app/backend/services/model_ops_cheap_first_canary_rollback_drill.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_rollback_drill.py`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_ROLLBACK_DRILL.md`
- `app/backend/services/model_ops_cheap_first_canary_change_manifest.py`
- `app/backend/tests/test_model_ops_cheap_first_canary_change_manifest.py`
- `docs/MODEL_OPS_CHEAP_FIRST_CANARY_CHANGE_MANIFEST.md`
- `app/backend/services/model_cost_regression_snapshots.py`
- `app/backend/services/route_telemetry_persistence_plan.py`
- `app/backend/services/maintenance_heartbeat_evidence.py`
- `app/backend/services/product_feature_gap_radar.py`
- `app/backend/services/legal_fixture_result_archive.py`
- `app/backend/services/legal_research_backlog.py`
- `app/backend/routers/maintenance.py`
- `app/backend/tests/test_release_readiness.py`
- `app/backend/tests/test_continuous_update_ledger.py`
- `app/backend/tests/test_model_route_legal_benchmark_risk_queue.py`
- `app/backend/tests/test_legal_rag_authority_citation_gate.py`
- `app/backend/tests/test_legal_benchmark_research_refresh.py`
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
- `app/backend/tests/test_legal_rag_request_metadata.py`
- `app/backend/tests/test_small_legal_document_corpus_expansion.py`
- `app/backend/tests/test_legal_document_benchmark_suite.py`
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
- `docs/CONTINUOUS_SESSION_RUN_MONITOR.md`
- `app/frontend/src/lib/billingUsageApi.ts`
- `app/frontend/src/lib/legalRagApi.ts`
- `app/frontend/src/lib/workbenchRuntimeApi.ts`
- `app/frontend/src/components/billing/BillingUsageBadge.tsx`
- `app/frontend/src/components/cases/CaseWorkbenchRuntimePanel.tsx`
- `app/frontend/src/components/cases/LegalRagResearchPanel.tsx`
- `app/frontend/src/components/Layout.tsx`
- `app/frontend/src/pages/CaseDetailPage.tsx`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/BILLING_QUOTA_MIGRATION_PLAN.md`
- `docs/BILLING_QUOTA_PERSISTENCE_PLAN.md`
- `docs/BILLING_USAGE_QUOTA_POLICY.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CASE_ROLE_PERMISSION_MATRIX.md`
- `docs/CASE_ACCESS_CONTROL_RUNTIME_GATE.md`
- `docs/CASE_WORKBENCH_PAYLOAD.md`
- `docs/CASE_WORKBENCH_PERSISTENCE_PLAN.md`
- `docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md`
- `docs/CONTRACT_CLAUSE_EXTRACTION_SCHEMA.md`
- `docs/DEADLINE_VALIDATION_POLICY.md`
- `docs/DOCUMENT_DELIVERY_PACKAGE_MANIFEST.md`
- `docs/DOCUMENT_VERSION_DIFF_CHECKLIST.md`
- `docs/FEEDBACK_LIFECYCLE_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md`
- `docs/GEMINI_NEWAPI_CHEAP_FIRST_CALIBRATION.md`
- `docs/GEMINI_NEWAPI_MODEL_SELECTOR.md`
- `docs/GEMINI_NEWAPI_SELECTOR_REPLAY.md`
- `docs/LEGAL_BENCHMARK_RESEARCH_REFRESH.md`
- `docs/MODEL_ROUTE_LEGAL_BENCHMARK_RISK_QUEUE.md`
- `docs/LEGAL_RAG_AUTHORITY_CITATION_GATE.md`
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
