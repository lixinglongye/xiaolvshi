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
- `app/backend/services/case_evidence_graph.py`
- `app/backend/services/case_intake_completeness.py`
- `app/backend/services/case_team_access_policy.py`
- `app/backend/services/client_delivery_risk_checklist.py`
- `app/backend/services/legal_document_template_matrix.py`
- `app/backend/services/legal_external_research_digest.py`
- `app/backend/services/product_feature_gap_radar.py`
- `app/backend/tests/test_billing_entitlement_gap.py`
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/tests/test_case_intake_completeness.py`
- `app/backend/tests/test_case_team_access_policy.py`
- `app/backend/tests/test_client_delivery_risk_checklist.py`
- `app/backend/tests/test_legal_document_template_matrix.py`
- `app/backend/tests/test_legal_external_research_digest.py`
- `app/backend/tests/test_product_feature_gap_radar.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CASE_INTAKE_COMPLETENESS.md`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
- `docs/CLIENT_DELIVERY_RISK_CHECKLIST.md`
- `docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md`
- `docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/OSS_MAINTENANCE_EVIDENCE.md`
- `docs/USER_RESEARCH_AND_MAINTENANCE.md`
- `docs/RELEASE_READINESS.md`
