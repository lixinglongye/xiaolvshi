from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExternalResearchSignal:
    id: str
    title: str
    url: str
    source_type: str
    checked_signal: str
    engineering_takeaway: str
    product_area: str
    local_validation_path: str
    license_or_privacy_gate: str
    evidence_paths: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_paths"] = list(self.evidence_paths)
        return data


class LegalExternalResearchDigestService:
    """Convert external legal-AI/RAG research signals into project work."""

    def build_digest(self) -> dict[str, Any]:
        signals = self._signals()
        product_area_counts: dict[str, int] = {}
        for signal in signals:
            product_area_counts[signal.product_area] = product_area_counts.get(signal.product_area, 0) + 1

        return {
            "status": "ready",
            "method": {
                "type": "external-legal-ai-research-digest",
                "notes": [
                    "Uses public source metadata and paper links only; it does not download datasets or copy benchmark examples.",
                    "Maps each research signal to local deterministic services, docs, and low-resource validation paths.",
                    "Treats licenses, attribution, privacy, and public benchmark raw text as explicit gates before import.",
                ],
            },
            "summary": {
                "signal_count": len(signals),
                "benchmark_source_count": sum(1 for signal in signals if "benchmark" in signal.source_type),
                "rag_source_count": sum(1 for signal in signals if signal.product_area == "legal_rag"),
                "chinese_legal_source_count": sum(1 for signal in signals if signal.product_area == "chinese_legal_workflow"),
                "document_generation_source_count": sum(
                    1 for signal in signals if signal.product_area == "legal_document_generation"
                ),
                "cheap_first_source_count": sum(1 for signal in signals if signal.product_area == "model_cost_ops"),
                "product_area_counts": dict(sorted(product_area_counts.items())),
            },
            "signals": [signal.to_api() for signal in signals],
            "implementation_queue": self._implementation_queue(signals),
            "low_resource_validation": {
                "default_fixture_limit": 2,
                "commands": [
                    "python -m pytest tests/test_legal_external_research_digest.py -q",
                    "python -m pytest tests/test_legal_research_backlog.py tests/test_legal_fixture_quick_suite.py -q",
                ],
                "policy": "Run synthetic fixtures and metadata-only checks before any public benchmark import.",
            },
            "release_guardrails": [
                "Do not claim public benchmark scores until source license review, attribution, sampling, and run archives exist.",
                "Do not commit raw public benchmark examples, real client documents, raw model outputs, or API credentials.",
                "Use cheap-first Gemini/NewAPI fixture runs for local validation before escalating selected failures.",
            ],
            "privacy_note": (
                "The digest stores source titles, URLs, planning signals, evidence paths, and validation commands only. "
                "It must not store benchmark raw text, private legal matter facts, user documents, emails, or secrets."
            ),
        }

    def _signals(self) -> tuple[ExternalResearchSignal, ...]:
        return (
            ExternalResearchSignal(
                id="legalbench",
                title="LegalBench legal reasoning benchmark",
                url="https://arxiv.org/abs/2308.11462",
                source_type="paper-benchmark",
                checked_signal="Legal model evaluation should be multi-task and legally specific instead of a single generic score.",
                engineering_takeaway="Keep benchmark fixtures grouped by legal task family, expected route, expected signals, and output schema fields.",
                product_area="legal_benchmark",
                local_validation_path="/api/v1/maintenance/legal-review-benchmark/quick-suite",
                license_or_privacy_gate="Use synthetic local fixtures by default; public task examples require attribution and license review before import.",
                evidence_paths=(
                    "app/backend/services/legal_review_benchmark.py",
                    "app/backend/services/legal_research_backlog.py",
                    "docs/LEGAL_REVIEW_BENCHMARK.md",
                    "docs/LEGAL_RESEARCH_BACKLOG.md",
                ),
            ),
            ExternalResearchSignal(
                id="cuad",
                title="CUAD contract review dataset",
                url="https://www.atticusprojectai.org/cuad",
                source_type="public-dataset-candidate",
                checked_signal="Contract review benefits from clause-level issue spotting and extraction-style evaluation.",
                engineering_takeaway="Expand synthetic clause fixtures before importing public samples; every clause category must map to report schema and smoke metrics.",
                product_area="contract_review",
                local_validation_path="/api/v1/maintenance/legal-review-benchmark/public-sampler",
                license_or_privacy_gate="Keep CUAD as catalog metadata until dataset license, attribution, and sample-size policy are documented.",
                evidence_paths=(
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "app/backend/services/legal_fixture_prompt_pack.py",
                    "docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md",
                    "docs/LEGAL_FIXTURE_PROMPT_PACK.md",
                ),
            ),
            ExternalResearchSignal(
                id="ragas",
                title="RAGAS retrieval augmented generation metrics",
                url="https://arxiv.org/abs/2309.15217",
                source_type="paper-evaluation",
                checked_signal="RAG evaluation should inspect faithfulness, answer relevance, and context relevance rather than final text alone.",
                engineering_takeaway="Map RAG metrics to legal citation, evidence, unsupported-claim, and grounding quick-audit gates.",
                product_area="legal_rag",
                local_validation_path="/api/v1/legal-knowledge/grounding-quick-audit-policy",
                license_or_privacy_gate="Use metric ideas and synthetic examples; do not store private retrieval contexts or raw model answers.",
                evidence_paths=(
                    "app/backend/services/legal_rag_evaluation.py",
                    "app/backend/services/legal_grounding_quick_audit.py",
                    "docs/LEGAL_RAG_EVALUATION.md",
                    "docs/LEGAL_GROUNDING_QUICK_AUDIT.md",
                ),
            ),
            ExternalResearchSignal(
                id="crag",
                title="CRAG comprehensive RAG benchmark",
                url="https://arxiv.org/abs/2406.04744",
                source_type="paper-benchmark",
                checked_signal="Retrieval QA evaluation needs source availability, factuality, abstention, and retrieval-failure cases.",
                engineering_takeaway="Add legal source-unavailable, abstention, and missing-authority cases before claiming grounded legal answers.",
                product_area="legal_rag",
                local_validation_path="/api/v1/legal-knowledge/rag-evaluation-policy",
                license_or_privacy_gate="Keep failure-mode tests synthetic until any public examples pass license and privacy review.",
                evidence_paths=(
                    "app/backend/services/legal_rag_evaluation.py",
                    "app/backend/services/case_evidence_graph.py",
                    "docs/CASE_EVIDENCE_GRAPH.md",
                    "docs/LEGAL_RAG_EVALUATION.md",
                ),
            ),
            ExternalResearchSignal(
                id="legalbench-rag",
                title="LegalBench-RAG legal retrieval benchmark",
                url="https://arxiv.org/abs/2408.10343",
                source_type="paper-benchmark",
                checked_signal="Legal RAG benchmark work should separate retrieval, grounding, citation support, and abstention behavior.",
                engineering_takeaway="Map legal RAG benchmark signals to failure fixtures, authority/citation gates, and retrieval diagnostics before importing public contexts.",
                product_area="legal_rag",
                local_validation_path="/api/v1/maintenance/legal-review-benchmark/rag-failure-fixtures",
                license_or_privacy_gate="Keep public retrieval contexts out of local validation until license, attribution, and privacy review pass.",
                evidence_paths=(
                    "app/backend/services/legal_rag_failure_fixtures.py",
                    "app/backend/services/legal_rag_authority_citation_gate.py",
                    "app/backend/services/legal_rag_retrieval_diagnostics_gate.py",
                    "docs/LEGAL_RAG_FAILURE_FIXTURES.md",
                    "docs/LEGAL_RAG_RETRIEVAL_DIAGNOSTICS_GATE.md",
                ),
            ),
            ExternalResearchSignal(
                id="lexeval",
                title="LexEval Chinese legal benchmark",
                url="https://arxiv.org/abs/2409.20288",
                source_type="paper-benchmark",
                checked_signal="Chinese legal evaluation should cover cognition, reasoning, and generation task families instead of generic legal QA only.",
                engineering_takeaway="Map LexEval-style Chinese legal task families to zh-CN synthetic document fixtures and user-need coverage rows.",
                product_area="chinese_legal_workflow",
                local_validation_path="/api/v1/maintenance/legal-review-benchmark/document-coverage",
                license_or_privacy_gate="Keep LexEval examples metadata-only until source license, attribution, and jurisdiction notes are reviewed.",
                evidence_paths=(
                    "app/backend/services/legal_document_benchmark_coverage.py",
                    "app/backend/services/user_need_benchmark_coverage.py",
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "docs/LEGAL_DOCUMENT_BENCHMARK_COVERAGE.md",
                    "docs/USER_NEED_BENCHMARK_COVERAGE.md",
                ),
            ),
            ExternalResearchSignal(
                id="casegen",
                title="CaseGen legal case generation benchmark",
                url="https://arxiv.org/abs/2502.17943",
                source_type="paper-benchmark",
                checked_signal="Legal case document generation should be evaluated through staged classification, extraction, reasoning, and drafting checks.",
                engineering_takeaway="Use CaseGen as a document-generation task-shape reference for structure, citation, PII, and risk-label fixture checks.",
                product_area="legal_document_generation",
                local_validation_path="/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                license_or_privacy_gate="Do not copy public case text or generated legal documents into the repo before source review.",
                evidence_paths=(
                    "app/backend/services/legal_document_benchmark_fixtures.py",
                    "app/backend/services/legal_document_benchmark_suite.py",
                    "app/backend/services/legal_document_coverage_claim_policy.py",
                    "docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md",
                    "docs/LEGAL_DOCUMENT_COVERAGE_CLAIM_POLICY.md",
                ),
            ),
            ExternalResearchSignal(
                id="frugalgpt",
                title="FrugalGPT cost-quality cascade",
                url="https://arxiv.org/abs/2305.05176",
                source_type="paper-routing",
                checked_signal="Cost-quality cascades can lower serving cost by trying cheaper models first and escalating selectively.",
                engineering_takeaway="Keep Gemini/NewAPI routing cheap-first, archive fixture failures, and escalate only selected legal tasks.",
                product_area="model_cost_ops",
                local_validation_path="/api/v1/maintenance/legal-review-benchmark/result-archive",
                license_or_privacy_gate="Archive only sanitized route, score, model, and cost summaries; never raw gateway output or keys.",
                evidence_paths=(
                    "app/backend/services/model_escalation_policy.py",
                    "app/backend/services/legal_fixture_result_archive.py",
                    "docs/MODEL_ESCALATION_POLICY.md",
                    "docs/LEGAL_FIXTURE_RESULT_ARCHIVE.md",
                ),
            ),
        )

    def _implementation_queue(self, signals: tuple[ExternalResearchSignal, ...]) -> list[dict[str, Any]]:
        priority_order = {
            "frugalgpt": 1,
            "legalbench": 2,
            "ragas": 3,
            "crag": 4,
            "legalbench-rag": 5,
            "lexeval": 6,
            "casegen": 7,
            "cuad": 8,
        }
        return [
            {
                "signal_id": signal.id,
                "title": signal.title,
                "priority": priority_order[signal.id],
                "next_action": signal.engineering_takeaway,
                "validation_target": signal.local_validation_path,
                "evidence_paths": list(signal.evidence_paths),
            }
            for signal in sorted(signals, key=lambda item: priority_order[item.id])
        ]
