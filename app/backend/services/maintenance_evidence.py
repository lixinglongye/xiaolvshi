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
                description="OpenAI-compatible gateway routing prefers cheaper Gemini models for routine tasks and reserves premium models for complex PDF or review work.",
                responsibility="Model catalog maintenance, budget policy review, and gateway compatibility updates.",
                cadence="Review when gateway model names, pricing, or task defaults change.",
                evidence_paths=(
                    "app/backend/services/model_catalog.py",
                    "app/backend/services/model_budget.py",
                    "app/backend/tests/test_model_catalog.py",
                    "docs/AI_MODEL_STRATEGY.md",
                ),
                weight=15,
            ),
            MaintenanceSignal(
                id="deep-review-quality-gates",
                category="quality",
                title="Deep-review quality gate",
                description="Deterministic gates verify that a report has enough structure, grounding, pending-fact handling, and disclaimers before review.",
                responsibility="Quality gate tuning, regression tests, and release criteria maintenance.",
                cadence="Review whenever report schema, legal source handling, or delivery policy changes.",
                evidence_paths=(
                    "app/backend/services/report_quality_gate.py",
                    "app/backend/services/legal_review_benchmark.py",
                    "app/backend/tests/test_report_quality_gate.py",
                    "app/backend/tests/test_legal_review_benchmark.py",
                    "docs/DEEP_REVIEW_QUALITY_GATES.md",
                    "docs/LEGAL_REVIEW_BENCHMARK.md",
                ),
                weight=15,
            ),
            MaintenanceSignal(
                id="citation-and-evidence-audits",
                category="review_ops",
                title="Citation and evidence audits",
                description="Citation and evidence services flag weak legal authorities, missing reviewable citations, missing evidence plans, and blocking pending facts.",
                responsibility="Legal-source review support, issue triage, and evidence completeness checks.",
                cadence="Review when legal knowledge sources, report sections, or risk-item fields change.",
                evidence_paths=(
                    "app/backend/services/citation_audit.py",
                    "app/backend/services/evidence_audit.py",
                    "app/backend/tests/test_citation_audit.py",
                    "app/backend/tests/test_evidence_audit.py",
                    "docs/DEEP_REVIEW_CITATION_AUDIT.md",
                    "docs/DEEP_REVIEW_EVIDENCE_AUDIT.md",
                ),
                weight=20,
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
                    "app/backend/services/user_needs_radar.py",
                    "docs/USER_NEEDS_RADAR.md",
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
