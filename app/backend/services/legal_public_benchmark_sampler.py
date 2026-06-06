from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.legal_review_benchmark import LegalReviewBenchmarkService


DEFAULT_MAX_SAMPLES_PER_SOURCE = 2
MAX_LOCAL_SAMPLE_CHARS = 1200


@dataclass(frozen=True)
class PublicBenchmarkMapping:
    source_id: str
    priority: str
    resource_profile: str
    sample_strategy: str
    local_fixture_ids: tuple[str, ...]
    benchmark_case_ids: tuple[str, ...]
    validation_targets: tuple[str, ...]
    license_gate: str
    document_fixture_ids: tuple[str, ...] = ()

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["local_fixture_ids"] = list(self.local_fixture_ids)
        data["benchmark_case_ids"] = list(self.benchmark_case_ids)
        data["document_fixture_ids"] = list(self.document_fixture_ids)
        data["validation_targets"] = list(self.validation_targets)
        return data


class LegalPublicBenchmarkSamplerService:
    """Build a lightweight public legal benchmark sampling plan without downloading datasets."""

    def __init__(self) -> None:
        self.benchmark_service = LegalReviewBenchmarkService()

    def build_plan(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        config = config or {}
        suite = self.benchmark_service.build_suite()
        sources = suite["public_sources"]
        enabled_source_ids = self._enabled_source_ids(config, sources)
        max_samples = self._max_samples(config)
        license_reviews = config.get("license_reviews") if isinstance(config.get("license_reviews"), dict) else {}
        mappings = {mapping.source_id: mapping for mapping in self._mappings()}
        source_plans = [
            self._source_plan(source, mappings[source["id"]], max_samples, license_reviews)
            for source in sources
            if source["id"] in enabled_source_ids and source["id"] in mappings
        ]
        ready_sources = [item for item in source_plans if item["sampling_state"] == "sampling_ready"]
        review_required = [item for item in source_plans if item["sampling_state"] == "license_review_required"]
        catalog_only = [item for item in source_plans if item["sampling_state"] == "catalog_only"]
        return {
            "status": "ready",
            "method": {
                "type": "resource-capped-public-legal-benchmark-sampler",
                "notes": [
                    "The sampler returns source mappings and run limits only; it never downloads benchmark data.",
                    "Default local tests continue to use synthetic fixtures from /fixture-smoke.",
                    "External public benchmark examples require maintainer license, privacy, and attribution review before import.",
                ],
                "research_basis": [
                    {
                        "id": "legalbench",
                        "url": "https://arxiv.org/abs/2308.11462",
                        "use": "multi-task legal reasoning coverage",
                    },
                    {
                        "id": "cuad",
                        "url": "https://www.atticusprojectai.org/cuad",
                        "use": "contract clause extraction and review sampling",
                    },
                    {
                        "id": "lexglue",
                        "url": "https://huggingface.co/datasets/coastalcph/lex_glue",
                        "use": "legal text classification and CaseHOLD-style reasoning sampling",
                    },
                    {
                        "id": "pile-of-law",
                        "url": "https://arxiv.org/abs/2207.00220",
                        "use": "corpus-scale reference only unless a resource-controlled job is approved",
                    },
                    {
                        "id": "legalbench-rag",
                        "url": "https://arxiv.org/abs/2408.10343",
                        "use": "legal RAG retrieval, citation, and grounding task design",
                    },
                    {
                        "id": "lexeval",
                        "url": "https://arxiv.org/abs/2409.20288",
                        "use": "Chinese legal cognition, reasoning, and generation coverage planning",
                    },
                    {
                        "id": "casegen",
                        "url": "https://arxiv.org/abs/2502.17943",
                        "use": "multi-stage legal case document generation fixture planning",
                    },
                ],
            },
            "summary": {
                "source_count": len(source_plans),
                "sampling_ready_source_count": len(ready_sources),
                "license_review_required_source_count": len(review_required),
                "catalog_only_source_count": len(catalog_only),
                "local_fixture_count": suite["document_fixture_count"],
                "benchmark_case_count": suite["case_count"],
                "max_samples_per_source": max_samples,
                "max_local_sample_chars": MAX_LOCAL_SAMPLE_CHARS,
            },
            "source_plans": source_plans,
            "sampling_batches": self._sampling_batches(source_plans),
            "resource_policy": {
                "default_mode": "metadata_plan_only",
                "network_access": "disabled_by_default",
                "max_samples_per_source": max_samples,
                "max_local_sample_chars": MAX_LOCAL_SAMPLE_CHARS,
                "storage_policy": "Store only source IDs, task labels, normalized observations, and attribution notes unless license review explicitly permits snippets.",
            },
            "validation_commands": [
                "python -m pytest tests/test_legal_public_benchmark_sampler.py tests/test_legal_review_benchmark.py -q",
                "python -m pytest tests/test_legal_fixture_evidence_bundle.py tests/test_release_readiness.py tests/test_maintenance_evidence.py -q",
            ],
            "recommended_actions": self._recommended_actions(source_plans),
            "privacy_note": (
                "Do not import raw public benchmark examples, contracts, court texts, personal data, emails, "
                "gateway keys, or model outputs through this sampler. Review license and attribution first."
            ),
        }

    def _enabled_source_ids(self, config: dict[str, Any], sources: list[dict[str, Any]]) -> set[str]:
        requested = config.get("enabled_source_ids")
        known_ids = {str(source["id"]) for source in sources}
        if not isinstance(requested, list) or not requested:
            return known_ids
        return {str(item) for item in requested if str(item) in known_ids}

    def _max_samples(self, config: dict[str, Any]) -> int:
        value = config.get("max_samples_per_source", DEFAULT_MAX_SAMPLES_PER_SOURCE)
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return DEFAULT_MAX_SAMPLES_PER_SOURCE
        return max(1, min(5, parsed))

    def _source_plan(
        self,
        source: dict[str, Any],
        mapping: PublicBenchmarkMapping,
        max_samples: int,
        license_reviews: dict[str, Any],
    ) -> dict[str, Any]:
        license_state = str(license_reviews.get(source["id"]) or "not_reviewed").strip().lower()
        if mapping.resource_profile == "corpus_scale":
            sampling_state = "catalog_only"
        elif license_state in {"pass", "approved", "ok"}:
            sampling_state = "sampling_ready"
        else:
            sampling_state = "license_review_required"
        return {
            **mapping.to_api(),
            "title": source["title"],
            "url": source["url"],
            "source_type": source["source_type"],
            "task_fit": source["task_fit"],
            "source_license_note": source["license_note"],
            "source_size_note": source["size_note"],
            "sampling_state": sampling_state,
            "max_samples": 0 if sampling_state == "catalog_only" else max_samples,
            "max_sample_chars": MAX_LOCAL_SAMPLE_CHARS,
            "download_policy": "do_not_download_in_default_local_tests",
            "recommended_action": self._source_action(sampling_state, mapping),
        }

    def _source_action(self, sampling_state: str, mapping: PublicBenchmarkMapping) -> str:
        if sampling_state == "sampling_ready":
            return f"Sample up to the configured cap and map observations to {', '.join(mapping.validation_targets)}."
        if sampling_state == "catalog_only":
            return "Keep as corpus-scale reference; use synthetic local fixtures or a separately approved resource-controlled job."
        return f"Complete license, attribution, and privacy review before sampling {mapping.source_id}."

    def _sampling_batches(self, source_plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "id": "contract_clause_smoke",
                "source_ids": [item["source_id"] for item in source_plans if item["source_id"] == "cuad"],
                "local_fixture_ids": ["fixture-service-agreement-small"],
                "target_endpoint": "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
                "run_condition": "Run only after CUAD license review is approved; keep sample count capped.",
            },
            {
                "id": "legal_reasoning_smoke",
                "source_ids": [item["source_id"] for item in source_plans if item["source_id"] in {"legalbench", "lexglue"}],
                "local_fixture_ids": ["fixture-lease-dispute-notice-small", "fixture-adversarial-upload-small"],
                "target_endpoint": "/api/v1/maintenance/legal-review-benchmark",
                "run_condition": "Run as small label-only or metadata-only samples before any raw text import.",
            },
            {
                "id": "legal_rag_grounding_smoke",
                "source_ids": [
                    item["source_id"]
                    for item in source_plans
                    if item["source_id"] in {"legalbench-rag", "pile-of-law"}
                ],
                "local_fixture_ids": ["fixture-low-text-pdf-page-small"],
                "document_fixture_ids": ["ldoc-evidence-catalog-mini", "ldoc-legal-opinion-mini"],
                "target_endpoint": "/api/v1/maintenance/legal-review-benchmark/rag-failure-fixtures",
                "run_condition": "Run only with synthetic source/citation fixtures until legal RAG source licenses pass review.",
            },
            {
                "id": "chinese_legal_document_generation_smoke",
                "source_ids": [
                    item["source_id"]
                    for item in source_plans
                    if item["source_id"] in {"lexeval", "casegen"}
                ],
                "local_fixture_ids": ["fixture-lease-dispute-notice-small", "fixture-service-agreement-small"],
                "document_fixture_ids": [
                    "ldoc-civil-complaint-mini",
                    "ldoc-lawyer-letter-mini",
                    "ldoc-contract-review-mini",
                    "ldoc-settlement-agreement-mini",
                    "ldoc-legal-opinion-mini",
                ],
                "target_endpoint": "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                "run_condition": "Run on synthetic zh-CN document fixtures; do not import public benchmark raw case text.",
            },
            {
                "id": "corpus_reference_only",
                "source_ids": [item["source_id"] for item in source_plans if item["resource_profile"] == "corpus_scale"],
                "local_fixture_ids": ["fixture-low-text-pdf-page-small"],
                "target_endpoint": "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
                "run_condition": "Do not run locally; use only as design reference for future retrieval stress tests.",
            },
        ]

    def _recommended_actions(self, source_plans: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Keep default laptop tests on synthetic fixtures; use public sources only for capped, reviewed samples.",
            "Record source ID, subset/task name, license note, and attribution before importing any example.",
        ]
        if any(item["sampling_state"] == "license_review_required" for item in source_plans):
            actions.append("Complete source-level license and attribution review before enabling public benchmark samples.")
        if any(item["sampling_state"] == "catalog_only" for item in source_plans):
            actions.append("Keep corpus-scale sources catalog-only unless a resource-controlled CI job is approved.")
        return actions

    def _mappings(self) -> tuple[PublicBenchmarkMapping, ...]:
        return (
            PublicBenchmarkMapping(
                source_id="legalbench",
                priority="high",
                resource_profile="small_task_sampling",
                sample_strategy="Select tiny task-family samples for issue spotting, rule application, and evidence reasoning.",
                local_fixture_ids=("fixture-lease-dispute-notice-small", "fixture-adversarial-upload-small"),
                benchmark_case_ids=("lease-dispute-evidence", "instruction-injection-upload", "legal-rag-grounding"),
                validation_targets=("citation_grounding", "evidence_plan", "release_decision"),
                license_gate="source_task_license_and_attribution_required",
            ),
            PublicBenchmarkMapping(
                source_id="cuad",
                priority="high",
                resource_profile="contract_clause_sampling",
                sample_strategy="Use a tiny number of clause-label examples to compare against synthetic contract-risk fixtures.",
                local_fixture_ids=("fixture-service-agreement-small",),
                benchmark_case_ids=("service-contract-risk",),
                validation_targets=("field_coverage", "risk_grounding", "cost_route"),
                license_gate="cuad_terms_review_required_before_copying_contract_text",
            ),
            PublicBenchmarkMapping(
                source_id="lexglue",
                priority="medium",
                resource_profile="classification_sampling",
                sample_strategy="Use label-only or tiny CaseHOLD-style samples for classification and legal reasoning smoke checks.",
                local_fixture_ids=("fixture-lease-dispute-notice-small", "fixture-adversarial-upload-small"),
                benchmark_case_ids=("lease-dispute-evidence", "instruction-injection-upload"),
                validation_targets=("answer_relevance", "context_relevance", "release_decision"),
                license_gate="subset_license_and_attribution_required",
            ),
            PublicBenchmarkMapping(
                source_id="pile-of-law",
                priority="low",
                resource_profile="corpus_scale",
                sample_strategy="Use as a design reference for future retrieval stress tests; do not import into local runs.",
                local_fixture_ids=("fixture-low-text-pdf-page-small",),
                benchmark_case_ids=("long-pdf-extraction", "legal-rag-grounding"),
                validation_targets=("extraction_quality", "context_relevance", "citation_grounding"),
                license_gate="source_specific_license_privacy_and_resource_review_required",
            ),
            PublicBenchmarkMapping(
                source_id="legalbench-rag",
                priority="high",
                resource_profile="legal_rag_sampling",
                sample_strategy="Use tiny retrieval-grounding task metadata to compare against synthetic citation and abstention fixtures.",
                local_fixture_ids=("fixture-low-text-pdf-page-small",),
                benchmark_case_ids=("legal-rag-grounding", "long-pdf-extraction"),
                validation_targets=("citation_grounding", "context_relevance", "release_decision"),
                license_gate="legal_rag_source_license_and_context_privacy_review_required",
                document_fixture_ids=("ldoc-evidence-catalog-mini", "ldoc-legal-opinion-mini"),
            ),
            PublicBenchmarkMapping(
                source_id="lexeval",
                priority="high",
                resource_profile="chinese_legal_task_sampling",
                sample_strategy="Use Chinese legal task taxonomy as metadata for local zh-CN classification and generation fixtures.",
                local_fixture_ids=("fixture-lease-dispute-notice-small", "fixture-adversarial-upload-small"),
                benchmark_case_ids=("lease-dispute-evidence", "instruction-injection-upload", "legal-rag-grounding"),
                validation_targets=("field_coverage", "answer_relevance", "release_decision"),
                license_gate="lexeval_license_attribution_and_jurisdiction_review_required",
                document_fixture_ids=(
                    "ldoc-civil-complaint-mini",
                    "ldoc-lawyer-letter-mini",
                    "ldoc-contract-review-mini",
                    "ldoc-legal-opinion-mini",
                ),
            ),
            PublicBenchmarkMapping(
                source_id="casegen",
                priority="medium",
                resource_profile="legal_document_generation_sampling",
                sample_strategy="Use multi-stage legal case document generation tasks as a planning reference for synthetic output fixtures.",
                local_fixture_ids=("fixture-service-agreement-small", "fixture-lease-dispute-notice-small"),
                benchmark_case_ids=("service-contract-risk", "lease-dispute-evidence"),
                validation_targets=("document_structure", "citation_presence", "risk_labeling"),
                license_gate="casegen_license_attribution_and_generated_text_review_required",
                document_fixture_ids=(
                    "ldoc-civil-complaint-mini",
                    "ldoc-lawyer-letter-mini",
                    "ldoc-settlement-agreement-mini",
                    "ldoc-legal-opinion-mini",
                ),
            ),
        )
