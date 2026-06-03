from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


Language = Literal["en", "zh"]


REPOSITORY_URL = "https://github.com/lixinglongye/xiaolvshi"


@dataclass(frozen=True)
class MaintenanceSignal:
    id: str
    category: str
    title: str
    description: str
    responsibility: str
    cadence: str
    evidence_paths: tuple[str, ...]
    weight: int

    def to_api(self) -> dict:
        data = asdict(self)
        data["evidence_paths"] = list(self.evidence_paths)
        return data


class MaintenanceEvidenceService:
    """Builds application-safe OSS maintenance evidence for this project."""

    def build_profile(self, language: Language = "en") -> dict:
        language = self._normalize_language(language)
        signals = self._signals()

        return {
            "project": {
                "name": "xiaolvshi",
                "display_name": "律审雷达",
                "repository_url": REPOSITORY_URL,
                "domain": "Legal document review, case material organization, and litigation preparation",
            },
            "maintainer_role": "primary_project_maintainer",
            "evidence_score": self._evidence_score(signals),
            "active_maintenance_summary": self._summary(language),
            "form_answer": self.build_form_answer(language),
            "signals": [signal.to_api() for signal in signals],
            "responsibilities": self._responsibilities(signals),
            "release_management": {
                "current_stage": "active_pre_release_development",
                "release_readiness_controls": [
                    "Deep-review quality gate",
                    "Citation audit",
                    "Evidence audit",
                    "Risk scoring",
                    "Unified release decision",
                    "Model configuration audit",
                    "Model default optimization",
                    "Model gateway compatibility",
                    "Model operations readiness",
                "Model route guardrails",
                "Gemini reasoning effort policy",
                "Generation request parameter policy",
                "Model request cost bounds",
                "Model cache policy",
                "Continuous update ledger",
                "Case team access policy",
                "Client delivery risk checklist",
                "Legal document template matrix",
                "Legal document export readiness",
            ],
                "client_delivery_policy": "Reports are not marked client-deliverable until release_decision allows delivery.",
            },
            "application_guardrails": [
                "Only claim maintenance work that is visible in this repository.",
                "Do not claim external ecosystem adoption without public evidence.",
                "Do not claim third-party PR or issue volume unless GitHub records show it.",
                "Human maintainer must confirm ownership and final form attestations before submission.",
            ],
        }

    def build_form_answer(self, language: Language = "en") -> str:
        language = self._normalize_language(language)
        if language == "zh":
            return (
                "我是 xiaolvshi 项目的维护者，仓库地址为 "
                f"{REPOSITORY_URL}。该项目正在持续维护，目前包含 FastAPI 后端、React/Vite "
                "前端、本地法律知识库、文件处理、深度审查流水线、自动化测试和维护文档。"
                "近期维护内容包括 Gemini/NewAPI 模型路由与预算策略、确定性风险评分、报告质量门禁、"
                "引用审计、证据审计，以及法律深度审查报告的统一交付决策流程。"
                "我持续负责发布就绪检查、质量控制、测试覆盖、文档更新和问题分级处理，使该项目作为"
                "可维护的开源法律审查工具持续演进，而不是一次性演示项目。"
            )

        return (
            "I am the maintainer of the xiaolvshi project: "
            f"{REPOSITORY_URL}. The repository is under active development and includes a FastAPI "
            "backend, React/Vite frontend, local legal knowledge base, file processing, deep-review "
            "pipeline, automated tests, and maintenance documentation. Recent maintenance work includes "
            "Gemini/NewAPI model routing and budget policy, deterministic risk scoring, report quality "
            "gates, citation auditing, evidence auditing, and a unified release decision workflow for "
            "legal deep-review reports. I actively handle release readiness, quality checks, test coverage, "
            "documentation updates, and issue-style triage logic so the project can be maintained as a usable "
            "open-source legal review tool rather than a one-time demo."
        )

    def _signals(self) -> list[MaintenanceSignal]:
        return [
            MaintenanceSignal(
                id="model-routing-cost-control",
                category="model_ops",
                title="Cost-aware Gemini/NewAPI routing",
                description="OpenAI-compatible gateway routing prefers cheaper Gemini models for routine tasks and keeps defaults pinned to stable lifecycle-safe models with safe gateway health planning and sanitized probe evaluation.",
                responsibility="Model catalog maintenance, budget policy review, gateway compatibility updates, gateway health-plan review, sanitized probe evaluation, and Gemini lifecycle policy review.",
                cadence="Review when gateway model names, pricing, or task defaults change.",
                evidence_paths=(
                    "app/backend/services/model_catalog.py",
                    "app/backend/services/model_budget.py",
                    "app/backend/services/model_capability_matrix.py",
                    "app/backend/services/model_configuration_audit.py",
                    "app/backend/services/model_default_optimization.py",
                    "app/backend/services/model_gateway_compatibility.py",
                    "app/backend/services/model_gateway_health_plan.py",
                    "app/backend/services/model_gateway_probe_evaluation.py",
                    "app/backend/services/model_lifecycle_policy.py",
                    "app/backend/services/model_ops_readiness.py",
                    "app/backend/services/model_runtime_router.py",
                    "app/backend/services/model_reasoning_policy.py",
                    "app/backend/services/model_request_policy.py",
                    "app/backend/services/model_request_cost_bounds.py",
                    "app/backend/services/model_cache_policy.py",
                    "app/backend/services/model_route_telemetry.py",
                    "app/backend/services/model_route_guardrails.py",
                    "app/backend/services/model_task_inference.py",
                    "app/backend/services/model_callsite_audit.py",
                    "app/backend/services/model_escalation_policy.py",
                    "app/backend/services/model_cost_forecast.py",
                    "app/backend/services/model_cost_guardrails.py",
                    "app/backend/services/model_routing_replay.py",
                    "app/backend/services/model_fallback_chains.py",
                    "app/backend/tests/test_model_catalog.py",
                    "app/backend/tests/test_model_capability_matrix.py",
                    "app/backend/tests/test_model_configuration_audit.py",
                    "app/backend/tests/test_model_default_optimization.py",
                    "app/backend/tests/test_model_gateway_compatibility.py",
                    "app/backend/tests/test_model_gateway_health_plan.py",
                    "app/backend/tests/test_model_gateway_probe_evaluation.py",
                    "app/backend/tests/test_model_lifecycle_policy.py",
                    "app/backend/tests/test_model_ops_readiness.py",
                    "app/backend/tests/test_model_runtime_router.py",
                    "app/backend/tests/test_model_reasoning_policy.py",
                    "app/backend/tests/test_model_request_policy.py",
                    "app/backend/tests/test_model_request_cost_bounds.py",
                    "app/backend/tests/test_model_cache_policy.py",
                    "app/backend/tests/test_model_route_telemetry.py",
                    "app/backend/tests/test_model_route_guardrails.py",
                    "app/backend/tests/test_aihub_runtime_routing.py",
                    "app/backend/tests/test_model_task_inference.py",
                    "app/backend/tests/test_model_callsite_audit.py",
                    "app/backend/tests/test_model_escalation_policy.py",
                    "app/backend/tests/test_model_cost_forecast.py",
                    "app/backend/tests/test_model_cost_guardrails.py",
                    "app/backend/tests/test_model_routing_replay.py",
                    "app/backend/tests/test_model_fallback_chains.py",
                    "docs/AI_MODEL_STRATEGY.md",
                    "docs/MODEL_CONFIGURATION_AUDIT.md",
                    "docs/MODEL_DEFAULT_OPTIMIZATION.md",
                    "docs/MODEL_GATEWAY_COMPATIBILITY.md",
                    "docs/MODEL_GATEWAY_HEALTH_PLAN.md",
                    "docs/MODEL_GATEWAY_PROBE_EVALUATION.md",
                    "docs/MODEL_LIFECYCLE_POLICY.md",
                    "docs/MODEL_OPS_READINESS.md",
                    "docs/MODEL_RUNTIME_ROUTER.md",
                    "docs/MODEL_REASONING_POLICY.md",
                    "docs/MODEL_REQUEST_POLICY.md",
                    "docs/MODEL_REQUEST_COST_BOUNDS.md",
                    "docs/MODEL_CACHE_POLICY.md",
                    "docs/MODEL_ROUTE_TELEMETRY.md",
                    "docs/MODEL_ROUTE_GUARDRAILS.md",
                    "docs/MODEL_TASK_INFERENCE.md",
                    "docs/MODEL_CALLSITE_AUDIT.md",
                    "docs/MODEL_ESCALATION_POLICY.md",
                    "docs/MODEL_COST_FORECAST.md",
                    "docs/MODEL_COST_GUARDRAILS.md",
                    "docs/MODEL_ROUTING_REPLAY.md",
                    "docs/MODEL_FALLBACK_CHAINS.md",
                ),
                weight=15,
            ),
            MaintenanceSignal(
                id="deep-review-quality-gates",
                category="quality",
                title="Deep-review quality gate",
                description="Deterministic gates, legal document template coverage, export-readiness checks, research-backed legal AI backlog planning, public benchmark sampling plans, quick laptop-safe fixture suites, fixture-level Gemini/NewAPI model matrices, cheap-first fixture prompt packs, safe gateway manifests, laptop-safe fixture run plans, one-at-a-time local run packages, response normalizers, one-step local run reviews, cheap-first run reports, evidence bundles, archive-safe result summaries, fixture smoke tests, and fixture improvement plans verify report structure, grounding, pending-fact handling, disclaimers, and small legal document coverage before review.",
                responsibility="Quality gate tuning, legal template matrix review, export-readiness review, research backlog review, public benchmark sampler review, quick-suite review, legal fixture model matrix review, prompt coverage, safe gateway manifest upkeep, fixture run-plan, local-package, response-normalizer, local-run-review, result-archive, run-report, and evidence-bundle maintenance, smoke coverage, prompt/schema improvement planning, regression tests, and release criteria maintenance.",
                cadence="Review whenever report schema, legal source handling, or delivery policy changes.",
                evidence_paths=(
                    "app/backend/services/report_quality_gate.py",
                    "app/backend/services/legal_review_benchmark.py",
                    "app/backend/services/legal_external_research_digest.py",
                    "app/backend/services/legal_document_export_readiness.py",
                    "app/backend/services/legal_document_template_matrix.py",
                    "app/backend/services/legal_research_backlog.py",
                    "app/frontend/src/lib/maintenanceApi.ts",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "app/backend/services/legal_fixture_quick_suite.py",
                    "app/backend/services/legal_fixture_model_matrix.py",
                    "app/backend/services/legal_fixture_prompt_pack.py",
                    "app/backend/services/legal_fixture_gateway_manifest.py",
                    "app/backend/services/legal_fixture_run_plan.py",
                    "app/backend/services/legal_fixture_local_run_package.py",
                    "app/backend/services/legal_fixture_response_normalizer.py",
                    "app/backend/services/legal_fixture_local_run_review.py",
                    "app/backend/services/legal_fixture_result_archive.py",
                    "app/backend/services/legal_fixture_run_report.py",
                    "app/backend/services/legal_fixture_evidence_bundle.py",
                    "app/backend/services/legal_fixture_improvement.py",
                    "app/backend/tests/test_report_quality_gate.py",
                    "app/backend/tests/test_legal_review_benchmark.py",
                    "app/backend/tests/test_legal_external_research_digest.py",
                    "app/backend/tests/test_legal_document_export_readiness.py",
                    "app/backend/tests/test_legal_document_template_matrix.py",
                    "app/backend/tests/test_legal_research_backlog.py",
                    "app/backend/tests/test_legal_public_benchmark_sampler.py",
                    "app/backend/tests/test_legal_fixture_quick_suite.py",
                    "app/backend/tests/test_legal_fixture_model_matrix.py",
                    "app/backend/tests/test_legal_fixture_prompt_pack.py",
                    "app/backend/tests/test_legal_fixture_gateway_manifest.py",
                    "app/backend/tests/test_legal_fixture_run_plan.py",
                    "app/backend/tests/test_legal_fixture_local_run_package.py",
                    "app/backend/tests/test_legal_fixture_response_normalizer.py",
                    "app/backend/tests/test_legal_fixture_local_run_review.py",
                    "app/backend/tests/test_legal_fixture_result_archive.py",
                    "app/backend/tests/test_legal_fixture_run_report.py",
                    "app/backend/tests/test_legal_fixture_evidence_bundle.py",
                    "app/backend/tests/test_legal_fixture_improvement.py",
                    "docs/DEEP_REVIEW_QUALITY_GATES.md",
                    "docs/LEGAL_REVIEW_BENCHMARK.md",
                    "docs/LEGAL_EXTERNAL_RESEARCH_DIGEST.md",
                    "docs/LEGAL_DOCUMENT_EXPORT_READINESS.md",
                    "docs/LEGAL_DOCUMENT_TEMPLATE_MATRIX.md",
                    "docs/LEGAL_RESEARCH_BACKLOG.md",
                    "docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md",
                    "docs/LEGAL_FIXTURE_QUICK_SUITE.md",
                    "docs/LEGAL_BENCHMARK_FIXTURES.md",
                    "docs/LEGAL_FIXTURE_MODEL_MATRIX.md",
                    "docs/LEGAL_FIXTURE_PROMPT_PACK.md",
                    "docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md",
                    "docs/LEGAL_FIXTURE_RUN_PLAN.md",
                    "docs/LEGAL_FIXTURE_LOCAL_RUN_PACKAGE.md",
                    "docs/LEGAL_FIXTURE_RESPONSE_NORMALIZER.md",
                    "docs/LEGAL_FIXTURE_LOCAL_RUN_REVIEW.md",
                    "docs/LEGAL_FIXTURE_RESULT_ARCHIVE.md",
                    "docs/LEGAL_FIXTURE_RUN_REPORT.md",
                    "docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md",
                    "docs/LEGAL_FIXTURE_IMPROVEMENT.md",
                ),
                weight=15,
            ),
            MaintenanceSignal(
                id="citation-and-evidence-audits",
                category="review_ops",
                title="Citation and evidence audits",
                description="Citation, evidence, grounding, case intake, delivery-risk, and graph services flag weak legal authorities, missing reviewable citations, missing evidence plans, incomplete intake fields, missing client disclosures, unsupported legal claims, and blocking pending facts.",
                responsibility="Legal-source review support, issue triage, grounding quick-audit review, intake completeness review, client-delivery checklist review, and evidence completeness checks.",
                cadence="Review when legal knowledge sources, report sections, or risk-item fields change.",
                evidence_paths=(
                    "app/backend/services/citation_audit.py",
                    "app/backend/services/evidence_audit.py",
                    "app/backend/services/legal_grounding_quick_audit.py",
                    "app/backend/services/case_evidence_graph.py",
                    "app/backend/services/case_intake_completeness.py",
                    "app/backend/services/client_delivery_risk_checklist.py",
                    "app/backend/tests/test_citation_audit.py",
                    "app/backend/tests/test_evidence_audit.py",
                    "app/backend/tests/test_legal_grounding_quick_audit.py",
                    "app/backend/tests/test_case_evidence_graph.py",
                    "app/backend/tests/test_case_intake_completeness.py",
                    "app/backend/tests/test_client_delivery_risk_checklist.py",
                    "docs/DEEP_REVIEW_CITATION_AUDIT.md",
                    "docs/DEEP_REVIEW_EVIDENCE_AUDIT.md",
                    "docs/LEGAL_GROUNDING_QUICK_AUDIT.md",
                    "docs/CASE_EVIDENCE_GRAPH.md",
                    "docs/CASE_INTAKE_COMPLETENESS.md",
                    "docs/CLIENT_DELIVERY_RISK_CHECKLIST.md",
                ),
                weight=20,
            ),
            MaintenanceSignal(
                id="case-team-access-policy",
                category="security",
                title="Case team access policy",
                description="The project defines least-privilege case collaboration roles, client-only scopes, sensitive-operation approval rules, and audit event requirements before richer team workflows are exposed.",
                responsibility="Role matrix review, sensitive-operation audit coverage, client access minimization, and firm-retention policy alignment.",
                cadence="Review whenever team roles, sharing actions, export behavior, or case membership storage changes.",
                evidence_paths=(
                    "app/backend/services/case_team_access_policy.py",
                    "app/backend/tests/test_case_team_access_policy.py",
                    "docs/CASE_TEAM_ACCESS_POLICY.md",
                ),
                weight=10,
            ),
            MaintenanceSignal(
                id="risk-scoring-release-decision",
                category="release_management",
                title="Risk scoring and release decision",
                description="The project computes deterministic risk scores and combines quality, citation, evidence, and risk signals into client delivery decisions.",
                responsibility="Release readiness review, lawyer-review routing, and delivery-blocker management.",
                cadence="Review before public releases and after high-risk workflow changes.",
                evidence_paths=(
                    "app/backend/services/risk_scoring.py",
                    "app/backend/services/release_decision.py",
                    "app/backend/tests/test_risk_scoring.py",
                    "app/backend/tests/test_release_decision.py",
                    "docs/DEEP_REVIEW_RISK_SCORING.md",
                    "docs/DEEP_REVIEW_RELEASE_DECISION.md",
                ),
                weight=20,
            ),
            MaintenanceSignal(
                id="frontend-review-visibility",
                category="product",
                title="Frontend report visibility",
                description="The report UI exposes quality, citation, evidence, risk, delivery, and lawyer-review status to reviewers.",
                responsibility="Reviewer workflow usability, report mapping, and frontend type maintenance.",
                cadence="Review with every report-schema change and user-facing delivery workflow update.",
                evidence_paths=(
                    "app/frontend/src/lib/deepReviewApi.ts",
                    "app/frontend/src/lib/reportMapper.ts",
                    "app/frontend/src/pages/DeepReportPage.tsx",
                    "app/frontend/src/lib/mockData.ts",
                ),
                weight=15,
            ),
            MaintenanceSignal(
                id="user-research-maintenance-notes",
                category="maintenance",
                title="User research and maintenance notes",
                description="The repository documents target users, workflow priorities, maintenance metrics, and application-safe claims.",
                responsibility="User workflow research, maintenance roadmap updates, and support-application accuracy.",
                cadence="Review when user segments, product scope, or public support applications change.",
                evidence_paths=(
                    "docs/USER_RESEARCH_AND_MAINTENANCE.md",
                    "app/backend/services/continuous_update_ledger.py",
                    "app/backend/services/feedback_roadmap_alignment.py",
                    "app/backend/services/billing_entitlement_gap.py",
                    "app/backend/services/product_feature_gap_radar.py",
                    "app/backend/services/user_needs_radar.py",
                    "app/backend/tests/test_billing_entitlement_gap.py",
                    "app/backend/tests/test_continuous_update_ledger.py",
                    "app/backend/tests/test_feedback_roadmap_alignment.py",
                    "app/backend/tests/test_product_feature_gap_radar.py",
                    "app/frontend/src/lib/maintenanceApi.ts",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                    "docs/CONTINUOUS_UPDATE_LEDGER.md",
                    "docs/BILLING_ENTITLEMENT_GAP.md",
                    "docs/PRODUCT_FEATURE_GAP_RADAR.md",
                    "docs/USER_NEEDS_RADAR.md",
                    "docs/FEEDBACK_ROADMAP_ALIGNMENT.md",
                ),
                weight=10,
            ),
        ]

    def _summary(self, language: Language) -> str:
        if language == "zh":
            return "项目有可审核的代码、测试、文档、质量控制、交付门禁和维护职责说明。"
        return "The project has reviewable code, tests, documentation, quality controls, release gates, and maintainer responsibilities."

    def _responsibilities(self, signals: list[MaintenanceSignal]) -> list[str]:
        seen: set[str] = set()
        responsibilities: list[str] = []
        for signal in signals:
            if signal.responsibility not in seen:
                seen.add(signal.responsibility)
                responsibilities.append(signal.responsibility)
        return responsibilities

    def _evidence_score(self, signals: list[MaintenanceSignal]) -> int:
        if not signals:
            return 0
        return min(100, sum(max(0, signal.weight) for signal in signals))

    def _normalize_language(self, language: str) -> Language:
        return "zh" if language == "zh" else "en"
