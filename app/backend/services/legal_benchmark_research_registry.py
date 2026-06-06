from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LegalBenchmarkResearchSource:
    public_name: str
    public_link: str
    experience_takeaways: tuple[str, ...]
    project_mapping: dict[str, Any]
    low_resource_action: str
    forbidden_claims: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["experience_takeaways"] = list(self.experience_takeaways)
        data["forbidden_claims"] = list(self.forbidden_claims)
        return data


class LegalBenchmarkResearchRegistryService:
    """Map public legal AI benchmark lessons to local low-resource test strategy."""

    def build_registry(self) -> dict[str, Any]:
        sources = self._sources()
        forbidden_claims = self._forbidden_claims(sources)
        return {
            "status": "ready",
            "method": {
                "type": "local-legal-benchmark-research-registry",
                "notes": [
                    "Stores public benchmark names, public links, design takeaways, and local mappings only.",
                    "Default validation is metadata-only and synthetic-fixture based; it does not download benchmark data.",
                    "The registry is evidence for local test planning, not external benchmark performance.",
                ],
            },
            "summary": {
                "source_count": len(sources),
                "source_names": [source.public_name for source in sources],
                "low_resource_action_count": len({source.low_resource_action for source in sources}),
                "forbidden_claim_count": len(forbidden_claims),
            },
            "sources": [source.to_api() for source in sources],
            "low_resource_strategy": {
                "default_mode": "metadata_only_synthetic_fixtures",
                "network_access": "disabled_for_local_validation",
                "dataset_downloads": "forbidden_in_default_tests",
                "sensitive_data": "not_allowed",
                "fixture_cap": {
                    "default_sources": 3,
                    "default_fixtures_per_source": 2,
                    "max_fixtures_per_source_without_review": 3,
                },
                "actions": [source.low_resource_action for source in sources],
            },
            "allowed_claims": [
                "The registry maps public legal benchmark design patterns to local synthetic fixture planning.",
                "The registry is pure local metadata and does not contain benchmark samples, model outputs, or sensitive data.",
                "The recommended validation path is a low-resource smoke test, not a public leaderboard run.",
            ],
            "forbidden_claims": forbidden_claims,
            "validation_commands": self.validation_commands(),
            "privacy_note": (
                "This registry must not store benchmark raw text, private matter facts, real client documents, "
                "emails, API keys, model outputs, or customer identifiers."
            ),
        }

    def validation_commands(self) -> list[str]:
        return [
            "python -m pytest tests/test_legal_benchmark_research_registry.py -q",
            "python -m pytest tests/test_legal_public_benchmark_sampler.py tests/test_legal_external_research_digest.py -q",
        ]

    def _sources(self) -> tuple[LegalBenchmarkResearchSource, ...]:
        return (
            LegalBenchmarkResearchSource(
                public_name="LegalBench",
                public_link="https://arxiv.org/abs/2308.11462",
                experience_takeaways=(
                    "Legal AI evaluation should be split by legal task family instead of reduced to one generic score.",
                    "Task prompts, expected outputs, and scoring rubrics need stable schemas before comparing models.",
                    "Benchmark ideas can guide fixture coverage without copying public task text into the repository.",
                ),
                project_mapping={
                    "local_area": "legal_review_benchmark",
                    "fixture_focus": "issue spotting, rule application, citation grounding, and release-decision smoke checks",
                    "measurement": "expected signals, expected routes, unsupported-claim checks, and per-fixture pass/fail notes",
                },
                low_resource_action=(
                    "Use LegalBench as a task-family coverage reference; run two synthetic fixtures per selected "
                    "task family before any licensed public sample import is considered."
                ),
                forbidden_claims=(
                    "Do not claim a LegalBench score, leaderboard position, or benchmark parity from this registry.",
                    "Do not claim external adoption or production legal accuracy.",
                    "Do not claim real client document coverage or customer-data validation.",
                ),
            ),
            LegalBenchmarkResearchSource(
                public_name="LexGLUE",
                public_link="https://arxiv.org/abs/2110.00976",
                experience_takeaways=(
                    "Legal NLP evaluation should keep task labels, splits, and metrics explicit for classification-style work.",
                    "Case-law and statute-oriented tasks should be tested separately from contract review tasks.",
                    "Small label-focused checks can expose routing and schema drift before larger benchmark work.",
                ),
                project_mapping={
                    "local_area": "legal_fixture_quick_suite",
                    "fixture_focus": "classification-style matter triage, answer relevance, context relevance, and abstention checks",
                    "measurement": "label stability, normalized response fields, route choice, and release readiness signals",
                },
                low_resource_action=(
                    "Use LexGLUE as a label-discipline reference; keep local tests to label-only or tiny synthetic "
                    "classification fixtures with no public corpus download."
                ),
                forbidden_claims=(
                    "Do not claim a LexGLUE score or legal text classification benchmark result.",
                    "Do not claim production classification uplift or deployed legal quality gains.",
                    "Do not claim real customer data was used to validate legal labels.",
                ),
            ),
            LegalBenchmarkResearchSource(
                public_name="LegalBench-RAG",
                public_link="https://arxiv.org/abs/2408.10343",
                experience_takeaways=(
                    "Legal RAG should be evaluated through retrieval, grounding, and citation support instead of answer text alone.",
                    "Missing-authority and unsupported-claim cases should be visible as separate failure modes.",
                    "RAG benchmark ideas can guide local synthetic source-pair fixtures without importing retrieval corpora.",
                ),
                project_mapping={
                    "local_area": "legal_rag_failure_fixtures",
                    "fixture_focus": "retrieval grounding, citation support, missing authority, abstention, and selected-source validation",
                    "measurement": "source availability, citation-map coverage, abstention routing, unsupported-claim blocking, and release decision",
                },
                low_resource_action=(
                    "Use LegalBench-RAG as a legal RAG task reference; run synthetic source-pair and abstention fixtures "
                    "before any public retrieval context import is considered."
                ),
                forbidden_claims=(
                    "Do not claim a LegalBench-RAG score, legal RAG benchmark result, or retrieval benchmark parity.",
                    "Do not claim production legal RAG accuracy or hallucination elimination.",
                    "Do not claim external legal retrieval corpora or real client sources were evaluated.",
                ),
            ),
            LegalBenchmarkResearchSource(
                public_name="LexEval",
                public_link="https://arxiv.org/abs/2409.20288",
                experience_takeaways=(
                    "Chinese legal AI evaluation should keep cognition, reasoning, and generation task families explicit.",
                    "Jurisdiction and document-type assumptions should be separated from generic legal reasoning labels.",
                    "Chinese benchmark ideas should map to zh-CN synthetic fixtures before public examples are imported.",
                ),
                project_mapping={
                    "local_area": "user_need_benchmark_coverage",
                    "fixture_focus": "zh-CN legal document classification, evidence reasoning, citation grounding, and generation readiness",
                    "measurement": "document fixture ids, task-family links, public-source license state, and user-need coverage status",
                },
                low_resource_action=(
                    "Use LexEval as a Chinese legal task-family reference; keep validation on local zh-CN synthetic "
                    "document fixtures until source license and attribution review pass."
                ),
                forbidden_claims=(
                    "Do not claim a LexEval score, Chinese legal benchmark score, or jurisdiction-wide legal accuracy.",
                    "Do not claim production Chinese legal reasoning uplift.",
                    "Do not claim public benchmark examples or real Chinese client documents were imported.",
                ),
            ),
            LegalBenchmarkResearchSource(
                public_name="CaseGen",
                public_link="https://arxiv.org/abs/2502.17943",
                experience_takeaways=(
                    "Legal case document generation should be evaluated as staged classification, extraction, reasoning, and drafting.",
                    "Generated legal documents need structure, citation, PII exclusion, and risk-label checks before release claims.",
                    "Case-generation research should map to local output fixtures without copying benchmark case text.",
                ),
                project_mapping={
                    "local_area": "legal_document_benchmark_fixtures",
                    "fixture_focus": "civil complaint, lawyer letter, contract review, settlement agreement, and legal opinion output checks",
                    "measurement": "document structure, citation presence, risk labels, PII exclusion, and generated-document release gates",
                },
                low_resource_action=(
                    "Use CaseGen as a legal document generation task-shape reference; run local synthetic document "
                    "fixture checks before considering any reviewed public case text."
                ),
                forbidden_claims=(
                    "Do not claim a CaseGen score, public document generation benchmark result, or drafting parity.",
                    "Do not claim production drafting quality or lawyer-equivalent document generation.",
                    "Do not claim benchmark case text, generated legal documents, or client documents were imported.",
                ),
            ),
            LegalBenchmarkResearchSource(
                public_name="COLIEE",
                public_link="https://coliee.org/COLIEE2026/overview",
                experience_takeaways=(
                    "Legal information retrieval and entailment should be evaluated as separate steps.",
                    "Citation support, source availability, and abstention behavior matter for legal QA reliability.",
                    "Retrieval failures should be first-class fixtures rather than hidden in aggregate answer quality.",
                ),
                project_mapping={
                    "local_area": "legal_rag_evaluation",
                    "fixture_focus": "source retrieval, citation grounding, entailment-style support, missing-authority handling, and abstention",
                    "measurement": "retrieved-source presence, supported-claim checks, unsupported-claim blocking, and failure-mode notes",
                },
                low_resource_action=(
                    "Use COLIEE as a retrieval-and-entailment reference; run synthetic source-pair and missing-authority "
                    "fixtures locally without importing competition corpora."
                ),
                forbidden_claims=(
                    "Do not claim a COLIEE task score, retrieval rank, or entailment benchmark result.",
                    "Do not claim production retrieval effectiveness or production legal QA impact.",
                    "Do not claim client matters, real client data, or private legal corpora were evaluated.",
                ),
            ),
        )

    def _forbidden_claims(self, sources: tuple[LegalBenchmarkResearchSource, ...]) -> list[str]:
        claims: list[str] = [
            "Do not claim external adoption from this local registry.",
            "Do not claim production effects, production accuracy, or production quality gains.",
            "Do not claim real customer data, real client documents, or private client matters were used.",
        ]
        for source in sources:
            claims.extend(source.forbidden_claims)
        return sorted(dict.fromkeys(claims))
