# Product Feature Gap Radar

Recent update: contract-review evidence now includes a legal document benchmark coverage matrix and a legal document coverage claim policy. They improve reviewer visibility for small synthetic fixtures and block overbroad coverage wording, while keeping broader real-world document coverage, raw contract parsing, fallback language, and negotiation workflow marked as gaps.

The first coverage-matrix gap pass now adds synthetic fixtures for evidence catalogs, settlement agreements, and legal opinions. Product gap status remains incomplete because these fixtures are local regression evidence only, and the claim policy forbids treating them as public benchmark, real-client, or universal document coverage.

This document describes the deterministic product gap radar exposed by
`app/backend/services/product_feature_gap_radar.py`.

The radar is intentionally marked `incomplete`. It is a planning and release-risk
artifact, not a claim that the product already covers every legal workflow. It
keeps the unfinished product surface visible while backend, benchmark, and
maintenance work continues in parallel.

Recent shipped evidence now includes matter intake readiness, deterministic
deadline validation, client delivery transparency gates, small legal document
benchmark fixtures, small legal corpus expansion, RAG failure fixtures,
legal source freshness policy, case workbench payload contracts, document
delivery package manifests, document version diff checklist, case workbench
persistence planning, case workbench state repository persistence, case workbench
runtime binding and routes, typed runtime API clients, contract clause extraction
schema, role permission matrices, billing usage quotas, billing quota persistence
planning, billing quota migration planning, billing quota repository persistence,
billing entitlement quota binding, billing quota consumption route, feedback
lifecycle policy, legal source ingestion metadata, legal source durable index
planning, legal source index repository persistence, legal RAG index binding and
routes, Gemini/NewAPI cheap-first policy metadata, default model recommendation
snapshots, price refresh monitoring, cost regression snapshots, and route
telemetry persistence planning. Model-cost evidence now also includes a
privacy-safe route telemetry repository and operations summary for persisted
route failure, premium-model, over-budget, operator-review, unknown-model, and
downgrade review, plus a triage queue that turns those checks into maintainer
actions and a remediation plan that maps triage into reviewed cheap-first env
suggestions. The latest UI evidence adds runtime router discovery smoke, the
case workbench runtime state/event panel, metadata-only risk/evidence refresh
planning from runtime event deltas, the metadata-only legal RAG research panel,
and the global billing usage badge.
The current follow-up evidence also adds billing report preflight, privacy-safe
case edit runtime events, metadata-only Legal RAG context cache/copy controls,
and a best-effort document-generation quota consumption attempt. The newest
backend and full-stack slices add server-side generated_documents CRUD quota
guards, case evidence-catalog/civil-complaint quota guards, selected-source
Legal RAG request metadata in case AI and document records, deep-review
first-principles document-generation quota guards, metadata-level
selected-source citation validation, a metadata-only selected-source validation
maintenance route, a local-only billing payment reconciliation policy, task
runtime notification summaries, a deterministic laptop-safe legal document
benchmark suite, a LegalBench/LexGLUE/COLIEE research registry mapped to local
low-resource validation, and a maintenance UI section for that registry.
The latest product-research slice adds a metadata-only legal adoption research
bridge that maps LegalBench, FrugalGPT, RAGAS, CRAG, and professional AI
governance/adoption signals into existing user needs, product gaps,
cheap-first validation commands, release gates, survey intake questions, and a
maintenance UI review panel.
The latest maintenance batch adds deep-review selected-source binding, quota
delivery decisions, deterministic feedback issue clustering, metadata-only
evidence bundle integrity checks, privacy retention rules, release-claim
compliance checks, case export readiness checks, and admin audit policy
evidence.
The newest evidence-management slice adds a metadata-only evidence-catalog
export preflight to case evidence-catalog generation. It joins exhibit package
policy and bundle integrity checks while still allowing draft generation, but
frontend download/export buttons still need to consume the blocked/ready result.
That follow-up is now partially closed for markdown downloads: the case detail
page gates report, evidence-catalog, and generated-document downloads through
metadata-only case export readiness before calling the local download helper.
Final DOCX/PDF export and delivery package release actions still need the same
gate.
Model-cost evidence now also includes the scoped Gemini/NewAPI model selector
evidence contract for `GET`/`POST`
`/api/v1/maintenance/gemini-newapi-model-selector`. That contract is
metadata-only selection review for normalized model ids, task labels, cost
tiers, cheap-first candidate chains, warnings, and evidence paths. It does not
call NewAPI, store prompts or raw model output, or close the 24-hour maintenance
proof gap.
The companion selector replay contract for `GET`/`POST`
`/api/v1/maintenance/gemini-newapi-selector-replay` adds deterministic scenario
replay evidence for fast/classification/OCR cheap-first behavior,
review/document_generation balanced-after-precheck, large_pdf/final_review
premium exceptions, unknown Gemini-like catalog review, and high-frequency
explicit premium blocking or warning. It remains metadata-only selector
regression evidence and does not prove live NewAPI execution or 24-hour
completion.
`docs/ROUTE_TELEMETRY_OPS_SUMMARY.md` scopes the implemented
`GET /api/v1/maintenance/route-telemetry-ops-summary` endpoint as a
repository-backed operations review over sanitized daily aggregates. It is
release evidence for cheap-first drift and route health checks, but it must not
be described as storing prompts, legal text, raw payloads, raw model outputs,
credentials, emails, or production health proof when no route events exist.
`docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md` scopes the implemented
`GET /api/v1/maintenance/route-telemetry-triage` endpoint as a maintainer
action queue over those operations checks. It still cannot prove production
health when no route events exist, and it must not include raw route events or
model payloads.
`docs/ROUTE_TELEMETRY_REMEDIATION_PLAN.md` scopes the implemented
`GET /api/v1/maintenance/route-telemetry-remediation` endpoint as an
operator-reviewed plan over triage and default optimization metadata. It never
writes config or calls gateways.
These are reviewable product slices, not proof that the full case workbench,
delivery portal, live deadline engine, durable model telemetry store, payment
provider settlement/webhook verification, automatic deep-review report binding
for selected-source validation, raw contract extraction, or database-backed team
workspace is finished.

The frontend productization queue has moved from route exposure to deeper
workflow binding:

- Runtime event deltas should refresh live risk state and evidence graph views.
- Selected-source citation validation should bind into live deep-review persistence and export actions.
- Quota summaries should bind into reviewer-visible export, delivery, and account-plan decisions.
- Local payment reconciliation policy should connect to reviewed provider webhook signatures, invoice states, and plan-change workflows before any real settlement claim.
- Continuous 24-hour maintenance evidence now binds the 100+ update ledger,
  heartbeat records, git-history commit cadence, push/test validation, and
  low-resource legal fixture runs into one reviewer timeline, while still
  blocking support-application completion claims until real timestamped records
  prove the window.
  `docs/CONTINUOUS_SESSION_TIMELINE.md` scopes the implemented
  `GET`/`POST` `/api/v1/maintenance/continuous-session-timeline` endpoint as
  metadata-only and keeps the 24-hour proof separate from the satisfied 100+
  update count.
  `docs/GIT_HISTORY_EVIDENCE.md` scopes the implemented
  `GET /api/v1/maintenance/git-history-evidence` endpoint as commit-cadence
  evidence only: commit count, longest cadence window, and maximum
  adjacent-commit gap from Git metadata, without inferring tests, pushes,
  credential scans, or legal fixture runs.
  `docs/VALIDATION_EVENT_EVIDENCE.md` scopes the upcoming `GET`/`POST`
  `/api/v1/maintenance/validation-event-evidence` endpoint as the metadata-only
  source for those non-git validation rows. It accepts event metadata for
  input validation `test`, `credential_scan`, `push`,
  `review`/`release_review`, and `legal_fixture` events, but not raw stdout,
  raw stderr, logs, full legal
  text, raw model output, secrets, emails, or passwords. It can fill gaps that
  git cadence cannot prove, but it still cannot prove 24-hour completion alone.
  `docs/CONTINUOUS_SESSION_REVIEW_PACKET.md` scopes the upcoming `GET`/`POST`
  `/api/v1/maintenance/continuous-session-review-packet` endpoint as a
  metadata-only reviewer/support packet over the ledger, timeline, git cadence,
  and validation-event evidence. It should expose section statuses, hashes,
  `evidence_paths`, blockers, review questions, and the privacy boundary, while
  excluding raw logs/stdout/stderr, complete legal text, raw model output,
  credentials, and emails. It is a review index only and cannot by itself
  claim the 24-hour session is complete.
- `docs/CONTINUOUS_SESSION_RUN_MONITOR.md` scopes the implemented `GET`/`POST`
  `/api/v1/maintenance/continuous-session-run-monitor` endpoint as a
  metadata-only active-run monitor over ledger, timeline, and review-packet
  metadata. It tracks elapsed hours, current gaps, next checkpoints, missing
  required evidence, blockers, and next actions, but it does not prove 24h
  completion. Real timestamped events remain required, and the monitor must not
  store raw logs, legal text, model outputs, credentials, or emails.
- `docs/LEGAL_ADOPTION_RESEARCH_BRIDGE.md` scopes the implemented
  `GET /api/v1/maintenance/legal-review-benchmark/adoption-research-bridge`
  endpoint as metadata-only planning evidence. It cannot prove law-firm
  adoption, public benchmark scores, live NewAPI calls, survey results,
  productivity gains, or external ecosystem importance.

## Scope

The radar tracks product modules that are not fully implemented or need
significant hardening:

- Case workbench
- Legal document generation
- Contract review workflow
- Evidence management
- OCR and import pipeline
- Permissions and team workspace
- Billing and entitlement control
- Feedback loop
- Model cost operations
- Legal knowledge base and RAG
- Safety and compliance
- Continuous maintenance evidence

Each gap includes:

- Product module and user segment
- Current state and target capability
- Priority score and priority band
- Dependencies
- Evidence paths
- Next implementation actions

## API Shape

`ProductFeatureGapRadarService().build_radar()` returns an API-ready dictionary
with these top-level keys:

- `status`: always `incomplete` until the high-priority feature gaps have shipped
  evidence.
- `summary`: counts, modules, top gap IDs, and public-claim guardrails.
- `feature_gaps`: deterministic list sorted by priority score descending.
- `delivery_phases`: staged delivery plan for core workflow, quality and
  operations, then commercial workspace readiness.
- `validation_commands`: small local checks for this slice.
- `privacy_note`: reminder that the radar must not include user documents,
  credentials, raw feedback text, account passwords, or legal matter content.

## Delivery Phases

### Phase 1: Core Legal Workflow

Focus on the case workbench, document generation, contract review, evidence
management, and OCR/import flow. The exit condition is a useful case flow from
import to evidence review, contract review, and draft generation with source
support and missing-fact markers.

### Phase 2: Quality, Knowledge, and Cost Controls

Focus on legal knowledge/RAG, model cost operations, feedback loop, and safety
controls. The exit condition is measurable legal retrieval quality, cheap-first
model behavior, benchmark archives, and feedback tied to roadmap and release
evidence.

### Phase 3: Team and Commercial Readiness

Focus on permissions/team workspace and billing/entitlements. The exit condition
is role-scoped case access, auditable changes, deterministic plan limits, and
privacy-safe usage metering.

### Cross-Phase Evidence Gap: Continuous Session Validation

The 100+ update target is now reviewable through repository artifacts, the
backend continuous-session validator can evaluate explicit metadata, and the
maintenance page can show a compact reviewer-facing timeline. The product still
needs persisted real session records and a fuller interactive timeline, so the
validator should not be treated as a backend-only metric. It should continue to
show:

- the longest verified maintenance window,
- the longest git-derived cadence window and maximum adjacent-commit gap,
- timestamped commits, test runs, pushes, and review actions,
- metadata-only validation event evidence for input validation tests,
  credential scans, pushes, review/release-review actions, and legal fixture
  events,
- active-run monitor metadata for elapsed hours, current checkpoint gaps,
  required evidence readiness, blockers, and next actions,
- links back to shipped update evidence,
- laptop-safe legal fixture runs for small machines, and
- explicit blockers when the 24-hour window is not proven, and
- a metadata-only review packet with section statuses, hashes, evidence paths,
  blockers, review questions, and the active privacy boundary.

This gap is linked to legal-document benchmark work because a long maintenance
session should include lightweight, repeatable legal quality checks. The
acceptable default is a quick-suite or local-run-review record with synthetic
fixture IDs and coverage metadata, not a large public benchmark download.
The continuous-session timeline also joins release review evidence and
public-claim guardrails, but it must not persist secrets, account
data, emails, raw stdout, raw stderr, raw legal texts, copied benchmark
samples, raw prompts, gateway payloads, raw patches, or model original outputs.

## Validation

Run the focused test from `app/backend`:

```powershell
python -m pytest tests/test_product_feature_gap_radar.py -q
python -m pytest tests/test_legal_adoption_research_bridge.py -q
```

The model-cost and legal-quality evidence referenced by the radar also has
focused local checks:

```powershell
python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py tests/test_gemini_newapi_selector_replay.py tests/test_legal_fixture_run_report.py tests/test_model_cost_guardrails.py -q
python -m pytest tests/test_route_telemetry_repository.py tests/test_route_telemetry_persistence_plan.py tests/test_model_route_telemetry.py -q
python -m pytest tests/test_model_price_refresh_monitor.py tests/test_model_cost_regression_snapshots.py tests/test_route_telemetry_persistence_plan.py -q
python -m pytest tests/test_small_legal_document_corpus_expansion.py tests/test_legal_document_benchmark_suite.py tests/test_legal_rag_failure_fixtures.py tests/test_legal_source_ingestion_metadata.py tests/test_legal_source_freshness_policy.py tests/test_legal_source_durable_index_plan.py tests/test_legal_source_index_repository.py tests/test_legal_rag_index_binding.py tests/test_legal_rag_router.py tests/test_legal_rag_request_metadata.py tests/test_contract_clause_extraction_schema.py -q
python -m pytest tests/test_case_workbench_payload.py tests/test_case_workbench_persistence_plan.py tests/test_case_workbench_state_repository.py tests/test_case_workbench_runtime_binding.py tests/test_case_workbench_runtime_router.py tests/test_case_task_notification_policy.py tests/test_case_evidence_catalog_export_preflight.py tests/test_case_export_readiness.py tests/test_document_delivery_package_manifest.py tests/test_document_version_diff_checklist.py tests/test_case_role_permission_matrix.py tests/test_billing_usage_quota_policy.py tests/test_billing_quota_persistence_plan.py tests/test_billing_quota_migration_plan.py tests/test_billing_quota_repository.py tests/test_billing_entitlement_quota_binding.py tests/test_billing_usage_router.py tests/test_generated_documents_quota.py tests/test_billing_payment_reconciliation.py tests/test_feedback_lifecycle_policy.py -q
npm run ui:regression
npm run typecheck
```

Additional focused checks:

```powershell
python -m pytest tests/test_runtime_router_discovery.py -q
npm run typecheck
```

Run the focused secret check from the repository root:

```powershell
rg -n "(s[k]-[A-Za-z0-9]{20,}|APP_AI_KEY=s[k]-)" app/backend/services/product_feature_gap_radar.py docs/PRODUCT_FEATURE_GAP_RADAR.md
```
