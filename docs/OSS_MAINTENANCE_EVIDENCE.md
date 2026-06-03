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

- Model operations: model catalog, configuration audit, default optimization, gateway compatibility, gateway health planning, sanitized gateway probe evaluation, Gemini lifecycle policy, model-ops readiness, budget policy, task inference, runtime routing, reasoning effort policy, request parameter policy, request cost bounds, cache policy, route telemetry, route guardrails, callsite audit, fallback chains, routing replay, usage-safe telemetry.
- Quality control: deep-review quality gates, legal document template coverage, legal document export readiness, legal-review benchmark cases, external legal-AI research digests, research-backed legal AI backlog planning, resource-capped public benchmark samplers, quick laptop-safe legal fixture suites, fixture-level Gemini/NewAPI model matrices, cheap-first legal fixture prompt packs, safe gateway request manifests, laptop-safe fixture run plans, one-at-a-time local run packages, response normalizers, one-step local run reviews, archive-safe fixture result summaries, cheap-first fixture run reports, release evidence bundles, lightweight synthetic legal document fixtures, and fixture-driven prompt/schema improvement planning.
- Document intake: OCR import readiness states, retry policy, scanned-page detection, and manual-review routing.
- Review operations: citation, evidence, legal grounding quick audits, the case evidence graph contract, the case intake completeness checklist, case timeline deadline risk, and the client delivery risk checklist.
- Security and collaboration: least-privilege case team roles, client-only scopes, sensitive-operation approvals, and access audit requirements.
- Release management: risk scoring and unified release decision.
- Product visibility: frontend report page, report mapping, and API types.
- Maintenance planning: user research, maintenance notes, billing entitlement gap evidence, product feature gap radar, and the continuous update ledger.

## Related files

- `app/backend/services/maintenance_evidence.py`
- `app/backend/services/continuous_update_ledger.py`
- `app/backend/services/billing_entitlement_gap.py`
- `app/backend/services/case_evidence_graph.py`
- `app/backend/services/case_intake_completeness.py`
- `app/backend/services/case_timeline_deadline_risk.py`
- `app/backend/services/case_team_access_policy.py`
- `app/backend/services/client_delivery_risk_checklist.py`
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
- `app/backend/tests/test_case_evidence_graph.py`
- `app/backend/tests/test_case_intake_completeness.py`
- `app/backend/tests/test_case_timeline_deadline_risk.py`
- `app/backend/tests/test_case_team_access_policy.py`
- `app/backend/tests/test_client_delivery_risk_checklist.py`
- `app/backend/tests/test_ocr_import_readiness_policy.py`
- `app/backend/tests/test_product_feature_gap_radar.py`
- `app/backend/tests/test_legal_external_research_digest.py`
- `app/backend/tests/test_legal_document_export_readiness.py`
- `app/backend/tests/test_legal_document_template_matrix.py`
- `app/backend/tests/test_legal_research_backlog.py`
- `app/frontend/src/lib/maintenanceApi.ts`
- `app/frontend/src/pages/MaintenanceEvidencePage.tsx`
- `docs/CONTINUOUS_UPDATE_LEDGER.md`
- `docs/BILLING_ENTITLEMENT_GAP.md`
- `docs/CASE_EVIDENCE_GRAPH.md`
- `docs/CASE_INTAKE_COMPLETENESS.md`
- `docs/CASE_TIMELINE_DEADLINE_RISK.md`
- `docs/CASE_TEAM_ACCESS_POLICY.md`
- `docs/CLIENT_DELIVERY_RISK_CHECKLIST.md`
- `docs/OCR_IMPORT_READINESS_POLICY.md`
- `docs/PRODUCT_FEATURE_GAP_RADAR.md`
- `docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md`
- `docs/LEGAL_DOCUMENT_EXPORT_READINESS.md`
- `docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md`
- `docs/USER_RESEARCH_AND_MAINTENANCE.md`
- `docs/LEGAL_RESEARCH_BACKLOG.md`
