# Product Feature Gap Radar

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
persistence planning, case workbench state repository persistence, contract clause
extraction schema, role permission
matrices, billing usage quotas, billing quota persistence planning, billing
quota migration planning, billing quota repository persistence, feedback
lifecycle policy, legal source ingestion metadata, legal source durable index
planning, legal source index repository persistence, Gemini/NewAPI cheap-first
policy metadata, default model recommendation snapshots, price refresh
monitoring, cost regression snapshots, and route telemetry persistence planning.
These are reviewable product slices, not proof that the full case workbench,
delivery portal, live deadline engine, durable model telemetry store, payment
integration, live RAG retrieval binding, raw contract extraction, or
database-backed team workspace is finished.

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

## Validation

Run the focused test from `app/backend`:

```powershell
python -m pytest tests/test_product_feature_gap_radar.py -q
```

The model-cost and legal-quality evidence referenced by the radar also has
focused local checks:

```powershell
python -m pytest tests/test_model_price_refresh_monitor.py tests/test_model_cost_regression_snapshots.py tests/test_route_telemetry_persistence_plan.py -q
python -m pytest tests/test_small_legal_document_corpus_expansion.py tests/test_legal_rag_failure_fixtures.py tests/test_legal_source_ingestion_metadata.py tests/test_legal_source_freshness_policy.py tests/test_legal_source_durable_index_plan.py tests/test_legal_source_index_repository.py tests/test_contract_clause_extraction_schema.py -q
python -m pytest tests/test_case_workbench_payload.py tests/test_case_workbench_persistence_plan.py tests/test_case_workbench_state_repository.py tests/test_document_delivery_package_manifest.py tests/test_document_version_diff_checklist.py tests/test_case_role_permission_matrix.py tests/test_billing_usage_quota_policy.py tests/test_billing_quota_persistence_plan.py tests/test_billing_quota_migration_plan.py tests/test_billing_quota_repository.py tests/test_feedback_lifecycle_policy.py -q
```

Run the focused secret check from the repository root:

```powershell
rg -n "(s[k]-[A-Za-z0-9]{20,}|APP_AI_KEY=s[k]-)" app/backend/services/product_feature_gap_radar.py docs/PRODUCT_FEATURE_GAP_RADAR.md
```
