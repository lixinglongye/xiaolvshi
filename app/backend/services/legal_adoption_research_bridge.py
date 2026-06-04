from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from services.legal_external_research_digest import LegalExternalResearchDigestService
from services.product_feature_gap_radar import ProductFeatureGapRadarService
from services.user_needs_radar import UserNeedsRadarService


@dataclass(frozen=True)
class AdoptionResearchSource:
    id: str
    title: str
    url: str
    source_type: str
    signal: str
    local_interpretation: str

    def to_api(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchBridgeAction:
    id: str
    title: str
    product_area: str
    source_ids: tuple[str, ...]
    user_need_ids: tuple[str, ...]
    product_gap_ids: tuple[str, ...]
    release_gate_links: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    impact: int
    urgency: int
    effort: int
    confidence: int
    low_cost_fit: int
    next_actions: tuple[str, ...]
    validation_commands: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_ids"] = list(self.source_ids)
        data["user_need_ids"] = list(self.user_need_ids)
        data["product_gap_ids"] = list(self.product_gap_ids)
        data["release_gate_links"] = list(self.release_gate_links)
        data["evidence_paths"] = list(self.evidence_paths)
        data["next_actions"] = list(self.next_actions)
        data["validation_commands"] = list(self.validation_commands)
        data["priority_score"] = priority_score(
            impact=self.impact,
            urgency=self.urgency,
            effort=self.effort,
            confidence=self.confidence,
            low_cost_fit=self.low_cost_fit,
        )
        data["priority_band"] = priority_band(data["priority_score"])
        return data


class LegalAdoptionResearchBridgeService:
    """Map public research and adoption signals into local product work."""

    def build_bridge(self) -> dict[str, Any]:
        sources = self._sources()
        source_ids = {source.id for source in sources}
        actions = sorted(
            (action.to_api() for action in self._actions()),
            key=lambda item: (-item["priority_score"], -item["low_cost_fit"], item["id"]),
        )
        need_ids = {need["id"] for need in UserNeedsRadarService().build_radar()["needs"]}
        gap_ids = {gap["id"] for gap in ProductFeatureGapRadarService().build_radar()["feature_gaps"]}
        research_digest = LegalExternalResearchDigestService().build_digest()
        product_area_counts = Counter(action["product_area"] for action in actions)

        return {
            "status": "ready",
            "method": {
                "type": "legal-adoption-research-to-roadmap-bridge",
                "scoring": "impact * confidence + urgency * 5 + low_cost_fit * 3 - effort * 4, bounded to 0-100",
                "input_sources": [source.to_api() for source in sources],
                "limitations": [
                    "This bridge stores source metadata and local planning mappings only.",
                    "It does not download public benchmark datasets or store research report raw text.",
                    "Survey signals are planning inputs; product adoption must still be validated with local feedback.",
                ],
            },
            "summary": {
                "source_count": len(sources),
                "action_count": len(actions),
                "high_priority_count": sum(1 for action in actions if action["priority_band"] == "high"),
                "cheap_first_action_count": sum(1 for action in actions if action["low_cost_fit"] >= 8),
                "governance_action_count": product_area_counts.get("ai_governance", 0),
                "legal_benchmark_action_count": product_area_counts.get("legal_benchmark", 0),
                "product_area_counts": dict(sorted(product_area_counts.items())),
                "research_digest_signal_count": research_digest["summary"]["signal_count"],
                "known_need_count": len(need_ids),
                "known_gap_count": len(gap_ids),
                "source_coverage": {
                    source_id: sum(1 for action in actions if source_id in action["source_ids"])
                    for source_id in sorted(source_ids)
                },
                "unmapped_need_ids": sorted(
                    {
                        need_id
                        for action in actions
                        for need_id in action["user_need_ids"]
                        if need_id not in need_ids
                    }
                ),
                "unmapped_gap_ids": sorted(
                    {
                        gap_id
                        for action in actions
                        for gap_id in action["product_gap_ids"]
                        if gap_id not in gap_ids
                    }
                ),
            },
            "implementation_queue": [
                {
                    "action_id": action["id"],
                    "title": action["title"],
                    "priority_score": action["priority_score"],
                    "first_action": action["next_actions"][0],
                    "release_gate_links": action["release_gate_links"],
                    "validation_commands": action["validation_commands"],
                }
                for action in actions[:5]
            ],
            "actions": actions,
            "survey_intake_questions": [
                {
                    "id": "workflow-friction",
                    "prompt": "Which legal-review workflow step took the longest or felt least trustworthy?",
                    "privacy_rule": "Capture category and severity only; do not store client facts or document text.",
                    "maps_to_need_ids": ["traceable-legal-review", "plain-language-actionability"],
                },
                {
                    "id": "governance-blocker",
                    "prompt": "What policy, confidentiality, or review concern would block use in a real matter?",
                    "privacy_rule": "Capture blocker type only; do not store names, emails, matter IDs, or privileged facts.",
                    "maps_to_need_ids": ["privacy-safe-upload", "prompt-injection-resilience"],
                },
                {
                    "id": "cost-acceptance",
                    "prompt": "When would a cheap model be acceptable, and when should the workflow escalate?",
                    "privacy_rule": "Capture task type and escalation reason only; do not store prompts or model output.",
                    "maps_to_need_ids": ["cheap-first-review-routing", "robust-extraction-quality"],
                },
            ],
            "release_guardrails": [
                "Do not claim law-firm adoption, benchmark scores, or productivity impact from this planning bridge.",
                "Do not ship new legal-answer behavior unless linked citation, evidence, privacy, and release gates pass.",
                "Keep Gemini/NewAPI validation cheap-first and synthetic by default; escalate only documented failure cases.",
            ],
            "validation_commands": [
                "python -m pytest tests/test_legal_adoption_research_bridge.py -q",
                "python -m pytest tests/test_user_needs_radar.py tests/test_product_feature_gap_radar.py tests/test_legal_external_research_digest.py -q",
            ],
            "privacy_note": (
                "The bridge is metadata-only. It must not include survey free text, raw feedback, client documents, "
                "public benchmark examples, model outputs, emails, credentials, or API keys."
            ),
        }

    def _sources(self) -> tuple[AdoptionResearchSource, ...]:
        return (
            AdoptionResearchSource(
                id="legalbench",
                title="LegalBench legal reasoning benchmark",
                url="https://arxiv.org/abs/2308.11462",
                source_type="paper-benchmark",
                signal="Legal evaluation should cover many legal reasoning task families, not only generic QA.",
                local_interpretation="Keep synthetic legal fixtures grouped by task family, output schema, and release gate.",
            ),
            AdoptionResearchSource(
                id="frugalgpt",
                title="FrugalGPT cost-quality cascade",
                url="https://arxiv.org/abs/2305.05176",
                source_type="paper-routing",
                signal="Cheaper-model cascades can reduce inference cost while preserving quality with selective escalation.",
                local_interpretation="Keep Gemini/NewAPI defaults cheap-first and escalate only documented legal failure modes.",
            ),
            AdoptionResearchSource(
                id="ragas",
                title="RAGAS retrieval augmented generation evaluation",
                url="https://arxiv.org/abs/2309.15217",
                source_type="paper-evaluation",
                signal="RAG systems need faithfulness, answer relevance, and context relevance checks.",
                local_interpretation="Map RAG metrics into legal citation, evidence, and unsupported-claim release gates.",
            ),
            AdoptionResearchSource(
                id="crag",
                title="CRAG comprehensive RAG benchmark",
                url="https://arxiv.org/abs/2406.04744",
                source_type="paper-benchmark",
                signal="Retrieval QA needs source availability, factuality, abstention, and failure-mode coverage.",
                local_interpretation="Add source-unavailable and abstention scenarios before claiming grounded legal answers.",
            ),
            AdoptionResearchSource(
                id="tr-future-professionals-2025",
                title="Thomson Reuters Future of Professionals 2025",
                url="https://www.thomsonreuters.com/en-us/posts/technology/future-of-professionals-2025/",
                source_type="industry-adoption-report",
                signal="Visible AI strategy, governance, training, and measurable workflow value matter for professional adoption.",
                local_interpretation="Expose governance, privacy, workflow value, and maintainer evidence instead of only model features.",
            ),
            AdoptionResearchSource(
                id="tr-ai-ethics-2025",
                title="Thomson Reuters AI ethics guidance",
                url="https://www.thomsonreuters.com/en/insights/articles/ethics-of-artificial-intelligence",
                source_type="industry-governance-guidance",
                signal="Responsible professional AI use needs fairness, transparency, privacy, accountability, and compliance controls.",
                local_interpretation="Keep user-facing release claims tied to privacy, audit, and human-review guardrails.",
            ),
        )

    def _actions(self) -> tuple[ResearchBridgeAction, ...]:
        return (
            ResearchBridgeAction(
                id="cheap-first-governed-review-loop",
                title="Cheap-first governed legal review loop",
                product_area="model_cost_ops",
                source_ids=("frugalgpt", "tr-future-professionals-2025"),
                user_need_ids=("cheap-first-review-routing", "traceable-legal-review"),
                product_gap_ids=("model-cost-ops", "contract-review"),
                release_gate_links=("gemini-newapi-model-selector", "gemini-newapi-selector-replay", "model-cost-guardrails"),
                evidence_paths=(
                    "app/backend/services/gemini_newapi_model_selector.py",
                    "app/backend/services/gemini_newapi_selector_replay.py",
                    "app/backend/services/model_cost_guardrails.py",
                    "docs/GEMINI_NEWAPI_MODEL_SELECTOR.md",
                ),
                impact=10,
                urgency=9,
                effort=4,
                confidence=9,
                low_cost_fit=10,
                next_actions=(
                    "Keep cheap Gemini-compatible models as the default for routine review and intake tasks.",
                    "Escalate only fixture-backed failures that cite a legal quality or extraction-risk reason.",
                    "Show maintainers the selected route, escalation reason, and cost guardrail without raw prompts.",
                ),
                validation_commands=(
                    "python -m pytest tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_selector_replay.py -q",
                    "python -m pytest tests/test_model_cost_guardrails.py tests/test_model_request_cost_bounds.py -q",
                ),
            ),
            ResearchBridgeAction(
                id="authority-grounded-rag-acceptance",
                title="Authority-grounded RAG acceptance gates",
                product_area="legal_rag",
                source_ids=("ragas", "crag", "legalbench"),
                user_need_ids=("traceable-legal-review", "prompt-injection-resilience"),
                product_gap_ids=("legal-knowledge-rag", "evidence-management"),
                release_gate_links=("legal-rag-evaluation", "citation_audit", "evidence_audit"),
                evidence_paths=(
                    "app/backend/services/legal_rag_evaluation.py",
                    "app/backend/services/legal_grounding_quick_audit.py",
                    "app/backend/services/citation_audit.py",
                    "docs/LEGAL_RAG_EVALUATION.md",
                ),
                impact=10,
                urgency=9,
                effort=6,
                confidence=8,
                low_cost_fit=7,
                next_actions=(
                    "Add source-unavailable and abstention checks to every legal RAG release pass.",
                    "Block unsupported legal conclusions instead of presenting them as low-confidence answers.",
                    "Keep retrieval examples synthetic until licenses, attribution, and privacy gates pass.",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_rag_evaluation.py tests/test_legal_grounding_quick_audit.py -q",
                    "python -m pytest tests/test_citation_audit.py tests/test_evidence_audit.py -q",
                ),
            ),
            ResearchBridgeAction(
                id="legal-task-coverage-to-fixtures",
                title="Legal task coverage to synthetic fixtures",
                product_area="legal_benchmark",
                source_ids=("legalbench", "crag"),
                user_need_ids=("traceable-legal-review", "robust-extraction-quality"),
                product_gap_ids=("contract-review", "document-generation"),
                release_gate_links=("legal-review-benchmark", "legal-document-benchmark-suite"),
                evidence_paths=(
                    "app/backend/services/legal_review_benchmark.py",
                    "app/backend/services/legal_document_benchmark_suite.py",
                    "app/backend/services/legal_document_benchmark_fixtures.py",
                    "docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md",
                ),
                impact=9,
                urgency=8,
                effort=5,
                confidence=8,
                low_cost_fit=8,
                next_actions=(
                    "Keep each fixture mapped to task family, expected route, expected warning, and output field.",
                    "Prefer three-case laptop-safe suites before larger benchmark imports.",
                    "Do not claim external benchmark scores from synthetic fixture coverage.",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_review_benchmark.py -q",
                    "python -m pytest tests/test_legal_fixture_quick_suite.py -q",
                ),
            ),
            ResearchBridgeAction(
                id="governance-visible-maintainer-workflow",
                title="Governance-visible maintainer workflow",
                product_area="ai_governance",
                source_ids=("tr-future-professionals-2025", "tr-ai-ethics-2025"),
                user_need_ids=("privacy-safe-upload", "feedback-to-roadmap-loop"),
                product_gap_ids=("safety-compliance", "feedback-loop"),
                release_gate_links=("privacy_redaction", "release_claim_compliance", "oss-maintenance-evidence"),
                evidence_paths=(
                    "app/backend/services/privacy_redaction.py",
                    "app/backend/services/release_claim_compliance.py",
                    "app/backend/services/maintenance_evidence.py",
                    "docs/PRIVACY_REDACTION.md",
                ),
                impact=9,
                urgency=9,
                effort=4,
                confidence=8,
                low_cost_fit=8,
                next_actions=(
                    "Show privacy, accountability, release-claim, and human-review status in maintainer evidence.",
                    "Collect only category-level adoption blockers and governance needs.",
                    "Keep support forms and product claims linked to repository-backed evidence.",
                ),
                validation_commands=(
                    "python -m pytest tests/test_privacy_redaction.py tests/test_release_claim_compliance.py -q",
                    "python -m pytest tests/test_maintenance_evidence.py -q",
                ),
            ),
            ResearchBridgeAction(
                id="persona-survey-to-roadmap-loop",
                title="Persona survey to roadmap loop",
                product_area="user_research",
                source_ids=("tr-future-professionals-2025", "legalbench"),
                user_need_ids=("feedback-to-roadmap-loop", "plain-language-actionability"),
                product_gap_ids=("feedback-loop", "case-workbench"),
                release_gate_links=("feedback-triage", "release-readiness"),
                evidence_paths=(
                    "app/backend/services/user_needs_radar.py",
                    "app/backend/services/feedback_roadmap_alignment.py",
                    "app/backend/services/product_feature_gap_radar.py",
                    "docs/USER_NEEDS_RADAR.md",
                ),
                impact=8,
                urgency=8,
                effort=4,
                confidence=7,
                low_cost_fit=9,
                next_actions=(
                    "Ask structured, privacy-safe questions about workflow friction, governance blockers, and escalation tolerance.",
                    "Map every answer to a need ID and product gap before scheduling work.",
                    "Avoid storing free-form legal facts, matter IDs, account emails, or pasted document excerpts.",
                ),
                validation_commands=(
                    "python -m pytest tests/test_user_needs_radar.py tests/test_feedback_roadmap_alignment.py -q",
                    "python -m pytest tests/test_product_feature_gap_radar.py -q",
                ),
            ),
        )


def priority_score(
    *,
    impact: int,
    urgency: int,
    effort: int,
    confidence: int,
    low_cost_fit: int,
) -> int:
    raw = impact * confidence + urgency * 5 + low_cost_fit * 3 - effort * 4
    return max(0, min(100, raw))


def priority_band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
