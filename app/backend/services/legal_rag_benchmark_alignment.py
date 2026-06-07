from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from services.legal_benchmark_fixture_crosswalk import LegalBenchmarkFixtureCrosswalkService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.legal_rag_abstention_escalation_gate import LegalRagAbstentionEscalationGateService
from services.legal_rag_retrieval_diagnostics_gate import LegalRagRetrievalDiagnosticsGateService


@dataclass(frozen=True)
class BenchmarkDimension:
    id: str
    title: str
    benchmark_signal_ids: tuple[str, ...]
    required_gate_ids: tuple[str, ...]
    required_validation_targets: tuple[str, ...]
    expected_local_fixture_ids: tuple[str, ...]
    cheap_first_policy: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["benchmark_signal_ids"] = list(self.benchmark_signal_ids)
        data["required_gate_ids"] = list(self.required_gate_ids)
        data["required_validation_targets"] = list(self.required_validation_targets)
        data["expected_local_fixture_ids"] = list(self.expected_local_fixture_ids)
        return data


class LegalRagBenchmarkAlignmentService:
    """Map public Legal RAG benchmark signals to local metadata-only gates."""

    def __init__(
        self,
        *,
        diagnostics_service: LegalRagRetrievalDiagnosticsGateService | None = None,
        abstention_service: LegalRagAbstentionEscalationGateService | None = None,
        sampler_service: LegalPublicBenchmarkSamplerService | None = None,
        crosswalk_service: LegalBenchmarkFixtureCrosswalkService | None = None,
    ) -> None:
        self.diagnostics_service = diagnostics_service or LegalRagRetrievalDiagnosticsGateService()
        self.abstention_service = abstention_service or LegalRagAbstentionEscalationGateService()
        self.sampler_service = sampler_service or LegalPublicBenchmarkSamplerService()
        self.crosswalk_service = crosswalk_service or LegalBenchmarkFixtureCrosswalkService()

    def build_scorecard(self) -> dict[str, Any]:
        diagnostics = self.diagnostics_service.build_gate()
        abstention = self.abstention_service.build_gate()
        sampler = self.sampler_service.build_plan()
        crosswalk = self.crosswalk_service.build_crosswalk()
        dimensions = self._dimensions()
        rows = [
            self._alignment_row(
                dimension,
                diagnostics=diagnostics,
                abstention=abstention,
                sampler=sampler,
                crosswalk=crosswalk,
            )
            for dimension in dimensions
        ]
        status_counts = Counter(row["alignment_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        blocked_rows = [row for row in rows if row["release_action"] == "block_claims"]
        review_rows = [row for row in rows if row["release_action"] == "maintainer_review"]

        return {
            "id": "legal-rag-benchmark-alignment",
            "title": "Legal RAG benchmark alignment scorecard",
            "status": "ready_with_blockers" if blocked_rows else ("ready_with_review" if review_rows else "ready"),
            "summary": {
                "dimension_count": len(rows),
                "aligned_count": status_counts.get("aligned", 0),
                "review_count": status_counts.get("review_required", 0),
                "gap_count": status_counts.get("gap", 0),
                "blocked_claim_count": len(blocked_rows),
                "maintainer_review_count": len(review_rows),
                "benchmark_signal_count": len(self._research_basis()),
                "diagnostic_row_count": diagnostics["summary"]["diagnostic_row_count"],
                "retrieval_blocked_row_count": diagnostics["summary"]["blocked_row_count"],
                "abstention_blocker_count": abstention["summary"]["blocker_count"],
                "public_sampler_source_count": sampler["summary"]["source_count"],
                "public_sampler_ready_source_count": sampler["summary"]["sampling_ready_source_count"],
                "fixture_crosswalk_gap_count": crosswalk["summary"]["gap_count"],
                "cheap_first_default": True,
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "raw_public_benchmark_text_included": False,
                "raw_query_included": False,
                "raw_retrieved_context_included": False,
                "raw_legal_text_included": False,
                "prompt_included": False,
                "model_output_included": False,
                "credentials_included": False,
            },
            "alignment_rows": rows,
            "alignment_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "benchmark_dimensions": [dimension.to_api() for dimension in dimensions],
            "linked_gate_summary": {
                "legal_rag_retrieval_diagnostics_gate": diagnostics["status"],
                "legal_rag_abstention_escalation_gate": abstention["status"],
                "legal_public_benchmark_sampler": sampler["status"],
                "legal_benchmark_fixture_crosswalk": crosswalk["status"],
                "retrieval_diagnostics_gate_id": diagnostics["id"],
                "abstention_gate_id": abstention["id"],
                "public_sampler_endpoint": "/api/v1/maintenance/legal-review-benchmark/public-sampler",
                "fixture_crosswalk_endpoint": "/api/v1/maintenance/legal-review-benchmark/fixture-crosswalk",
            },
            "research_basis": self._research_basis(),
            "claim_boundary": {
                "legal_advice_claimed": False,
                "legal_rag_quality_claimed": False,
                "public_benchmark_score_claimed": False,
                "leaderboard_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_client_delivery_claimed": False,
                "allowed_claims": [
                    "The repository maps public Legal RAG benchmark signals to local metadata-only release gates.",
                    "The scorecard links retrieval diagnostics, abstention escalation, public source sampling policy, and fixture crosswalk coverage.",
                ],
                "forbidden_claims": [
                    "Do not claim LegalBench-RAG, CRAG, Legal RAG Bench, RAGAS, or public benchmark scores.",
                    "Do not claim live retrieval accuracy, legal answer accuracy, or production quality from this scorecard.",
                    "Do not claim NewAPI/Gemini execution, public dataset downloads, or automatic client delivery.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_public_benchmark_text": False,
                "returns_raw_query": False,
                "returns_retrieved_context": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "returns_gateway_payloads": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_benchmark_alignment.py tests/test_legal_rag_retrieval_diagnostics_gate.py tests/test_legal_benchmark_fixture_crosswalk.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _alignment_row(
        self,
        dimension: BenchmarkDimension,
        *,
        diagnostics: dict[str, Any],
        abstention: dict[str, Any],
        sampler: dict[str, Any],
        crosswalk: dict[str, Any],
    ) -> dict[str, Any]:
        source_rows = {
            row["source_id"]: row
            for row in crosswalk.get("source_rows", [])
            if isinstance(row, dict)
        }
        sampler_rows = {
            row["source_id"]: row
            for row in sampler.get("source_plans", [])
            if isinstance(row, dict)
        }
        relevant_sources = self._relevant_sources(dimension, source_rows)
        observed_targets = self._observed_targets(relevant_sources)
        observed_fixtures = self._observed_fixtures(relevant_sources)
        missing_targets = [
            target
            for target in dimension.required_validation_targets
            if target not in observed_targets
        ]
        missing_fixtures = [
            fixture_id
            for fixture_id in dimension.expected_local_fixture_ids
            if fixture_id not in observed_fixtures
        ]
        source_states = {
            source_id: str(sampler_rows.get(source_id, {}).get("sampling_state") or "not_mapped")
            for source_id in dimension.benchmark_signal_ids
        }
        gate_statuses = self._gate_statuses(dimension, diagnostics, abstention)
        gap_reasons = self._gap_reasons(
            missing_targets=missing_targets,
            missing_fixtures=missing_fixtures,
            source_states=source_states,
            gate_statuses=gate_statuses,
            diagnostics=diagnostics,
            abstention=abstention,
        )
        alignment_status = self._alignment_status(gap_reasons)
        release_action = self._release_action(alignment_status)
        return {
            "id": dimension.id,
            "title": dimension.title,
            "benchmark_signal_ids": list(dimension.benchmark_signal_ids),
            "alignment_status": alignment_status,
            "release_action": release_action,
            "coverage_score": self._coverage_score(
                required_targets=dimension.required_validation_targets,
                observed_targets=observed_targets,
                required_fixtures=dimension.expected_local_fixture_ids,
                observed_fixtures=observed_fixtures,
            ),
            "required_gate_ids": list(dimension.required_gate_ids),
            "gate_statuses": gate_statuses,
            "required_validation_targets": list(dimension.required_validation_targets),
            "observed_validation_targets": sorted(observed_targets),
            "missing_validation_targets": missing_targets,
            "expected_local_fixture_ids": list(dimension.expected_local_fixture_ids),
            "observed_local_fixture_ids": sorted(observed_fixtures),
            "missing_local_fixture_ids": missing_fixtures,
            "public_source_sampling_states": source_states,
            "cheap_first_policy": dimension.cheap_first_policy,
            "starts_cheap": alignment_status != "gap",
            "premium_exception_allowed": False,
            "gap_reasons": gap_reasons,
            "linked_gate_ids": [
                *dimension.required_gate_ids,
                "legal-rag-benchmark-alignment",
                "legal-public-benchmark-sampler",
                "legal-benchmark-fixture-crosswalk",
            ],
            "privacy_boundary": self._row_privacy_boundary(),
        }

    def _relevant_sources(
        self,
        dimension: BenchmarkDimension,
        source_rows: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            source_rows[source_id]
            for source_id in dimension.benchmark_signal_ids
            if source_id in source_rows
        ]

    def _observed_targets(self, rows: list[dict[str, Any]]) -> set[str]:
        targets: set[str] = set()
        for row in rows:
            for target in row.get("validation_targets", []):
                targets.add(str(target))
        return targets

    def _observed_fixtures(self, rows: list[dict[str, Any]]) -> set[str]:
        fixture_ids: set[str] = set()
        for row in rows:
            for field in ("local_fixture_ids", "document_fixture_ids", "small_corpus_item_ids"):
                for fixture_id in row.get(field, []):
                    fixture_ids.add(str(fixture_id))
        return fixture_ids

    def _gate_statuses(
        self,
        dimension: BenchmarkDimension,
        diagnostics: dict[str, Any],
        abstention: dict[str, Any],
    ) -> dict[str, str]:
        statuses: dict[str, str] = {}
        for gate_id in dimension.required_gate_ids:
            if gate_id == diagnostics["id"]:
                statuses[gate_id] = diagnostics["status"]
            elif gate_id == abstention["id"]:
                statuses[gate_id] = abstention["status"]
            elif gate_id == "legal-rag-authority-citation-gate":
                statuses[gate_id] = str(diagnostics["linked_gate_summary"].get("authority_gate_id") or "linked")
            elif gate_id == "legal-rag-index-binding":
                statuses[gate_id] = "metadata_only"
            elif gate_id == "legal-benchmark-fixture-crosswalk":
                statuses[gate_id] = "ready"
            else:
                statuses[gate_id] = "linked"
        return statuses

    def _gap_reasons(
        self,
        *,
        missing_targets: list[str],
        missing_fixtures: list[str],
        source_states: dict[str, str],
        gate_statuses: dict[str, str],
        diagnostics: dict[str, Any],
        abstention: dict[str, Any],
    ) -> list[str]:
        reasons: list[str] = []
        if missing_targets:
            reasons.append("validation_target_gap")
        if missing_fixtures:
            reasons.append("local_fixture_gap")
        if any(state == "license_review_required" for state in source_states.values()):
            reasons.append("public_source_license_review_required")
        if any(state == "catalog_only" for state in source_states.values()):
            reasons.append("public_source_catalog_only")
        if diagnostics["summary"]["blocked_row_count"] > 0:
            reasons.append("retrieval_diagnostic_blockers_present")
        if abstention["summary"]["blocker_count"] > 0:
            reasons.append("abstention_blockers_present")
        if any("blocker" in status or "blocked" in status for status in gate_statuses.values()):
            reasons.append("linked_gate_blocker")
        return self._unique(reasons)

    def _alignment_status(self, gap_reasons: list[str]) -> str:
        hard_gaps = {
            "validation_target_gap",
            "local_fixture_gap",
            "retrieval_diagnostic_blockers_present",
            "abstention_blockers_present",
            "linked_gate_blocker",
        }
        if any(reason in hard_gaps for reason in gap_reasons):
            return "gap"
        if gap_reasons:
            return "review_required"
        return "aligned"

    def _release_action(self, alignment_status: str) -> str:
        if alignment_status == "aligned":
            return "allow_local_metadata_claim"
        if alignment_status == "review_required":
            return "maintainer_review"
        return "block_claims"

    def _coverage_score(
        self,
        *,
        required_targets: tuple[str, ...],
        observed_targets: set[str],
        required_fixtures: tuple[str, ...],
        observed_fixtures: set[str],
    ) -> int:
        target_count = len(required_targets)
        fixture_count = len(required_fixtures)
        covered_targets = sum(1 for item in required_targets if item in observed_targets)
        covered_fixtures = sum(1 for item in required_fixtures if item in observed_fixtures)
        total = max(1, target_count + fixture_count)
        return round(((covered_targets + covered_fixtures) / total) * 100)

    def _dimensions(self) -> tuple[BenchmarkDimension, ...]:
        return (
            BenchmarkDimension(
                id="legal-rag-source-coverage",
                title="Source coverage and citation grounding",
                benchmark_signal_ids=("legalbench-rag", "legalbench"),
                required_gate_ids=("legal-rag-retrieval-diagnostics-gate", "legal-rag-authority-citation-gate"),
                required_validation_targets=("citation_grounding", "context_relevance", "release_decision"),
                expected_local_fixture_ids=("fixture-low-text-pdf-page-small", "ldoc-evidence-catalog-mini"),
                cheap_first_policy="Start with metadata-only cheap-first retrieval diagnostics; block claims when source coverage is empty.",
            ),
            BenchmarkDimension(
                id="corrective-rag-abstention",
                title="Corrective retrieval and abstention routing",
                benchmark_signal_ids=("legalbench-rag", "pile-of-law"),
                required_gate_ids=("legal-rag-retrieval-diagnostics-gate", "legal-rag-abstention-escalation-gate"),
                required_validation_targets=("citation_grounding", "context_relevance", "release_decision"),
                expected_local_fixture_ids=("fixture-low-text-pdf-page-small", "ldoc-legal-opinion-mini"),
                cheap_first_policy="Use cheap-first checks for sufficient metadata and require operator review before any premium exception.",
            ),
            BenchmarkDimension(
                id="chinese-legal-rag-transfer",
                title="Chinese legal RAG and document-generation transfer",
                benchmark_signal_ids=("lexeval", "casegen"),
                required_gate_ids=("legal-rag-retrieval-diagnostics-gate", "legal-benchmark-fixture-crosswalk"),
                required_validation_targets=("field_coverage", "answer_relevance", "release_decision"),
                expected_local_fixture_ids=("fixture-lease-dispute-notice-small", "ldoc-legal-opinion-mini"),
                cheap_first_policy="Keep zh-CN legal task checks on laptop-safe fixtures before broadening Gemini/NewAPI defaults.",
            ),
            BenchmarkDimension(
                id="contract-rag-clause-grounding",
                title="Contract clause grounding and risk labels",
                benchmark_signal_ids=("cuad", "legalbench-rag"),
                required_gate_ids=("legal-rag-retrieval-diagnostics-gate", "legal-benchmark-fixture-crosswalk"),
                required_validation_targets=("risk_grounding", "citation_grounding", "field_coverage"),
                expected_local_fixture_ids=("fixture-service-agreement-small", "ldoc-contract-review-mini"),
                cheap_first_policy="Retain cheap-first contract review until fixture output shows missing clause or citation blockers.",
            ),
        )

    def _research_basis(self) -> list[dict[str, str]]:
        return [
            {
                "id": "legalbench-rag",
                "url": "https://arxiv.org/abs/2408.10343",
                "signal": "Legal RAG benchmarks should test retrieval, citation, and grounding rather than generated text alone.",
            },
            {
                "id": "crag",
                "url": "https://arxiv.org/abs/2401.15884",
                "signal": "Corrective RAG motivates routing low-confidence retrieval to verification or abstention paths.",
            },
            {
                "id": "ragas",
                "url": "https://arxiv.org/abs/2309.15217",
                "signal": "RAG evaluation should separate faithfulness, answer relevance, context precision, and context recall.",
            },
            {
                "id": "legal-rag-bench",
                "url": "https://arxiv.org/abs/2603.01710",
                "signal": "Legal RAG quality depends on retrieval quality and domain-specific grounded source selection.",
            },
        ]

    def _row_privacy_boundary(self) -> dict[str, bool]:
        return {
            "public_benchmark_text_returned": False,
            "raw_query_returned": False,
            "retrieved_context_returned": False,
            "raw_legal_text_returned": False,
            "prompt_returned": False,
            "model_output_returned": False,
            "credentials_returned": False,
        }

    def _recommended_actions(self, blocked_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]]) -> list[str]:
        if blocked_rows:
            return [
                "Keep public benchmark and Legal RAG quality claims blocked until local fixture gaps and retrieval blockers are closed.",
                "Resolve retrieval diagnostics and abstention blockers before promoting any Gemini/NewAPI cheap-first default for legal RAG.",
                "Keep public benchmark sources license-reviewed and metadata-only before importing samples.",
            ]
        if review_rows:
            return [
                "Review license-required or catalog-only source mappings before using them as release evidence.",
                "Keep scorecard rows linked to retrieval diagnostics and fixture crosswalk validation commands.",
            ]
        return [
            "Use this alignment scorecard before each Legal RAG, source-ingestion, or model-default release.",
            "Re-run the scorecard when public benchmark mappings, diagnostics, or fixture crosswalk coverage changes.",
        ]

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            safe = str(value or "").strip()
            if safe and safe not in seen:
                seen.add(safe)
                result.append(safe)
        return result
