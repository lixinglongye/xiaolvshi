from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProductFeatureGap:
    id: str
    title: str
    module: str
    current_state: str
    target_capability: str
    user_segments: tuple[str, ...]
    impact: int
    urgency: int
    effort: int
    confidence: int
    dependencies: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    next_actions: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["user_segments"] = list(self.user_segments)
        data["dependencies"] = list(self.dependencies)
        data["evidence_paths"] = list(self.evidence_paths)
        data["next_actions"] = list(self.next_actions)
        data["priority_score"] = priority_score(
            self.impact,
            self.urgency,
            self.effort,
            self.confidence,
        )
        data["priority_band"] = priority_band(data["priority_score"])
        data["completion_state"] = "gap"
        return data


@dataclass(frozen=True)
class DeliveryPhase:
    id: str
    title: str
    objective: str
    gap_ids: tuple[str, ...]
    exit_criteria: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["gap_ids"] = list(self.gap_ids)
        data["exit_criteria"] = list(self.exit_criteria)
        return data


class ProductFeatureGapRadarService:
    """Expose the unfinished product surface as deterministic roadmap data."""

    def build_radar(self) -> dict[str, Any]:
        feature_gaps = sorted(
            (gap.to_api() for gap in self._feature_gaps()),
            key=lambda item: (-item["priority_score"], item["id"]),
        )
        high_priority = [gap for gap in feature_gaps if gap["priority_band"] in {"critical", "high"}]
        modules = sorted({gap["module"] for gap in feature_gaps})

        return {
            "status": "incomplete",
            "summary": {
                "feature_gap_count": len(feature_gaps),
                "high_priority_count": len(high_priority),
                "module_count": len(modules),
                "top_gap_ids": [gap["id"] for gap in feature_gaps[:5]],
                "modules": modules,
                "ready_for_public_feature_claim": False,
                "completion_policy": (
                    "Treat this radar as a product gap register until each high-priority gap has shipped evidence.",
                    "Do not claim full legal workflow coverage while any listed module remains in gap state.",
                ),
            },
            "feature_gaps": feature_gaps,
            "delivery_phases": [phase.to_api() for phase in self._delivery_phases()],
            "validation_commands": [
                "python -m pytest tests/test_product_feature_gap_radar.py -q",
                "rg -n \"(s[k]-[A-Za-z0-9]{20,}|APP_AI_KEY=s[k]-)\" app/backend/services/product_feature_gap_radar.py docs/PRODUCT_FEATURE_GAP_RADAR.md",
            ],
            "privacy_note": (
                "This privacy-safe radar is product planning metadata only. It must not include user documents, "
                "credentials, raw feedback text, API keys, account passwords, or personally identifying legal "
                "matter content."
            ),
        }

    def _feature_gaps(self) -> tuple[ProductFeatureGap, ...]:
        return (
            ProductFeatureGap(
                id="case-workbench",
                title="Case workbench",
                module="case_management",
                current_state="Case primitives exist, but the end-to-end workspace for matter timeline, tasks, parties, facts, and risk state is not complete.",
                target_capability="A lawyer-grade case workspace that ties facts, parties, tasks, documents, risks, and review decisions together.",
                user_segments=("lawyer", "legal_ops"),
                impact=10,
                urgency=10,
                effort=7,
                confidence=9,
                dependencies=("evidence-management", "document-generation", "feedback-loop"),
                evidence_paths=(
                    "app/backend/services/cases.py",
                    "app/backend/services/case_tasks.py",
                    "app/backend/services/case_facts.py",
                    "app/backend/services/case_task_notification_policy.py",
                    "app/backend/services/case_timeline_deadline_risk.py",
                    "app/backend/services/deadline_validation_policy.py",
                    "app/backend/services/matter_intake_readiness_policy.py",
                    "app/backend/tests/test_case_task_notification_policy.py",
                    "app/backend/tests/test_case_timeline_deadline_risk.py",
                    "app/backend/tests/test_deadline_validation_policy.py",
                    "app/backend/tests/test_matter_intake_readiness_policy.py",
                    "docs/CASE_TASK_NOTIFICATION_POLICY.md",
                    "docs/CASE_TIMELINE_DEADLINE_RISK.md",
                    "docs/DEADLINE_VALIDATION_POLICY.md",
                    "docs/MATTER_INTAKE_READINESS_POLICY.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Define the canonical case dashboard payload.",
                    "Wire matter intake readiness and deadline validation into the case dashboard payload.",
                    "Wire timeline deadline-risk flags into the case dashboard payload.",
                    "Wire task notification and escalation policy into case task status changes.",
                ),
            ),
            ProductFeatureGap(
                id="document-generation",
                title="Legal document generation",
                module="document_generation",
                current_state="Generated document storage exists, but template governance, clause variables, review status, and export readiness are incomplete.",
                target_capability="Generate pleadings, notices, settlement drafts, and review memos with template provenance and lawyer review checkpoints.",
                user_segments=("lawyer", "individual", "legal_ops"),
                impact=10,
                urgency=9,
                effort=8,
                confidence=8,
                dependencies=("case-workbench", "legal-knowledge-rag", "safety-compliance"),
                evidence_paths=(
                    "app/backend/services/generated_documents.py",
                    "app/backend/services/documents.py",
                    "app/backend/services/legal_document_export_readiness.py",
                    "app/backend/services/legal_document_template_matrix.py",
                    "app/backend/services/lawyer_review_workflow_policy.py",
                    "app/backend/services/client_delivery_transparency_policy.py",
                    "app/backend/tests/test_legal_document_export_readiness.py",
                    "app/backend/tests/test_legal_document_template_matrix.py",
                    "app/backend/tests/test_lawyer_review_workflow_policy.py",
                    "app/backend/tests/test_client_delivery_transparency_policy.py",
                    "docs/LEGAL_DOCUMENT_EXPORT_READINESS.md",
                    "docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md",
                    "docs/LAWYER_REVIEW_WORKFLOW_POLICY.md",
                    "docs/CLIENT_DELIVERY_TRANSPARENCY_POLICY.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Wire the document template matrix into concrete generation and export flows.",
                    "Wire export-readiness gates into DOCX/PDF export actions.",
                    "Wire client delivery transparency gates into final package release actions.",
                    "Gate exports on source support and missing-fact checks.",
                ),
            ),
            ProductFeatureGap(
                id="contract-review",
                title="Contract review workflow",
                module="contract_review",
                current_state="Deep review and report quality checks exist, but contract-specific clause extraction, fallback language, and negotiation workflow are incomplete.",
                target_capability="Clause-level review with risk grading, proposed edits, negotiation notes, and source-backed explanations.",
                user_segments=("lawyer", "legal_ops", "individual"),
                impact=9,
                urgency=9,
                effort=7,
                confidence=8,
                dependencies=("ocr-import", "legal-knowledge-rag", "model-cost-ops"),
                evidence_paths=(
                    "app/backend/services/deep_review.py",
                    "app/backend/services/report_quality_gate.py",
                    "app/backend/services/legal_document_benchmark_fixtures.py",
                    "app/backend/services/small_legal_document_corpus_expansion.py",
                    "app/backend/tests/test_legal_document_benchmark_fixtures.py",
                    "app/backend/tests/test_small_legal_document_corpus_expansion.py",
                    "docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md",
                    "docs/SMALL_LEGAL_DOCUMENT_CORPUS_EXPANSION.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Split contract review into clause extraction, risk scoring, and replacement drafting stages.",
                    "Add contract-specific quality checks for missing clauses and unsupported recommendations.",
                    "Use the expanded small legal corpus to cover common commercial and civil scenarios.",
                ),
            ),
            ProductFeatureGap(
                id="evidence-management",
                title="Evidence management",
                module="evidence",
                current_state="Evidence services exist, but exhibit organization, chain-of-custody notes, source dedupe, and case linking need a fuller workflow.",
                target_capability="Manage uploads, exhibits, source excerpts, relevance, authenticity notes, and case-level evidence bundles.",
                user_segments=("lawyer", "legal_ops"),
                impact=9,
                urgency=8,
                effort=6,
                confidence=8,
                dependencies=("case-workbench", "ocr-import", "safety-compliance"),
                evidence_paths=(
                    "app/backend/services/evidences.py",
                    "app/backend/services/evidence_audit.py",
                    "app/backend/services/case_materials.py",
                    "app/backend/services/evidence_exhibit_package_policy.py",
                    "app/backend/tests/test_evidence_exhibit_package_policy.py",
                    "docs/EVIDENCE_EXHIBIT_PACKAGE_POLICY.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Wire the evidence exhibit package policy into evidence catalog export.",
                    "Add duplicate and missing-source checks to evidence bundles.",
                    "Expose relevance and authenticity flags in backend payloads.",
                ),
            ),
            ProductFeatureGap(
                id="ocr-import",
                title="OCR and import pipeline",
                module="document_intake",
                current_state="Extraction quality checks exist, but scanned-file OCR routing, import retry state, and structured import mapping need more coverage.",
                target_capability="Robust import for PDFs, images, Word files, and structured forms with visible extraction confidence and retry handling.",
                user_segments=("lawyer", "legal_ops", "individual"),
                impact=9,
                urgency=8,
                effort=6,
                confidence=8,
                dependencies=("safety-compliance", "model-cost-ops"),
                evidence_paths=(
                    "app/backend/services/document_extraction.py",
                    "app/backend/services/extraction_quality.py",
                    "app/backend/services/document_preflight.py",
                    "app/backend/services/ocr_import_readiness_policy.py",
                    "app/backend/tests/test_ocr_import_readiness_policy.py",
                    "docs/OCR_IMPORT_READINESS_POLICY.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Wire the OCR import readiness policy into upload preflight and retry flows.",
                    "Track import parser, page count, low-text pages, and retry eligibility.",
                    "Create small scanned-document fixtures for local testing.",
                ),
            ),
            ProductFeatureGap(
                id="permissions-team",
                title="Permissions and team workspace",
                module="collaboration",
                current_state="Authentication and entitlements exist, but matter roles, team permissions, audit-friendly sharing, and reviewer assignment are incomplete.",
                target_capability="Team workspace with owner, lawyer, reviewer, assistant, and client roles scoped to cases and documents.",
                user_segments=("lawyer", "legal_ops", "team_admin"),
                impact=8,
                urgency=8,
                effort=8,
                confidence=7,
                dependencies=("case-workbench", "billing-entitlements", "safety-compliance"),
                evidence_paths=(
                    "app/backend/services/auth.py",
                    "app/backend/services/entitlements.py",
                    "app/backend/services/audit_logs.py",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Define case-scoped roles and permission matrix.",
                    "Add reviewer assignment and access audit payloads.",
                    "Keep role changes visible in audit logs.",
                ),
            ),
            ProductFeatureGap(
                id="billing-entitlements",
                title="Billing and entitlement control",
                module="billing",
                current_state="Entitlement checks exist, but product packaging, usage metering, invoice states, and model-cost-aware limits are incomplete.",
                target_capability="Plans, quotas, invoices, review credits, and model-cost controls that protect low-cost usage.",
                user_segments=("individual", "legal_ops", "team_admin"),
                impact=8,
                urgency=7,
                effort=7,
                confidence=7,
                dependencies=("model-cost-ops", "permissions-team"),
                evidence_paths=(
                    "app/backend/services/entitlements.py",
                    "app/backend/services/model_budget.py",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Define plan limits for uploads, reviews, generated documents, and premium model escalation.",
                    "Add deterministic over-limit reasons to entitlement responses.",
                    "Track usage without storing document content.",
                ),
            ),
            ProductFeatureGap(
                id="feedback-loop",
                title="Feedback loop",
                module="feedback",
                current_state="Feedback triage and roadmap alignment exist, but in-product feedback capture, closure state, and repeated issue tracking need implementation.",
                target_capability="Close the loop from user report to triage, roadmap gap, release gate, fix evidence, and customer-visible resolution.",
                user_segments=("maintainer", "support_ops", "lawyer"),
                impact=8,
                urgency=8,
                effort=5,
                confidence=8,
                dependencies=("case-workbench", "model-cost-ops"),
                evidence_paths=(
                    "app/backend/services/feedback_tickets.py",
                    "app/backend/services/feedback_triage.py",
                    "app/backend/services/feedback_roadmap_alignment.py",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Add feedback states from intake to resolved.",
                    "Require every high-risk ticket to link to a roadmap gap or release gate.",
                    "Create aggregate counts that do not expose raw legal matter text.",
                ),
            ),
            ProductFeatureGap(
                id="model-cost-ops",
                title="Model cost operations",
                module="model_ops",
                current_state="Model routing, budgets, and compatibility checks exist, but cost observability, result archives, and cheap-first guardrails still need product hardening.",
                target_capability="Cheap-first legal AI operations with route telemetry, budget limits, fallback policy, and benchmark-backed model choices.",
                user_segments=("maintainer", "legal_ops", "team_admin"),
                impact=9,
                urgency=9,
                effort=5,
                confidence=8,
                dependencies=("contract-review", "legal-knowledge-rag", "billing-entitlements"),
                evidence_paths=(
                    "app/backend/services/model_budget.py",
                    "app/backend/services/model_runtime_router.py",
                    "app/backend/services/model_route_telemetry.py",
                    "app/backend/services/model_default_recommendation_snapshot.py",
                    "app/backend/services/gemini_newapi_cheap_first_policy.py",
                    "app/backend/services/model_price_refresh_monitor.py",
                    "app/backend/services/model_cost_regression_snapshots.py",
                    "app/backend/services/route_telemetry_persistence_plan.py",
                    "app/backend/tests/test_model_default_recommendation_snapshot.py",
                    "app/backend/tests/test_gemini_newapi_cheap_first_policy.py",
                    "app/backend/tests/test_model_price_refresh_monitor.py",
                    "app/backend/tests/test_model_cost_regression_snapshots.py",
                    "app/backend/tests/test_route_telemetry_persistence_plan.py",
                    "docs/MODEL_DEFAULT_RECOMMENDATION_SNAPSHOT.md",
                    "docs/GEMINI_NEWAPI_CHEAP_FIRST_POLICY.md",
                    "docs/MODEL_PRICE_REFRESH_MONITOR.md",
                    "docs/MODEL_COST_REGRESSION_SNAPSHOTS.md",
                    "docs/ROUTE_TELEMETRY_PERSISTENCE_PLAN.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Archive small benchmark results by model, cost band, and legal task.",
                    "Wire price refresh and cost regression snapshots into recurring maintenance review.",
                    "Move route telemetry from schema validation to durable privacy-safe storage.",
                    "Keep Gemini-compatible cheap models first for eligible low-risk work.",
                ),
            ),
            ProductFeatureGap(
                id="legal-knowledge-rag",
                title="Legal knowledge base and RAG",
                module="legal_knowledge",
                current_state="Knowledge and RAG audits exist, but source ingestion, jurisdiction tagging, freshness tracking, and retrieval evaluation are incomplete.",
                target_capability="A jurisdiction-aware legal knowledge base with retrieval quality checks, citation freshness, and source provenance.",
                user_segments=("lawyer", "legal_ops", "maintainer"),
                impact=10,
                urgency=9,
                effort=9,
                confidence=8,
                dependencies=("safety-compliance", "model-cost-ops", "contract-review"),
                evidence_paths=(
                    "app/backend/services/legal_knowledge_audit.py",
                    "app/backend/services/legal_rag_evaluation.py",
                    "app/backend/services/legal_rag_failure_fixtures.py",
                    "app/backend/services/citation_audit.py",
                    "app/backend/tests/test_legal_rag_failure_fixtures.py",
                    "docs/LEGAL_RAG_FAILURE_FIXTURES.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Define source ingestion schema for laws, cases, templates, and internal notes.",
                    "Add jurisdiction and effective-date metadata to retrieval fixtures.",
                    "Use RAG failure fixtures to block stale, unsupported, and wrong-jurisdiction answers.",
                ),
            ),
            ProductFeatureGap(
                id="safety-compliance",
                title="Safety and compliance",
                module="safety",
                current_state="Privacy redaction, injection audit, and audit logs exist, but compliance review, data retention, export control, and admin policies need product-level ownership.",
                target_capability="Auditable privacy, security, retention, and legal-output safety controls suitable for sensitive legal workflows.",
                user_segments=("lawyer", "legal_ops", "team_admin", "maintainer"),
                impact=10,
                urgency=10,
                effort=8,
                confidence=8,
                dependencies=("permissions-team", "ocr-import", "legal-knowledge-rag"),
                evidence_paths=(
                    "app/backend/services/privacy_redaction.py",
                    "app/backend/services/instruction_injection_audit.py",
                    "app/backend/services/audit_logs.py",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                ),
                next_actions=(
                    "Define retention and deletion rules for uploaded legal materials.",
                    "Add compliance review checklist for public release claims.",
                    "Ensure secret scans and privacy checks are part of every release pass.",
                ),
            ),
        )

    def _delivery_phases(self) -> tuple[DeliveryPhase, ...]:
        return (
            DeliveryPhase(
                id="phase-1-core-legal-workflow",
                title="Core legal workflow",
                objective="Make the legal workbench useful before adding broad collaboration and monetization flows.",
                gap_ids=(
                    "case-workbench",
                    "document-generation",
                    "contract-review",
                    "evidence-management",
                    "ocr-import",
                ),
                exit_criteria=(
                    "A case can move from import to evidence review, contract review, and draft generation.",
                    "Every generated legal output has missing-fact, source-support, and review-required markers.",
                ),
            ),
            DeliveryPhase(
                id="phase-2-quality-and-ops",
                title="Quality, knowledge, and cost controls",
                objective="Harden legal accuracy and cheap-first model operations before higher-volume usage.",
                gap_ids=(
                    "legal-knowledge-rag",
                    "model-cost-ops",
                    "feedback-loop",
                    "safety-compliance",
                ),
                exit_criteria=(
                    "Legal knowledge retrieval has jurisdiction, freshness, and citation checks.",
                    "Small benchmark archives show cost, quality, and fallback behavior for target legal tasks.",
                    "Feedback can be tied back to roadmap gaps and release gates.",
                ),
            ),
            DeliveryPhase(
                id="phase-3-commercial-workspace",
                title="Team and commercial readiness",
                objective="Add team, permission, and billing controls once the core workflow is auditable.",
                gap_ids=("permissions-team", "billing-entitlements"),
                exit_criteria=(
                    "Case access is role-scoped and auditable.",
                    "Plan limits, usage metering, and model-cost limits are deterministic and privacy-safe.",
                ),
            ),
        )


def priority_score(impact: int, urgency: int, effort: int, confidence: int) -> int:
    raw = impact * 5 + urgency * 4 + confidence * 3 - effort * 2
    return max(0, min(100, raw))


def priority_band(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 75:
        return "high"
    if score >= 55:
        return "medium"
    return "low"
