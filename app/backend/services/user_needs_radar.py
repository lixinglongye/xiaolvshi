from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ResearchSource:
    id: str
    title: str
    url: str
    signal: str

    def to_api(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class UserNeed:
    id: str
    title: str
    category: str
    user_segments: tuple[str, ...]
    pain_point: str
    product_response: str
    impact: int
    effort: int
    confidence: int
    source_ids: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    release_gate_links: tuple[str, ...]
    next_actions: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["user_segments"] = list(self.user_segments)
        data["source_ids"] = list(self.source_ids)
        data["evidence_paths"] = list(self.evidence_paths)
        data["release_gate_links"] = list(self.release_gate_links)
        data["next_actions"] = list(self.next_actions)
        data["priority_score"] = priority_score(self.impact, self.effort, self.confidence)
        data["priority_band"] = priority_band(data["priority_score"])
        return data


class UserNeedsRadarService:
    """Convert legal-AI research and local feedback categories into a maintainable roadmap."""

    def build_radar(self) -> dict[str, Any]:
        sources = self._sources()
        needs = sorted((need.to_api() for need in self._needs()), key=lambda item: item["priority_score"], reverse=True)
        top_needs = needs[:5]
        source_ids = {source.id for source in sources}

        return {
            "status": "ready",
            "method": {
                "scoring": "impact * confidence - effort * 4, normalized to 0-100",
                "input_sources": [source.to_api() for source in sources],
                "limitations": [
                    "Scores are deterministic planning signals, not user analytics.",
                    "External research signals must be validated against Chinese legal workflows before release.",
                    "No private user documents or credentials are used in this radar.",
                ],
            },
            "summary": {
                "need_count": len(needs),
                "top_need_ids": [need["id"] for need in top_needs],
                "high_priority_count": sum(1 for need in needs if need["priority_band"] == "high"),
                "source_coverage": {source_id: sum(1 for need in needs if source_id in need["source_ids"]) for source_id in source_ids},
            },
            "needs": needs,
            "roadmap": self._roadmap(top_needs),
            "maintenance_actions": [
                "Review top needs before changing model routing, report schema, or upload workflow.",
                "Cluster incoming feedback tickets against these need IDs before scheduling feature work.",
                "Do not ship user-facing legal answers unless linked quality, citation, evidence, and release checks are passing.",
            ],
        }

    def _sources(self) -> tuple[ResearchSource, ...]:
        return (
            ResearchSource(
                id="legalbench",
                title="LegalBench legal reasoning benchmark",
                url="https://arxiv.org/abs/2308.11462",
                signal="Legal AI evaluation should cover multiple legal reasoning task types, not a single generic QA score.",
            ),
            ResearchSource(
                id="legalbench-rag",
                title="LegalBench-RAG legal retrieval benchmark",
                url="https://arxiv.org/abs/2408.10343",
                signal="Legal RAG evaluation needs retrieval, citation, and grounding checks that are separate from general legal reasoning.",
            ),
            ResearchSource(
                id="lawbench",
                title="LawBench Chinese legal LLM benchmark",
                url="https://aclanthology.org/2024.emnlp-main.452/",
                signal="Chinese legal task coverage should include legal knowledge, reasoning, and application rather than generic chatbot checks.",
            ),
            ResearchSource(
                id="lexeval",
                title="LexEval Chinese legal benchmark",
                url="https://arxiv.org/abs/2409.20288",
                signal="Chinese legal workflows need jurisdiction-specific cognition, reasoning, and generation validation.",
            ),
            ResearchSource(
                id="casegen",
                title="CaseGen legal case generation benchmark",
                url="https://arxiv.org/abs/2502.17943",
                signal="Legal document generation should be evaluated as staged classification, extraction, reasoning, and drafting tasks.",
            ),
            ResearchSource(
                id="stanford-legal-rag",
                title="Stanford legal RAG hallucination evaluation",
                url="https://reglab.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/",
                signal="Legal RAG tools still need citation grounding checks, professional review, and hallucination-aware release gates.",
            ),
            ResearchSource(
                id="internal-feedback-triage",
                title="Internal deterministic feedback triage",
                url="docs/FEEDBACK_TRIAGE.md",
                signal="Feedback categories should distinguish security, access, legal-output risk, pipeline failure, and usability work.",
            ),
            ResearchSource(
                id="local-maintenance-notes",
                title="Local user research and maintenance notes",
                url="docs/USER_RESEARCH_AND_MAINTENANCE.md",
                signal="Target users need low-cost review, traceable evidence, missing facts, and lawyer-review escalation.",
            ),
            ResearchSource(
                id="legal-research-backlog",
                title="Legal research to engineering backlog",
                url="docs/LEGAL_RESEARCH_BACKLOG.md",
                signal="Paper and benchmark signals should become tested engineering work before they are used in public release claims.",
            ),
        )

    def _needs(self) -> tuple[UserNeed, ...]:
        return (
            UserNeed(
                id="traceable-legal-review",
                title="Traceable legal review output",
                category="legal_quality",
                user_segments=("lawyer", "legal_ops", "individual"),
                pain_point="Users cannot rely on legal AI output if risks, sources, and source support are not visible.",
                product_response="Keep citation audit, evidence audit, source appendix, and release decision visible in every deep review.",
                impact=10,
                effort=5,
                confidence=9,
                source_ids=(
                    "legalbench",
                    "legalbench-rag",
                    "lawbench",
                    "lexeval",
                    "stanford-legal-rag",
                    "local-maintenance-notes",
                    "legal-research-backlog",
                ),
                evidence_paths=(
                    "app/backend/services/citation_audit.py",
                    "app/backend/services/evidence_audit.py",
                    "app/backend/services/release_decision.py",
                    "app/frontend/src/pages/DeepReportPage.tsx",
                ),
                release_gate_links=("citation_audit", "evidence_audit", "release_decision"),
                next_actions=(
                    "Keep high-risk items blocked from delivery when citation or evidence coverage fails.",
                    "Add UI filters for risks without reviewable sources.",
                ),
            ),
            UserNeed(
                id="cheap-first-review-routing",
                title="Cheap-first model routing",
                category="model_ops",
                user_segments=("legal_ops", "individual"),
                pain_point="Cost-sensitive users need useful review without sending every task to premium models.",
                product_response="Use deterministic preflight and route simple tasks to cheap Gemini-compatible models first.",
                impact=9,
                effort=4,
                confidence=8,
                source_ids=("local-maintenance-notes", "internal-feedback-triage", "legal-research-backlog", "casegen"),
                evidence_paths=(
                    "app/backend/services/model_budget.py",
                    "app/backend/services/document_preflight.py",
                    "docs/AI_MODEL_STRATEGY.md",
                ),
                release_gate_links=("document_preflight", "model_budget"),
                next_actions=(
                    "Track per-stage model usage and failed escalation rate.",
                    "Keep premium routing reserved for complex PDF and high-risk review tasks.",
                ),
            ),
            UserNeed(
                id="privacy-safe-upload",
                title="Privacy-safe upload review",
                category="security",
                user_segments=("lawyer", "legal_ops", "individual"),
                pain_point="Legal files often contain identity, contact, payment, and dispute details that should not be logged raw.",
                product_response="Scan for personal data patterns and expose privacy risk during upload preflight.",
                impact=10,
                effort=4,
                confidence=8,
                source_ids=("internal-feedback-triage", "local-maintenance-notes"),
                evidence_paths=(
                    "app/backend/services/privacy_redaction.py",
                    "app/backend/services/document_preflight.py",
                    "app/frontend/src/pages/UploadPage.tsx",
                    "docs/PRIVACY_REDACTION.md",
                ),
                release_gate_links=("privacy_redaction", "secret_scan"),
                next_actions=(
                    "Add opt-in redacted preview before sending text to model review.",
                    "Track privacy-risk distribution without storing raw matched values.",
                ),
            ),
            UserNeed(
                id="robust-extraction-quality",
                title="Robust document extraction",
                category="document_processing",
                user_segments=("lawyer", "legal_ops"),
                pain_point="Scanned or low-text PDFs can produce incomplete review input and misleading legal conclusions.",
                product_response="Audit extraction quality, OCR pages, low-text pages, and block unusable extraction before model review.",
                impact=9,
                effort=5,
                confidence=8,
                source_ids=(
                    "local-maintenance-notes",
                    "internal-feedback-triage",
                    "legal-research-backlog",
                    "lawbench",
                    "lexeval",
                ),
                evidence_paths=(
                    "app/backend/services/extraction_quality.py",
                    "app/backend/routers/deep_review.py",
                    "app/frontend/src/pages/UploadPage.tsx",
                    "docs/EXTRACTION_QUALITY_AUDIT.md",
                ),
                release_gate_links=("extraction_quality", "document_preflight"),
                next_actions=(
                    "Store extraction-quality trends by parser and document type.",
                    "Add operator override only when source document is manually checked.",
                ),
            ),
            UserNeed(
                id="prompt-injection-resilience",
                title="Prompt-injection resilience",
                category="security",
                user_segments=("lawyer", "legal_ops"),
                pain_point="Uploaded documents can contain instructions that attempt to override system behavior or reveal secrets.",
                product_response="Treat instruction-like text as document evidence and show instruction risk in preflight.",
                impact=8,
                effort=4,
                confidence=8,
                source_ids=("internal-feedback-triage", "stanford-legal-rag", "legalbench-rag", "legal-research-backlog"),
                evidence_paths=(
                    "app/backend/services/instruction_injection_audit.py",
                    "app/backend/services/document_preflight.py",
                    "app/frontend/src/pages/UploadPage.tsx",
                    "docs/INSTRUCTION_INJECTION_AUDIT.md",
                ),
                release_gate_links=("instruction_injection_audit", "secret_scan"),
                next_actions=(
                    "Add matched-text review workflow for operators.",
                    "Keep secret-bearing examples out of docs, tests, and prompts.",
                ),
            ),
            UserNeed(
                id="plain-language-actionability",
                title="Plain-language actionability",
                category="product",
                user_segments=("individual", "legal_ops"),
                pain_point="Non-lawyer users need a clear next step, not only a professional risk matrix.",
                product_response="Preserve executive summaries, missing facts, next steps, replacement clauses, and lawyer-review triggers.",
                impact=8,
                effort=6,
                confidence=7,
                source_ids=("local-maintenance-notes", "legal-research-backlog", "casegen", "lawbench", "lexeval"),
                evidence_paths=(
                    "app/frontend/src/pages/DeepReportPage.tsx",
                    "app/backend/services/report_quality_gate.py",
                    "docs/DEEP_REVIEW_QUALITY_GATES.md",
                ),
                release_gate_links=("report_quality_gate", "release_decision"),
                next_actions=(
                    "Add persona-specific report modes for individual, legal ops, and lawyer users.",
                    "Measure whether users can identify the top three required actions.",
                ),
            ),
            UserNeed(
                id="feedback-to-roadmap-loop",
                title="Feedback-to-roadmap loop",
                category="maintenance",
                user_segments=("maintainer", "support_ops"),
                pain_point="Unclustered feedback turns into scattered fixes instead of a maintainable roadmap.",
                product_response="Map feedback categories to user-need IDs and release gates before scheduling work.",
                impact=7,
                effort=3,
                confidence=8,
                source_ids=("internal-feedback-triage", "local-maintenance-notes"),
                evidence_paths=(
                    "app/backend/services/feedback_triage.py",
                    "app/backend/services/user_needs_radar.py",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                    "docs/USER_NEEDS_RADAR.md",
                ),
                release_gate_links=("feedback_triage", "release_readiness"),
                next_actions=(
                    "Add feedback preview labels that include the nearest user-need ID.",
                    "Review need scores during each release-readiness pass.",
                ),
            ),
        )

    def _roadmap(self, top_needs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "phase": "stabilize",
                "focus_need_ids": [need["id"] for need in top_needs[:3]],
                "exit_criteria": [
                    "All linked release gates pass or are explicitly waived.",
                    "No high-risk legal output ships without citation and evidence review.",
                ],
            },
            {
                "phase": "measure",
                "focus_need_ids": [need["id"] for need in top_needs[3:5]],
                "exit_criteria": [
                    "Upload, extraction, privacy, and model-routing metrics are visible to maintainers.",
                    "Feedback tickets can be clustered into user-need IDs.",
                ],
            },
        ]


def priority_score(impact: int, effort: int, confidence: int) -> int:
    raw = impact * confidence - effort * 4
    return max(0, min(100, raw))


def priority_band(score: int) -> str:
    if score >= 50:
        return "high"
    if score >= 35:
        return "medium"
    return "low"
