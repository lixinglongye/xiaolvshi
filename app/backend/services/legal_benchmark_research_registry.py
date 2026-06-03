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
