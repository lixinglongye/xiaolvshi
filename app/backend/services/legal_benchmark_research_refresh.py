from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from services.legal_adoption_research_bridge import LegalAdoptionResearchBridgeService
from services.legal_benchmark_research_registry import LegalBenchmarkResearchRegistryService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService
from services.user_needs_radar import UserNeedsRadarService


@dataclass(frozen=True)
class BenchmarkRefreshSource:
    id: str
    title: str
    url: str
    source_type: str
    benchmark_signal: str
    local_interpretation: str
    import_policy: str

    def to_api(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkRefreshRow:
    id: str
    source_id: str
    product_area: str
    user_need_ids: tuple[str, ...]
    benchmark_signal: str
    local_validation_target: str
    local_evidence_paths: tuple[str, ...]
    validation_commands: tuple[str, ...]
    cheap_first_policy: str
    next_actions: tuple[str, ...]
    release_gate_links: tuple[str, ...]
    priority: int

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["user_need_ids"] = list(self.user_need_ids)
        data["local_evidence_paths"] = list(self.local_evidence_paths)
        data["validation_commands"] = list(self.validation_commands)
        data["next_actions"] = list(self.next_actions)
        data["release_gate_links"] = list(self.release_gate_links)
        data["cheap_first_relevant"] = "cheap" in self.cheap_first_policy.lower()
        data["dataset_download_required"] = False
        data["model_call_required"] = False
        data["public_score_claimed"] = False
        data["external_legal_text_included"] = False
        return data


class LegalBenchmarkResearchRefreshService:
    """Refresh legal benchmark lessons into local low-resource validation work."""

    def __init__(
        self,
        user_needs_service: UserNeedsRadarService | None = None,
        registry_service: LegalBenchmarkResearchRegistryService | None = None,
        adoption_bridge_service: LegalAdoptionResearchBridgeService | None = None,
        benchmark_coverage_service: UserNeedBenchmarkCoverageService | None = None,
    ) -> None:
        self.user_needs_service = user_needs_service or UserNeedsRadarService()
        self.registry_service = registry_service or LegalBenchmarkResearchRegistryService()
        self.adoption_bridge_service = adoption_bridge_service or LegalAdoptionResearchBridgeService()
        self.benchmark_coverage_service = benchmark_coverage_service or UserNeedBenchmarkCoverageService()

    def build_refresh(self) -> dict[str, Any]:
        sources = self._sources()
        rows = [row.to_api() for row in self._rows()]
        known_need_ids = {need["id"] for need in self.user_needs_service.build_radar()["needs"]}
        unmapped_need_ids = sorted(
            {
                need_id
                for row in rows
                for need_id in row["user_need_ids"]
                if need_id not in known_need_ids
            }
        )
        registry = self.registry_service.build_registry()
        adoption_bridge = self.adoption_bridge_service.build_bridge()
        benchmark_coverage = self.benchmark_coverage_service.build_coverage()
        user_need_rows = self._user_need_rows(rows, benchmark_coverage)
        validation_commands = self._validation_commands(rows)
        cheap_first_rows = [row for row in rows if row["cheap_first_relevant"]]
        retrieval_rows = [
            row for row in rows if row["product_area"] in {"legal_rag", "retrieval_entailment"}
        ]

        return {
            "status": "ready" if not unmapped_need_ids else "needs_mapping_review",
            "method": {
                "type": "legal-benchmark-research-refresh",
                "notes": [
                    "Maps public legal benchmark and cost-routing research signals to local validation work only.",
                    "Uses source metadata, existing user-need IDs, and repository evidence paths; it does not download datasets.",
                    "Keeps cheap-first Gemini/NewAPI routing as the default policy and escalates only fixture-backed failures.",
                ],
                "source_registry_status": registry["status"],
                "adoption_bridge_status": adoption_bridge["status"],
                "benchmark_coverage_status": benchmark_coverage["status"],
            },
            "summary": {
                "source_count": len(sources),
                "refresh_row_count": len(rows),
                "user_need_row_count": len(user_need_rows),
                "known_user_need_count": len(known_need_ids),
                "unmapped_need_count": len(unmapped_need_ids),
                "cheap_first_signal_count": len(cheap_first_rows),
                "retrieval_or_entailment_signal_count": len(retrieval_rows),
                "local_validation_command_count": len(validation_commands),
                "registry_source_count": registry["summary"]["source_count"],
                "adoption_bridge_action_count": adoption_bridge["summary"]["action_count"],
                "benchmark_coverage_high_priority_gap_count": benchmark_coverage["summary"]["high_priority_gap_count"],
                "dataset_downloaded": False,
                "network_called": False,
                "model_called": False,
                "public_benchmark_score_claimed": False,
                "external_legal_text_included": False,
                "secret_value_included": False,
            },
            "research_sources": [source.to_api() for source in sources],
            "refresh_rows": rows,
            "user_need_rows": user_need_rows,
            "unmapped_need_ids": unmapped_need_ids,
            "recommended_actions": self._recommended_actions(rows, user_need_rows, unmapped_need_ids),
            "privacy_boundary": {
                "returns_public_benchmark_text": False,
                "returns_dataset_samples": False,
                "returns_raw_legal_text": False,
                "returns_raw_model_output": False,
                "returns_user_feedback_text": False,
                "returns_credentials": False,
                "network_called": False,
                "model_called": False,
                "source": "metadata_only_public_source_registry_and_local_evidence_paths",
            },
            "claim_boundary": {
                "public_benchmark_scores_claimed": False,
                "leaderboard_rank_claimed": False,
                "production_accuracy_claimed": False,
                "external_dataset_download_claimed": False,
                "real_client_document_coverage_claimed": False,
                "automatic_model_improvement_claimed": False,
            },
            "validation_commands": validation_commands,
        }

    def _sources(self) -> tuple[BenchmarkRefreshSource, ...]:
        return (
            BenchmarkRefreshSource(
                id="legalbench",
                title="LegalBench legal reasoning benchmark",
                url="https://arxiv.org/abs/2308.11462",
                source_type="paper-benchmark",
                benchmark_signal="Multi-task legal reasoning coverage should be mapped by legal task family.",
                local_interpretation="Refresh local fixtures by task family, output schema, release gate, and unsupported-claim checks.",
                import_policy="Use source metadata only; no LegalBench task text or scores are imported by default.",
            ),
            BenchmarkRefreshSource(
                id="lexglue",
                title="LexGLUE legal language understanding benchmark",
                url="https://arxiv.org/abs/2110.00976",
                source_type="paper-benchmark",
                benchmark_signal="Classification-style legal NLP needs explicit label, split, and metric discipline.",
                local_interpretation="Keep matter-intake and quick-suite checks label-only before larger legal text imports.",
                import_policy="Use label taxonomy ideas only; no LexGLUE corpus text or scores are imported by default.",
            ),
            BenchmarkRefreshSource(
                id="coliee",
                title="COLIEE legal case retrieval and entailment",
                url="https://coliee.org/COLIEE2026/overview",
                source_type="competition-overview",
                benchmark_signal="Legal retrieval and legal entailment should be evaluated as separate steps.",
                local_interpretation="Refresh legal RAG fixtures for source retrieval, citation support, missing authority, and abstention.",
                import_policy="Use retrieval/entailment task structure only; no competition corpus text is imported by default.",
            ),
            BenchmarkRefreshSource(
                id="legalbench-rag",
                title="LegalBench-RAG legal retrieval benchmark",
                url="https://arxiv.org/abs/2408.10343",
                source_type="paper-benchmark",
                benchmark_signal="Legal RAG evaluation should separate retrieval, citation grounding, and answer support.",
                local_interpretation="Refresh legal RAG failure fixtures and selected-source validation around missing authority and unsupported claims.",
                import_policy="Use source metadata and task structure only; no retrieval context or public legal text is imported by default.",
            ),
            BenchmarkRefreshSource(
                id="lexeval",
                title="LexEval Chinese legal benchmark",
                url="https://arxiv.org/abs/2409.20288",
                source_type="paper-benchmark",
                benchmark_signal="Chinese legal evaluation should cover cognition, reasoning, and generation task families.",
                local_interpretation="Refresh zh-CN legal document fixtures and user-need mappings without importing public benchmark examples.",
                import_policy="Use Chinese task taxonomy ideas only; no LexEval corpus text or scores are imported by default.",
            ),
            BenchmarkRefreshSource(
                id="casegen",
                title="CaseGen legal case generation benchmark",
                url="https://arxiv.org/abs/2502.17943",
                source_type="paper-benchmark",
                benchmark_signal="Legal case generation benefits from staged classification, extraction, reasoning, and drafting checks.",
                local_interpretation="Refresh local generated-document fixture checks for structure, citation, PII exclusion, and risk labels.",
                import_policy="Use document-generation task shape only; no benchmark case text or generated public examples are imported by default.",
            ),
            BenchmarkRefreshSource(
                id="frugalgpt",
                title="FrugalGPT cost-quality cascade",
                url="https://arxiv.org/abs/2305.05176",
                source_type="paper-routing",
                benchmark_signal="Cheap-first model cascades can reduce cost when escalation is selective and measured.",
                local_interpretation="Keep Gemini/NewAPI routing cheap-first and escalate only documented legal fixture failures.",
                import_policy="Use routing strategy metadata only; no live gateway call is made by this refresh.",
            ),
        )

    def _rows(self) -> tuple[BenchmarkRefreshRow, ...]:
        return (
            BenchmarkRefreshRow(
                id="legalbench-task-family-refresh",
                source_id="legalbench",
                product_area="legal_benchmark",
                user_need_ids=("traceable-legal-review", "plain-language-actionability"),
                benchmark_signal="Task-family breadth, legal reasoning schemas, and unsupported-claim controls.",
                local_validation_target="/api/v1/maintenance/legal-review-benchmark/quick-suite",
                local_evidence_paths=(
                    "app/backend/services/legal_review_benchmark.py",
                    "app/backend/services/legal_document_benchmark_suite.py",
                    "app/backend/services/legal_document_coverage_claim_policy.py",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_review_benchmark.py tests/test_legal_document_benchmark_suite.py -q",
                    "python -m pytest tests/test_legal_document_coverage_claim_policy.py -q",
                ),
                cheap_first_policy="Use cheap Gemini-compatible models for smoke validation; escalate only if task-family fixtures fail.",
                next_actions=(
                    "Group synthetic fixtures by legal task family before any prompt or routing promotion.",
                    "Keep public benchmark score claims blocked unless separate licensed run archives exist.",
                    "Require unsupported-claim policy checks for broad legal-document coverage wording.",
                ),
                release_gate_links=("legal-review-benchmark", "legal-document-benchmark-suite"),
                priority=92,
            ),
            BenchmarkRefreshRow(
                id="lexglue-label-discipline-refresh",
                source_id="lexglue",
                product_area="classification_triage",
                user_need_ids=("robust-extraction-quality", "privacy-safe-upload"),
                benchmark_signal="Label stability, task splits, and classification metric discipline.",
                local_validation_target="/api/v1/maintenance/legal-review-benchmark/quick-suite",
                local_evidence_paths=(
                    "app/backend/services/legal_fixture_quick_suite.py",
                    "app/backend/services/matter_intake_readiness_policy.py",
                    "app/backend/services/legal_fixture_response_normalizer.py",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_fixture_quick_suite.py tests/test_legal_fixture_response_normalizer.py -q",
                    "python -m pytest tests/test_matter_intake_readiness_policy.py -q",
                ),
                cheap_first_policy="Keep label-only triage checks on cheap models; require review escalation for ambiguous labels.",
                next_actions=(
                    "Add label-only checks before importing any larger legal classification corpus.",
                    "Keep privacy-safe upload gates attached to classification fixture review.",
                    "Normalize response labels before comparing cheap-first model behavior.",
                ),
                release_gate_links=("legal-review-benchmark", "matter-intake-readiness-policy"),
                priority=83,
            ),
            BenchmarkRefreshRow(
                id="coliee-retrieval-entailment-refresh",
                source_id="coliee",
                product_area="legal_rag",
                user_need_ids=("traceable-legal-review", "prompt-injection-resilience"),
                benchmark_signal="Retrieval, entailment, citation support, and missing-authority handling.",
                local_validation_target="/api/v1/maintenance/legal-review-benchmark/rag-failure-fixtures",
                local_evidence_paths=(
                    "app/backend/services/legal_rag_failure_fixtures.py",
                    "app/backend/services/legal_rag_selected_source_validation.py",
                    "app/backend/services/deep_review_selected_source_binding.py",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_rag_failure_fixtures.py tests/test_maintenance_legal_rag_selected_source_validation_route.py -q",
                    "python -m pytest tests/test_deep_review_selected_source_binding.py -q",
                ),
                cheap_first_policy="Use cheap retrieval checks first; escalate answer generation only when source support is present.",
                next_actions=(
                    "Separate source retrieval failures from legal-answer generation failures.",
                    "Add missing-authority and abstention rows to every selected-source validation packet.",
                    "Keep public COLIEE corpus text out of local validation until license review passes.",
                ),
                release_gate_links=("legal-rag-selected-source-validation", "legal-review-benchmark"),
                priority=90,
            ),
            BenchmarkRefreshRow(
                id="legalbench-rag-grounding-refresh",
                source_id="legalbench-rag",
                product_area="legal_rag",
                user_need_ids=("traceable-legal-review", "prompt-injection-resilience"),
                benchmark_signal="Legal RAG retrieval, citation grounding, unsupported-claim, and abstention task structure.",
                local_validation_target="/api/v1/maintenance/legal-review-benchmark/rag-failure-fixtures",
                local_evidence_paths=(
                    "app/backend/services/legal_rag_failure_fixtures.py",
                    "app/backend/services/legal_rag_authority_citation_gate.py",
                    "app/backend/services/legal_rag_abstention_escalation_gate.py",
                    "app/backend/services/legal_rag_retrieval_diagnostics_gate.py",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_rag_failure_fixtures.py tests/test_legal_rag_authority_citation_gate.py -q",
                    "python -m pytest tests/test_legal_rag_abstention_escalation_gate.py tests/test_legal_rag_retrieval_diagnostics_gate.py -q",
                ),
                cheap_first_policy="Run cheap retrieval diagnostics first; escalate answer generation only after source support is reviewable.",
                next_actions=(
                    "Map each legal RAG fixture to retrieval, citation, abstention, and hallucination-triage gates.",
                    "Keep public retrieval contexts metadata-only until source license and privacy review pass.",
                    "Block broad legal grounding claims unless authority/citation and abstention gates pass.",
                ),
                release_gate_links=("legal-rag-authority-citation-gate", "legal-rag-abstention-escalation-gate"),
                priority=91,
            ),
            BenchmarkRefreshRow(
                id="lexeval-chinese-legal-task-refresh",
                source_id="lexeval",
                product_area="chinese_legal_workflow",
                user_need_ids=("traceable-legal-review", "robust-extraction-quality", "plain-language-actionability"),
                benchmark_signal="Chinese legal cognition, reasoning, and generation should be mapped to local zh-CN workflow fixtures.",
                local_validation_target="/api/v1/maintenance/legal-review-benchmark/document-coverage",
                local_evidence_paths=(
                    "app/backend/services/legal_document_benchmark_coverage.py",
                    "app/backend/services/user_need_benchmark_coverage.py",
                    "app/backend/services/legal_public_benchmark_sampler.py",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_document_benchmark_coverage.py tests/test_user_need_benchmark_coverage.py -q",
                    "python -m pytest tests/test_legal_public_benchmark_sampler.py tests/test_user_needs_radar.py -q",
                ),
                cheap_first_policy="Use cheap models for zh-CN smoke checks; require lawyer-review escalation for ambiguous legal reasoning.",
                next_actions=(
                    "Keep LexEval as metadata-only Chinese task-family coverage until license review passes.",
                    "Map zh-CN document fixture ids to user needs before claiming Chinese legal workflow coverage.",
                    "Use document coverage and public sampler rows before importing any public examples.",
                ),
                release_gate_links=("user-need-benchmark-coverage", "legal-document-benchmark-coverage"),
                priority=89,
            ),
            BenchmarkRefreshRow(
                id="casegen-document-generation-refresh",
                source_id="casegen",
                product_area="legal_document_generation",
                user_need_ids=("plain-language-actionability", "traceable-legal-review"),
                benchmark_signal="Staged legal case generation should validate document structure, citations, PII exclusion, and risk labels.",
                local_validation_target="/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                local_evidence_paths=(
                    "app/backend/services/legal_document_benchmark_fixtures.py",
                    "app/backend/services/legal_document_benchmark_suite.py",
                    "app/backend/services/legal_document_coverage_claim_policy.py",
                ),
                validation_commands=(
                    "python -m pytest tests/test_legal_document_benchmark_fixtures.py tests/test_legal_document_benchmark_suite.py -q",
                    "python -m pytest tests/test_legal_document_coverage_claim_policy.py -q",
                ),
                cheap_first_policy="Use cheap models for document-structure smoke checks; escalate final legal opinion review only after deterministic checks pass.",
                next_actions=(
                    "Keep local document generation checks on synthetic zh-CN fixtures.",
                    "Require PII exclusion and citation presence before any generated-document coverage claim.",
                    "Do not copy public benchmark case text into repository fixtures.",
                ),
                release_gate_links=("legal-document-benchmark-suite", "legal-document-coverage-claim-policy"),
                priority=87,
            ),
            BenchmarkRefreshRow(
                id="frugalgpt-cheap-first-cascade-refresh",
                source_id="frugalgpt",
                product_area="model_cost_ops",
                user_need_ids=("cheap-first-review-routing", "feedback-to-roadmap-loop"),
                benchmark_signal="Cost-quality cascades should default to cheap models and escalate selected failures.",
                local_validation_target="/api/v1/aihub/models/cheap-first-calibration",
                local_evidence_paths=(
                    "app/backend/services/gemini_newapi_cheap_first_calibration.py",
                    "app/backend/services/gemini_newapi_selector_replay.py",
                    "app/backend/services/model_ops_cheap_first_canary_plan.py",
                ),
                validation_commands=(
                    "python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py tests/test_gemini_newapi_selector_replay.py -q",
                    "python -m pytest tests/test_model_ops_cheap_first_canary_plan.py tests/test_model_ops_readiness.py -q",
                ),
                cheap_first_policy="Prefer cheap Gemini-compatible defaults; escalate only fixture-backed legal risk, OCR, or final-review failures.",
                next_actions=(
                    "Keep cheap-first calibration passing before promoting model defaults.",
                    "Attach selector replay and canary-plan evidence to every default-change review.",
                    "Collect feedback as category-level escalation tolerance, not raw legal text.",
                ),
                release_gate_links=("gemini-newapi-cheap-first-calibration", "cheap-first-canary-plan"),
                priority=95,
            ),
        )

    def _user_need_rows(
        self,
        rows: list[dict[str, Any]],
        benchmark_coverage: dict[str, Any],
    ) -> list[dict[str, Any]]:
        by_need: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            for need_id in row["user_need_ids"]:
                by_need[need_id].append(row)

        coverage_rows = {
            row["need_id"]: row
            for row in benchmark_coverage.get("coverage_rows", [])
            if isinstance(row, dict) and row.get("need_id")
        }
        result: list[dict[str, Any]] = []
        for need_id, mapped_rows in sorted(by_need.items()):
            coverage = coverage_rows.get(need_id, {})
            validation_commands = sorted(
                {
                    command
                    for row in mapped_rows
                    for command in row["validation_commands"]
                }
            )
            result.append(
                {
                    "need_id": need_id,
                    "refresh_row_ids": [row["id"] for row in mapped_rows],
                    "source_ids": sorted({row["source_id"] for row in mapped_rows}),
                    "product_areas": sorted({row["product_area"] for row in mapped_rows}),
                    "local_coverage_status": str(coverage.get("coverage_status") or "not_mapped"),
                    "public_benchmark_status": str(coverage.get("public_benchmark_status") or "not_mapped"),
                    "calibration_status": str(coverage.get("calibration_status") or "not_mapped"),
                    "cheap_first_relevant": any(row["cheap_first_relevant"] for row in mapped_rows),
                    "validation_commands": validation_commands,
                    "next_action": self._need_next_action(need_id, mapped_rows, coverage),
                }
            )
        return result

    def _need_next_action(
        self,
        need_id: str,
        mapped_rows: list[dict[str, Any]],
        coverage: dict[str, Any],
    ) -> str:
        if coverage.get("calibration_status") in {"warn", "fail"}:
            return f"Review cheap-first calibration before changing routing for {need_id}."
        if coverage.get("public_benchmark_status") == "license_review_required":
            return f"Keep {need_id} public benchmark work metadata-only until license review passes."
        if coverage.get("coverage_status") in {"covered", "partial"}:
            return f"Run mapped local validations before claiming refreshed coverage for {need_id}."
        return f"Add a synthetic fixture or backlog link before claiming benchmark coverage for {need_id}."

    def _validation_commands(self, rows: list[dict[str, Any]]) -> list[str]:
        commands = {
            "python -m pytest tests/test_legal_benchmark_research_refresh.py -q",
            "python -m pytest tests/test_legal_benchmark_research_registry.py tests/test_user_need_benchmark_coverage.py -q",
        }
        for row in rows:
            commands.update(row["validation_commands"])
        return sorted(commands)

    def _recommended_actions(
        self,
        rows: list[dict[str, Any]],
        user_need_rows: list[dict[str, Any]],
        unmapped_need_ids: list[str],
    ) -> list[str]:
        if unmapped_need_ids:
            return [
                "Map refresh rows to existing user need IDs before release review: "
                + ", ".join(unmapped_need_ids)
                + ".",
                "Do not create public benchmark claims until every research refresh row has local evidence paths.",
            ]
        top_rows = sorted(rows, key=lambda row: (-int(row["priority"]), row["id"]))[:3]
        actions = [
            "Run the cheap-first cascade refresh before changing Gemini/NewAPI defaults.",
            "Keep LegalBench, LexGLUE, LegalBench-RAG, LexEval, CaseGen, and COLIEE signals as metadata-only planning references until license review passes.",
            "Use local synthetic fixtures and selected-source validation before importing external legal benchmark text.",
        ]
        actions.extend(
            f"{row['source_id']}: {row['next_actions'][0]}"
            for row in top_rows
        )
        uncovered = [
            row["need_id"]
            for row in user_need_rows
            if row["local_coverage_status"] not in {"covered", "partial"}
        ]
        if uncovered:
            actions.append("Add local evidence before claiming benchmark refresh coverage for: " + ", ".join(uncovered) + ".")
        return actions
