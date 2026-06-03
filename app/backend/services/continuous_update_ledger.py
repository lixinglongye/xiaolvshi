from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Literal


TARGET_CONTINUOUS_HOURS = 24
TARGET_MEDIUM_LARGE_UPDATE_COUNT = 100

UpdateSize = Literal["medium", "large"]
UpdateStatus = Literal["shipped", "planned"]


@dataclass(frozen=True)
class LedgerEntry:
    id: str
    title: str
    category: str
    size: UpdateSize
    status: UpdateStatus
    impact: str
    evidence_paths: tuple[str, ...]
    release_gate_links: tuple[str, ...]
    user_need_ids: tuple[str, ...]
    commit_hint: str | None = None

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_paths"] = list(self.evidence_paths)
        data["release_gate_links"] = list(self.release_gate_links)
        data["user_need_ids"] = list(self.user_need_ids)
        return data


class ContinuousUpdateLedgerService:
    """Track long-running maintenance progress without claiming completion early."""

    def build_ledger(self) -> dict[str, Any]:
        entries = self._entries()
        completed = [entry for entry in entries if entry.status == "shipped"]
        planned = [entry for entry in entries if entry.status == "planned"]
        category_counts = Counter(entry.category for entry in completed)
        size_counts = Counter(entry.size for entry in completed)
        completed_count = len(completed)
        remaining_count = max(0, TARGET_MEDIUM_LARGE_UPDATE_COUNT - completed_count)

        return {
            "status": "in_progress",
            "goal": {
                "target_continuous_hours": TARGET_CONTINUOUS_HOURS,
                "target_medium_large_update_count": TARGET_MEDIUM_LARGE_UPDATE_COUNT,
                "completion_policy": [
                    "Do not mark the goal complete until both the 24-hour evidence window and 100+ medium/large shipped updates are reviewable.",
                    "Count only repository-backed updates with code, tests, docs, or reviewer-facing evidence.",
                    "Keep laptop-safe quick suites separate from heavier benchmark or public corpus work.",
                ],
            },
            "summary": {
                "completed_medium_large_update_count": completed_count,
                "remaining_medium_large_update_count": remaining_count,
                "planned_update_count": len(planned),
                "large_update_count": size_counts.get("large", 0),
                "medium_update_count": size_counts.get("medium", 0),
                "category_counts": dict(sorted(category_counts.items())),
                "continuous_hours_verified": 0,
                "continuous_hours_remaining": TARGET_CONTINUOUS_HOURS,
                "completion_ready": False,
            },
            "completed_updates": [entry.to_api() for entry in completed],
            "next_update_queue": [entry.to_api() for entry in planned[:12]],
            "twenty_four_hour_evidence_requirements": [
                "Record timestamped commits or CI runs across the full 24-hour window.",
                "Keep each update reviewable through a code path, test, doc, endpoint, or UI surface.",
                "Do not treat local-only benchmark attempts as shipped updates unless results are normalized and stored safely.",
            ],
            "hundred_update_evidence_requirements": [
                "Group updates by model operations, legal benchmark coverage, frontend visibility, maintenance evidence, and safety controls.",
                "Keep small fixture tests serial and cheap-first so low-resource machines can validate the work.",
                "Use release-readiness and OSS-maintenance evidence endpoints as the reviewer-facing index.",
            ],
            "low_resource_test_policy": {
                "default_fixture_limit": 3,
                "max_parallel_requests": 1,
                "network_access": "disabled_by_default",
                "model_call_policy": "manual_serial_only",
                "recommended_endpoint": "/api/v1/maintenance/legal-review-benchmark/quick-suite",
            },
            "release_guardrails": [
                "The ledger is optional release evidence; it must not unblock a release by itself.",
                "Secret values, account credentials, raw client documents, and raw gateway responses must stay out of git.",
                "Public benchmark sources stay metadata-only until license, attribution, and privacy review pass.",
            ],
            "validation_commands": [
                "python -m pytest tests/test_continuous_update_ledger.py -q",
                "python -m pytest tests/test_legal_fixture_quick_suite.py tests/test_legal_review_benchmark.py -q",
            ],
        }

    def _entries(self) -> list[LedgerEntry]:
        return [
            LedgerEntry(
                id="model-gateway-probe-evaluation",
                title="Sanitized model gateway probe evaluation",
                category="model_ops",
                size="large",
                status="shipped",
                impact="Reviews OpenAI-compatible gateway model and chat probes without storing keys or raw secrets.",
                evidence_paths=(
                    "app/backend/services/model_gateway_probe_evaluation.py",
                    "app/backend/tests/test_model_gateway_probe_evaluation.py",
                    "docs/MODEL_GATEWAY_PROBE_EVALUATION.md",
                ),
                release_gate_links=("model-gateway-probe-evaluation", "model-ops-readiness"),
                user_need_ids=("low-cost-routing", "safe-ai-ops"),
            ),
            LedgerEntry(
                id="model-gateway-probe-ui",
                title="Model gateway probe evidence in operations UI",
                category="frontend_ui",
                size="medium",
                status="shipped",
                impact="Surfaces probe recommendations and sanitized defaults in the model operations page.",
                evidence_paths=(
                    "app/frontend/src/lib/modelOpsApi.ts",
                    "app/frontend/src/pages/ModelOpsPage.tsx",
                ),
                release_gate_links=("frontend-typecheck", "frontend-build"),
                user_need_ids=("low-cost-routing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="model-gateway-health-plan",
                title="Gateway health planning before live requests",
                category="model_ops",
                size="large",
                status="shipped",
                impact="Documents cheap JSON probes, base URL checks, and manual health gates before real model calls.",
                evidence_paths=(
                    "app/backend/services/model_gateway_health_plan.py",
                    "app/backend/tests/test_model_gateway_health_plan.py",
                    "docs/MODEL_GATEWAY_HEALTH_PLAN.md",
                ),
                release_gate_links=("model-gateway-health-plan", "model-ops-readiness"),
                user_need_ids=("safe-ai-ops", "low-cost-routing"),
            ),
            LedgerEntry(
                id="legal-research-backlog",
                title="Research-backed legal AI backlog",
                category="user_research",
                size="large",
                status="shipped",
                impact="Maps LegalBench, FrugalGPT, RAGAS, CRAG, and CUAD signals into concrete engineering tasks.",
                evidence_paths=(
                    "app/backend/services/legal_research_backlog.py",
                    "app/backend/tests/test_legal_research_backlog.py",
                    "docs/LEGAL_RESEARCH_BACKLOG.md",
                ),
                release_gate_links=("legal-review-benchmark", "oss-maintenance-evidence"),
                user_need_ids=("grounded-legal-output", "low-cost-routing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="legal-external-research-digest",
                title="External legal AI research digest",
                category="user_research",
                size="large",
                status="shipped",
                impact="Maps LegalBench, CUAD, RAGAS, CRAG, and FrugalGPT signals into local legal benchmark, RAG, and cheap-first routing work.",
                evidence_paths=(
                    "app/backend/services/legal_external_research_digest.py",
                    "app/backend/tests/test_legal_external_research_digest.py",
                    "docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md",
                ),
                release_gate_links=("legal-review-benchmark", "oss-maintenance-evidence"),
                user_need_ids=("grounded-legal-output", "low-cost-routing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="legal-research-backlog-ui",
                title="Legal research backlog reviewer panel",
                category="frontend_ui",
                size="medium",
                status="shipped",
                impact="Shows research backlog priorities and evidence paths on the maintenance page.",
                evidence_paths=(
                    "app/frontend/src/lib/maintenanceApi.ts",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                ),
                release_gate_links=("frontend-typecheck", "frontend-build"),
                user_need_ids=("reviewer-visibility", "grounded-legal-output"),
            ),
            LedgerEntry(
                id="legal-public-benchmark-sampler",
                title="Resource-capped public benchmark sampler",
                category="benchmark",
                size="large",
                status="shipped",
                impact="Keeps public benchmark work as metadata until license and attribution review are complete.",
                evidence_paths=(
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "app/backend/tests/test_legal_public_benchmark_sampler.py",
                    "docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md",
                ),
                release_gate_links=("legal-review-benchmark",),
                user_need_ids=("grounded-legal-output", "low-resource-testing"),
            ),
            LedgerEntry(
                id="legal-fixture-quick-suite",
                title="Laptop-safe legal fixture quick suite",
                category="benchmark",
                size="large",
                status="shipped",
                impact="Selects a tiny serial fixture subset for low-resource local testing.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_quick_suite.py",
                    "app/backend/tests/test_legal_fixture_quick_suite.py",
                    "docs/LEGAL_FIXTURE_QUICK_SUITE.md",
                ),
                release_gate_links=("legal-review-benchmark",),
                user_need_ids=("low-resource-testing", "low-cost-routing"),
            ),
            LedgerEntry(
                id="legal-fixture-model-matrix",
                title="Fixture-level Gemini and NewAPI model matrix",
                category="model_ops",
                size="medium",
                status="shipped",
                impact="Assigns cheap-first, fallback, and premium-exception candidates per legal fixture.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_model_matrix.py",
                    "app/backend/tests/test_legal_fixture_model_matrix.py",
                    "docs/LEGAL_FIXTURE_MODEL_MATRIX.md",
                ),
                release_gate_links=("legal-review-benchmark", "model-fallback-chains"),
                user_need_ids=("low-cost-routing", "low-resource-testing"),
            ),
            LedgerEntry(
                id="legal-fixture-prompt-pack",
                title="Cheap-first legal fixture prompt pack",
                category="benchmark",
                size="medium",
                status="shipped",
                impact="Builds small legal document prompts with observation targets for manual gateway checks.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_prompt_pack.py",
                    "app/backend/tests/test_legal_fixture_prompt_pack.py",
                    "docs/LEGAL_FIXTURE_PROMPT_PACK.md",
                ),
                release_gate_links=("legal-review-benchmark",),
                user_need_ids=("grounded-legal-output", "low-cost-routing"),
            ),
            LedgerEntry(
                id="legal-fixture-gateway-manifest",
                title="Safe legal fixture gateway manifests",
                category="safety",
                size="medium",
                status="shipped",
                impact="Generates OpenAI-compatible request manifests with placeholders instead of real credentials.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_gateway_manifest.py",
                    "app/backend/tests/test_legal_fixture_gateway_manifest.py",
                    "docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md",
                ),
                release_gate_links=("secret-scan", "legal-review-benchmark"),
                user_need_ids=("safe-ai-ops", "low-resource-testing"),
            ),
            LedgerEntry(
                id="legal-fixture-run-plan",
                title="Serial cheap-first fixture run plan",
                category="benchmark",
                size="large",
                status="shipped",
                impact="Converts fixture manifests into one-at-a-time local batches with conditional escalation.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_run_plan.py",
                    "app/backend/tests/test_legal_fixture_run_plan.py",
                    "docs/LEGAL_FIXTURE_RUN_PLAN.md",
                ),
                release_gate_links=("legal-review-benchmark", "model-escalation-policy"),
                user_need_ids=("low-resource-testing", "low-cost-routing"),
            ),
            LedgerEntry(
                id="legal-fixture-local-run-package",
                title="One-at-a-time local fixture run package",
                category="benchmark",
                size="large",
                status="shipped",
                impact="Bundles request JSON, PowerShell and curl templates, observation slots, and report scaffolding.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_local_run_package.py",
                    "app/backend/tests/test_legal_fixture_local_run_package.py",
                    "docs/LEGAL_FIXTURE_LOCAL_RUN_PACKAGE.md",
                ),
                release_gate_links=("legal-review-benchmark",),
                user_need_ids=("low-resource-testing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="legal-fixture-response-normalizer",
                title="Local fixture response normalizer",
                category="safety",
                size="medium",
                status="shipped",
                impact="Redacts secret-like values and normalizes local gateway outputs into fixture observations.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_response_normalizer.py",
                    "app/backend/tests/test_legal_fixture_response_normalizer.py",
                    "docs/LEGAL_FIXTURE_RESPONSE_NORMALIZER.md",
                ),
                release_gate_links=("secret-scan", "legal-review-benchmark"),
                user_need_ids=("safe-ai-ops", "low-resource-testing"),
            ),
            LedgerEntry(
                id="legal-fixture-local-run-review",
                title="One-step local fixture run review",
                category="benchmark",
                size="large",
                status="shipped",
                impact="Normalizes local responses, scores smoke coverage, builds run reports, and returns evidence bundles.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_local_run_review.py",
                    "app/backend/tests/test_legal_fixture_local_run_review.py",
                    "docs/LEGAL_FIXTURE_LOCAL_RUN_REVIEW.md",
                ),
                release_gate_links=("legal-review-benchmark",),
                user_need_ids=("low-resource-testing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="legal-fixture-run-report",
                title="Cheap-first fixture run report",
                category="release_evidence",
                size="medium",
                status="shipped",
                impact="Turns fixture observations into release decisions and fixture-scoped escalation actions.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_run_report.py",
                    "app/backend/tests/test_legal_fixture_run_report.py",
                    "docs/LEGAL_FIXTURE_RUN_REPORT.md",
                ),
                release_gate_links=("legal-review-benchmark",),
                user_need_ids=("reviewer-visibility", "low-cost-routing"),
            ),
            LedgerEntry(
                id="legal-fixture-evidence-bundle",
                title="Legal fixture evidence bundle",
                category="release_evidence",
                size="medium",
                status="shipped",
                impact="Archives component status, validation commands, release-safe claims, and cheap-first run evidence.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_evidence_bundle.py",
                    "app/backend/tests/test_legal_fixture_evidence_bundle.py",
                    "docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md",
                ),
                release_gate_links=("legal-review-benchmark", "oss-maintenance-evidence"),
                user_need_ids=("reviewer-visibility", "grounded-legal-output"),
            ),
            LedgerEntry(
                id="user-needs-radar",
                title="User needs radar",
                category="user_research",
                size="medium",
                status="shipped",
                impact="Ranks target legal-review needs and links them to release gates and evidence paths.",
                evidence_paths=(
                    "app/backend/services/user_needs_radar.py",
                    "app/backend/tests/test_user_needs_radar.py",
                    "docs/USER_NEEDS_RADAR.md",
                ),
                release_gate_links=("user-needs-radar", "oss-maintenance-evidence"),
                user_need_ids=("reviewer-visibility", "grounded-legal-output", "safe-ai-ops"),
            ),
            LedgerEntry(
                id="feedback-roadmap-alignment",
                title="Feedback-to-roadmap alignment",
                category="maintenance",
                size="medium",
                status="shipped",
                impact="Maps support feedback categories to user-need IDs and release gates.",
                evidence_paths=(
                    "app/backend/services/feedback_roadmap_alignment.py",
                    "app/backend/tests/test_feedback_roadmap_alignment.py",
                    "docs/FEEDBACK_ROADMAP_ALIGNMENT.md",
                ),
                release_gate_links=("feedback-roadmap-alignment", "oss-maintenance-evidence"),
                user_need_ids=("reviewer-visibility", "safe-ai-ops"),
            ),
            LedgerEntry(
                id="product-feature-gap-radar",
                title="Product-wide feature gap radar",
                category="product_planning",
                size="large",
                status="shipped",
                impact="Makes incomplete product modules explicit across case workbench, document generation, contract review, evidence, OCR, billing, team, feedback, model ops, legal knowledge, and safety.",
                evidence_paths=(
                    "app/backend/services/product_feature_gap_radar.py",
                    "app/backend/tests/test_product_feature_gap_radar.py",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                release_gate_links=("product-feature-gap-radar", "oss-maintenance-evidence"),
                user_need_ids=("reviewer-visibility", "product-readiness"),
            ),
            LedgerEntry(
                id="case-evidence-graph-contract",
                title="Case evidence graph contract",
                category="product_planning",
                size="large",
                status="shipped",
                impact="Defines the fact-evidence-citation-risk graph contract and blocking gap flags before a full case workbench graph UI is built.",
                evidence_paths=(
                    "app/backend/services/case_evidence_graph.py",
                    "app/backend/tests/test_case_evidence_graph.py",
                    "docs/CASE_EVIDENCE_GRAPH.md",
                ),
                release_gate_links=("case-evidence-graph", "legal-rag-evaluation"),
                user_need_ids=("grounded-legal-output", "case-workbench"),
            ),
            LedgerEntry(
                id="case-intake-completeness",
                title="Case intake completeness checklist",
                category="product_planning",
                size="medium",
                status="shipped",
                impact="Blocks document generation when parties, venue, deadlines, claims, evidence, or risk disclosure fields are incomplete.",
                evidence_paths=(
                    "app/backend/services/case_intake_completeness.py",
                    "app/backend/tests/test_case_intake_completeness.py",
                    "docs/CASE_INTAKE_COMPLETENESS.md",
                ),
                release_gate_links=("case-intake-completeness", "case-evidence-graph"),
                user_need_ids=("case-workbench", "document-generation", "grounded-legal-output"),
            ),
            LedgerEntry(
                id="case-team-access-policy",
                title="Case team access policy",
                category="safety",
                size="medium",
                status="shipped",
                impact="Defines least-privilege owner, lawyer, paralegal, reviewer, and client roles with audit-required sensitive operations.",
                evidence_paths=(
                    "app/backend/services/case_team_access_policy.py",
                    "app/backend/tests/test_case_team_access_policy.py",
                    "docs/CASE_TEAM_ACCESS_POLICY.md",
                ),
                release_gate_links=("case-team-access-policy", "product-feature-gap-radar"),
                user_need_ids=("case-workbench", "reviewer-visibility", "safe-ai-ops"),
            ),
            LedgerEntry(
                id="client-delivery-risk-checklist",
                title="Client delivery risk checklist",
                category="safety",
                size="medium",
                status="shipped",
                impact="Adds delivery blockers for citation evidence, lawyer review, scope assumptions, AI limitation notices, and client-readable risk language.",
                evidence_paths=(
                    "app/backend/services/client_delivery_risk_checklist.py",
                    "app/backend/tests/test_client_delivery_risk_checklist.py",
                    "docs/CLIENT_DELIVERY_RISK_CHECKLIST.md",
                ),
                release_gate_links=("client-delivery-risk-checklist", "case-intake-completeness"),
                user_need_ids=("grounded-legal-output", "reviewer-visibility", "safe-ai-ops"),
            ),
            LedgerEntry(
                id="legal-document-template-matrix",
                title="Legal document template matrix",
                category="product_planning",
                size="large",
                status="shipped",
                impact="Defines required fields, formatting requirements, blockers, lawyer-review gates, and export formats for six legal document types.",
                evidence_paths=(
                    "app/backend/services/legal_document_template_matrix.py",
                    "app/backend/tests/test_legal_document_template_matrix.py",
                    "docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md",
                ),
                release_gate_links=("legal-document-template-matrix", "product-feature-gap-radar"),
                user_need_ids=("document-generation", "case-workbench", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="legal-document-export-readiness",
                title="Legal document export readiness",
                category="product_planning",
                size="medium",
                status="shipped",
                impact="Blocks final export until template fields, blocker clearance, lawyer review, source support, redaction, version lock, and format support pass.",
                evidence_paths=(
                    "app/backend/services/legal_document_export_readiness.py",
                    "app/backend/tests/test_legal_document_export_readiness.py",
                    "docs/LEGAL_DOCUMENT_EXPORT_READINESS.md",
                ),
                release_gate_links=("legal-document-export-readiness", "legal-document-template-matrix"),
                user_need_ids=("document-generation", "grounded-legal-output", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="billing-entitlement-gap-evidence",
                title="Billing entitlement gap evidence",
                category="product_planning",
                size="medium",
                status="shipped",
                impact="Adds deterministic payment activation and usage-plan guard evidence without integrating a live payment gateway.",
                evidence_paths=(
                    "app/backend/services/billing_entitlement_gap.py",
                    "app/backend/tests/test_billing_entitlement_gap.py",
                    "docs/BILLING_ENTITLEMENT_GAP.md",
                ),
                release_gate_links=("billing-entitlement-gap", "product-feature-gap-radar"),
                user_need_ids=("billing-entitlements", "product-readiness"),
            ),
            LedgerEntry(
                id="continuous-update-ledger-ui",
                title="Reviewer-facing continuous update ledger panel",
                category="frontend_ui",
                size="medium",
                status="shipped",
                impact="Expose the ledger on the maintenance dashboard with completed count, remaining count, and low-resource test policy.",
                evidence_paths=(
                    "app/frontend/src/lib/maintenanceApi.ts",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                ),
                release_gate_links=("frontend-typecheck", "frontend-build"),
                user_need_ids=("reviewer-visibility",),
            ),
            LedgerEntry(
                id="cheap-first-result-archive",
                title="Cheap-first fixture result archive",
                category="release_evidence",
                size="large",
                status="shipped",
                impact="Store normalized fixture run summaries without raw client text or raw model output.",
                evidence_paths=(
                    "app/backend/services/legal_fixture_result_archive.py",
                    "app/backend/tests/test_legal_fixture_result_archive.py",
                    "docs/LEGAL_FIXTURE_RESULT_ARCHIVE.md",
                ),
                release_gate_links=("legal-review-benchmark", "secret-scan"),
                user_need_ids=("low-resource-testing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="gemini-price-refresh-monitor",
                title="Gemini and gateway price refresh monitor",
                category="model_ops",
                size="medium",
                status="planned",
                impact="Flag model catalog drift when cheap-first assumptions no longer match gateway price metadata.",
                evidence_paths=("app/backend/services/model_cost_forecast.py", "docs/MODEL_COST_FORECAST.md"),
                release_gate_links=("model-cost-forecast", "model-cost-guardrails"),
                user_need_ids=("low-cost-routing",),
            ),
            LedgerEntry(
                id="small-legal-document-corpus-expansion",
                title="Small legal fixture corpus expansion",
                category="benchmark",
                size="large",
                status="planned",
                impact="Add more synthetic labor, lease, service, and purchase contract fixtures before full public benchmark runs.",
                evidence_paths=("docs/LEGAL_BENCHMARK_FIXTURES.md",),
                release_gate_links=("legal-review-benchmark",),
                user_need_ids=("grounded-legal-output", "low-resource-testing"),
            ),
            LedgerEntry(
                id="legal-rag-failure-fixtures",
                title="Legal RAG failure fixtures",
                category="benchmark",
                size="large",
                status="planned",
                impact="Add small grounding failure cases that test missing citations, weak authorities, and unsupported legal claims.",
                evidence_paths=("docs/LEGAL_RAG_EVALUATION.md", "docs/LEGAL_GROUNDING_QUICK_AUDIT.md"),
                release_gate_links=("legal-rag-evaluation",),
                user_need_ids=("grounded-legal-output",),
            ),
            LedgerEntry(
                id="maintenance-dashboard-filtering",
                title="Maintenance dashboard filtering",
                category="frontend_ui",
                size="medium",
                status="planned",
                impact="Add filters for category, release gate, and low-resource status in the maintenance page.",
                evidence_paths=("app/frontend/src/pages/MaintenanceEvidencePage.tsx",),
                release_gate_links=("frontend-typecheck", "frontend-build"),
                user_need_ids=("reviewer-visibility",),
            ),
            LedgerEntry(
                id="model-cost-regression-snapshots",
                title="Model cost regression snapshots",
                category="model_ops",
                size="large",
                status="planned",
                impact="Persist sanitized route-cost scenarios so cheap-first defaults can be compared across updates.",
                evidence_paths=("docs/MODEL_COST_GUARDRAILS.md", "docs/MODEL_ROUTING_REPLAY.md"),
                release_gate_links=("model-cost-guardrails", "model-routing-replay"),
                user_need_ids=("low-cost-routing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="twenty-four-hour-heartbeat-evidence",
                title="24-hour heartbeat evidence export",
                category="maintenance",
                size="medium",
                status="planned",
                impact="Export timestamped commit, test, and validation evidence for the full continuous maintenance window.",
                evidence_paths=("docs/CONTINUOUS_UPDATE_LEDGER.md",),
                release_gate_links=("oss-maintenance-evidence",),
                user_need_ids=("reviewer-visibility",),
            ),
            LedgerEntry(
                id="frontend-local-run-review-form",
                title="Frontend local run review form",
                category="frontend_ui",
                size="medium",
                status="planned",
                impact="Let maintainers paste already-redacted local fixture responses into the one-step review endpoint.",
                evidence_paths=("app/frontend/src/pages/MaintenanceEvidencePage.tsx",),
                release_gate_links=("frontend-typecheck", "legal-review-benchmark"),
                user_need_ids=("low-resource-testing", "reviewer-visibility"),
            ),
            LedgerEntry(
                id="route-telemetry-persistence-plan",
                title="Route telemetry persistence plan",
                category="model_ops",
                size="large",
                status="planned",
                impact="Move model route telemetry from process-local aggregation to a sanitized persistence design.",
                evidence_paths=("docs/MODEL_ROUTE_TELEMETRY.md",),
                release_gate_links=("model-route-telemetry", "secret-scan"),
                user_need_ids=("low-cost-routing", "safe-ai-ops"),
            ),
        ]
