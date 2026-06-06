from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LegalResearchSource:
    id: str
    title: str
    url: str
    source_type: str
    signal: str
    project_application: str

    def to_api(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class LegalResearchBacklogItem:
    id: str
    title: str
    workstream: str
    source_ids: tuple[str, ...]
    user_need_ids: tuple[str, ...]
    release_gate_links: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    impact: int
    effort: int
    confidence: int
    cost_sensitivity: int
    local_run_fit: int
    next_actions: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_ids"] = list(self.source_ids)
        data["user_need_ids"] = list(self.user_need_ids)
        data["release_gate_links"] = list(self.release_gate_links)
        data["evidence_paths"] = list(self.evidence_paths)
        data["next_actions"] = list(self.next_actions)
        data["priority_score"] = priority_score(
            impact=self.impact,
            effort=self.effort,
            confidence=self.confidence,
            cost_sensitivity=self.cost_sensitivity,
            local_run_fit=self.local_run_fit,
        )
        data["priority_band"] = priority_band(data["priority_score"])
        return data


class LegalResearchBacklogService:
    """Map legal-AI research sources into concrete project maintenance work."""

    def build_backlog(self) -> dict[str, Any]:
        sources = self._sources()
        source_ids = {source.id for source in sources}
        items = sorted((item.to_api() for item in self._items()), key=lambda item: item["priority_score"], reverse=True)
        high_priority = [item for item in items if item["priority_band"] == "high"]
        return {
            "status": "ready",
            "method": {
                "type": "legal-ai-research-to-engineering-backlog",
                "scoring": "impact * confidence + cost_sensitivity * 3 + local_run_fit * 2 - effort * 4, bounded to 0-100",
                "input_sources": [source.to_api() for source in sources],
                "limitations": [
                    "This is a deterministic planning artifact, not a claim that public datasets were imported.",
                    "Public benchmark examples stay out of local tests until license, attribution, and privacy review pass.",
                    "Backlog priority does not override release gates for privacy, citation, evidence, or model cost.",
                ],
            },
            "summary": {
                "source_count": len(sources),
                "backlog_item_count": len(items),
                "high_priority_count": len(high_priority),
                "cheap_first_item_count": sum(1 for item in items if "cheap-first-review-routing" in item["user_need_ids"]),
                "local_run_item_count": sum(1 for item in items if item["local_run_fit"] >= 7),
                "workstream_count": len({item["workstream"] for item in items}),
                "source_coverage": {source_id: sum(1 for item in items if source_id in item["source_ids"]) for source_id in source_ids},
            },
            "backlog": items,
            "workstream_plan": self._workstream_plan(items),
            "next_iteration_queue": [
                {
                    "item_id": item["id"],
                    "title": item["title"],
                    "priority_score": item["priority_score"],
                    "first_action": item["next_actions"][0],
                    "release_gate_links": item["release_gate_links"],
                }
                for item in items[:5]
            ],
            "maintenance_actions": [
                "Review this backlog before adding new legal benchmark fixtures or changing model-routing defaults.",
                "Prefer cheap-first, serial local runs when validating research-inspired changes on low-resource machines.",
                "Convert accepted research signals into tests and release-readiness evidence before making public claims.",
            ],
            "privacy_note": (
                "The backlog stores source URLs, planning scores, evidence paths, and action text only. "
                "It must not include API keys, user documents, public benchmark raw examples, emails, or raw model outputs."
            ),
        }

    def _sources(self) -> tuple[LegalResearchSource, ...]:
        return (
            LegalResearchSource(
                id="legalbench",
                title="LegalBench legal reasoning benchmark",
                url="https://arxiv.org/abs/2308.11462",
                source_type="paper-benchmark",
                signal="Legal evaluation needs multiple legal task families rather than one generic accuracy score.",
                project_application="Keep fixture coverage split across contract risk, evidence reasoning, extraction, privacy, injection, and legal RAG tasks.",
            ),
            LegalResearchSource(
                id="frugalgpt",
                title="FrugalGPT cost-quality cascade",
                url="https://arxiv.org/abs/2305.05176",
                source_type="paper-routing",
                signal="A cascade can reduce LLM serving cost by trying cheaper models first and escalating selectively.",
                project_application="Keep Gemini/NewAPI defaults cheap-first, record cost guardrails, and escalate only fixture-scoped failures.",
            ),
            LegalResearchSource(
                id="ragas",
                title="RAGAS retrieval-augmented generation metrics",
                url="https://arxiv.org/abs/2309.15217",
                source_type="paper-evaluation",
                signal="RAG outputs need faithfulness, answer relevance, and context relevance metrics.",
                project_application="Tie legal RAG reports to citation, evidence, grounding, and unsupported-claim checks.",
            ),
            LegalResearchSource(
                id="crag",
                title="CRAG comprehensive RAG benchmark",
                url="https://arxiv.org/abs/2406.04744",
                source_type="paper-benchmark",
                signal="Retrieval QA benchmarks should include factuality, source availability, and realistic retrieval failure modes.",
                project_application="Add legal source availability, abstention, and retrieval-failure cases before claiming legal grounding quality.",
            ),
            LegalResearchSource(
                id="cuad",
                title="CUAD contract review dataset",
                url="https://www.atticusprojectai.org/cuad",
                source_type="public-dataset-candidate",
                signal="Contract review evaluation benefits from clause-level issue spotting and extraction tasks.",
                project_application="Use CUAD as a cataloged reference for future sampled contract-clause fixtures after license review.",
            ),
            LegalResearchSource(
                id="legalbench-rag",
                title="LegalBench-RAG legal retrieval benchmark",
                url="https://arxiv.org/abs/2408.10343",
                source_type="paper-benchmark",
                signal="Legal RAG evaluation should separate retrieval, citation grounding, and answer support.",
                project_application="Use LegalBench-RAG as a metadata-only reference for legal RAG failure fixtures, authority/citation gates, and retrieval diagnostics.",
            ),
            LegalResearchSource(
                id="lexeval",
                title="LexEval Chinese legal benchmark",
                url="https://arxiv.org/abs/2409.20288",
                source_type="paper-benchmark",
                signal="Chinese legal evaluation needs cognition, reasoning, and generation task families.",
                project_application="Use LexEval as a zh-CN task-family reference for user-need coverage and legal-document fixture mapping.",
            ),
            LegalResearchSource(
                id="casegen",
                title="CaseGen legal case generation benchmark",
                url="https://arxiv.org/abs/2502.17943",
                source_type="paper-benchmark",
                signal="Legal case generation benefits from staged classification, extraction, reasoning, and drafting checks.",
                project_application="Use CaseGen as a local synthetic legal-document generation fixture planning reference.",
            ),
        )

    def _items(self) -> tuple[LegalResearchBacklogItem, ...]:
        return (
            LegalResearchBacklogItem(
                id="cheap-first-cascade-evaluation",
                title="Cheap-first cascade evaluation for legal fixtures",
                workstream="model_ops",
                source_ids=("frugalgpt", "legalbench"),
                user_need_ids=("cheap-first-review-routing", "traceable-legal-review"),
                release_gate_links=("model_cost_guardrails", "legal-review-benchmark", "fixture-run-report"),
                evidence_paths=(
                    "app/backend/services/model_escalation_policy.py",
                    "app/backend/services/legal_fixture_run_report.py",
                    "app/backend/services/legal_fixture_local_run_review.py",
                    "docs/MODEL_ESCALATION_POLICY.md",
                    "docs/LEGAL_FIXTURE_LOCAL_RUN_REVIEW.md",
                ),
                impact=10,
                effort=4,
                confidence=9,
                cost_sensitivity=10,
                local_run_fit=9,
                next_actions=(
                    "Keep cheap-first Gemini/NewAPI fixture runs as the default release evidence path.",
                    "Track which fixture failure patterns justify selected escalation instead of changing global defaults.",
                    "Add a release note only after fixture-run-report keeps cheap-first defaults or documents accepted gaps.",
                ),
            ),
            LegalResearchBacklogItem(
                id="legal-task-coverage-map",
                title="Legal task coverage map for synthetic fixtures",
                workstream="benchmark_design",
                source_ids=("legalbench", "cuad"),
                user_need_ids=("traceable-legal-review", "plain-language-actionability"),
                release_gate_links=("legal-review-benchmark", "report_quality_gate"),
                evidence_paths=(
                    "app/backend/services/legal_review_benchmark.py",
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "docs/LEGAL_BENCHMARK_FIXTURES.md",
                    "docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md",
                ),
                impact=9,
                effort=5,
                confidence=8,
                cost_sensitivity=6,
                local_run_fit=8,
                next_actions=(
                    "Keep each new legal fixture tied to a task family, expected route, expected signals, and expected tasks.",
                    "Add Chinese legal workflow variants without copying public benchmark raw examples into the repo.",
                    "Require fixture-smoke coverage before adding premium-model examples.",
                ),
            ),
            LegalResearchBacklogItem(
                id="rag-grounding-metric-gates",
                title="Legal RAG grounding metric gates",
                workstream="retrieval_quality",
                source_ids=("ragas", "crag"),
                user_need_ids=("traceable-legal-review", "prompt-injection-resilience"),
                release_gate_links=("legal-rag-evaluation", "citation_audit", "evidence_audit"),
                evidence_paths=(
                    "app/backend/services/legal_rag_evaluation.py",
                    "app/backend/services/legal_grounding_quick_audit.py",
                    "app/backend/services/citation_audit.py",
                    "docs/LEGAL_RAG_EVALUATION.md",
                    "docs/LEGAL_GROUNDING_QUICK_AUDIT.md",
                ),
                impact=10,
                effort=6,
                confidence=8,
                cost_sensitivity=5,
                local_run_fit=7,
                next_actions=(
                    "Map RAGAS-style faithfulness and context relevance to legal citation and evidence audit fields.",
                    "Add unsupported-claim and missing-source cases to quick grounding audits.",
                    "Block legal delivery when citation or evidence gates fail.",
                ),
            ),
            LegalResearchBacklogItem(
                id="retrieval-failure-abstention-cases",
                title="Retrieval failure and abstention cases",
                workstream="retrieval_quality",
                source_ids=("crag", "ragas"),
                user_need_ids=("traceable-legal-review", "robust-extraction-quality"),
                release_gate_links=("legal-rag-evaluation", "release_decision"),
                evidence_paths=(
                    "app/backend/services/release_decision.py",
                    "app/backend/services/legal_grounding_quick_audit.py",
                    "docs/DEEP_REVIEW_RELEASE_DECISION.md",
                    "docs/LEGAL_GROUNDING_QUICK_AUDIT.md",
                ),
                impact=9,
                effort=6,
                confidence=7,
                cost_sensitivity=4,
                local_run_fit=6,
                next_actions=(
                    "Add small synthetic cases where the correct behavior is to ask for missing sources or abstain.",
                    "Expose unsupported legal conclusions as release blockers, not just warnings.",
                    "Keep retrieval-failure fixtures synthetic until public source licenses are reviewed.",
                ),
            ),
            LegalResearchBacklogItem(
                id="contract-clause-sampling-plan",
                title="Contract clause sampling plan",
                workstream="benchmark_design",
                source_ids=("cuad", "legalbench"),
                user_need_ids=("traceable-legal-review", "plain-language-actionability"),
                release_gate_links=("legal-review-benchmark", "public_sampler"),
                evidence_paths=(
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "app/backend/services/legal_fixture_prompt_pack.py",
                    "docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md",
                    "docs/LEGAL_FIXTURE_PROMPT_PACK.md",
                ),
                impact=8,
                effort=5,
                confidence=7,
                cost_sensitivity=5,
                local_run_fit=6,
                next_actions=(
                    "Keep CUAD as a candidate source until license and attribution rules are documented.",
                    "Use synthetic service-agreement snippets for default local tests.",
                    "Add clause categories only after they map to output schema fields and smoke checks.",
                ),
            ),
            LegalResearchBacklogItem(
                id="research-backed-ui-review",
                title="Research-backed review visibility in UI",
                workstream="frontend_review",
                source_ids=("legalbench", "ragas"),
                user_need_ids=("traceable-legal-review", "plain-language-actionability"),
                release_gate_links=("frontend-typecheck", "report_quality_gate"),
                evidence_paths=(
                    "app/frontend/src/pages/DeepReportPage.tsx",
                    "app/frontend/src/lib/reportMapper.ts",
                    "docs/USER_NEEDS_RADAR.md",
                    "docs/DEEP_REVIEW_QUALITY_GATES.md",
                ),
                impact=8,
                effort=6,
                confidence=7,
                cost_sensitivity=3,
                local_run_fit=5,
                next_actions=(
                    "Expose missing citations, pending facts, and release blockers as scan-friendly reviewer fields.",
                    "Keep user-facing wording tied to deterministic report fields instead of freeform model prose.",
                    "Typecheck frontend report mappings whenever report schema changes.",
                ),
            ),
            LegalResearchBacklogItem(
                id="chinese-legal-benchmark-fixture-refresh",
                title="Chinese legal benchmark fixture refresh",
                workstream="benchmark_design",
                source_ids=("lexeval", "legalbench-rag", "casegen"),
                user_need_ids=("traceable-legal-review", "robust-extraction-quality", "plain-language-actionability"),
                release_gate_links=(
                    "user-need-benchmark-coverage",
                    "legal-document-benchmark-coverage",
                    "legal-rag-retrieval-diagnostics-gate",
                ),
                evidence_paths=(
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "app/backend/services/user_need_benchmark_coverage.py",
                    "app/backend/services/legal_benchmark_research_refresh.py",
                    "docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md",
                    "docs/USER_NEED_BENCHMARK_COVERAGE.md",
                ),
                impact=9,
                effort=5,
                confidence=8,
                cost_sensitivity=7,
                local_run_fit=9,
                next_actions=(
                    "Map LegalBench-RAG, LexEval, and CaseGen metadata to local synthetic fixture ids before any public sample import.",
                    "Keep zh-CN document checks laptop-safe and cheap-first by default.",
                    "Review license, attribution, jurisdiction, and privacy gates before copying external legal text.",
                ),
            ),
            LegalResearchBacklogItem(
                id="casegen-document-output-gates",
                title="CaseGen-inspired legal document output gates",
                workstream="document_generation",
                source_ids=("casegen", "lexeval"),
                user_need_ids=("plain-language-actionability", "traceable-legal-review"),
                release_gate_links=("legal-document-benchmark-suite", "legal-document-coverage-claim-policy"),
                evidence_paths=(
                    "app/backend/services/legal_document_benchmark_fixtures.py",
                    "app/backend/services/legal_document_benchmark_suite.py",
                    "app/backend/services/legal_document_coverage_claim_policy.py",
                    "docs/LEGAL_DOCUMENT_BENCHMARK_FIXTURES.md",
                    "docs/LEGAL_DOCUMENT_COVERAGE_CLAIM_POLICY.md",
                ),
                impact=8,
                effort=5,
                confidence=7,
                cost_sensitivity=5,
                local_run_fit=8,
                next_actions=(
                    "Keep generated-document checks split into classification, extraction, structure, citation, PII, and risk-label stages.",
                    "Use synthetic local fixtures for civil complaints, lawyer letters, settlement agreements, and legal opinions.",
                    "Block public document-generation benchmark claims unless reviewed run archives exist.",
                ),
            ),
        )

    def _workstream_plan(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        workstreams = sorted({item["workstream"] for item in items})
        return [
            {
                "workstream": workstream,
                "item_ids": [item["id"] for item in items if item["workstream"] == workstream],
                "top_priority_score": max(item["priority_score"] for item in items if item["workstream"] == workstream),
                "primary_release_gates": sorted(
                    {
                        gate
                        for item in items
                        if item["workstream"] == workstream
                        for gate in item["release_gate_links"]
                    }
                ),
            }
            for workstream in workstreams
        ]


def priority_score(
    *,
    impact: int,
    effort: int,
    confidence: int,
    cost_sensitivity: int,
    local_run_fit: int,
) -> int:
    raw = impact * confidence + cost_sensitivity * 3 + local_run_fit * 2 - effort * 4
    return max(0, min(100, raw))


def priority_band(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
