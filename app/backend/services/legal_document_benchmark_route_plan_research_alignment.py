from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.legal_document_benchmark_route_plan_replay import (
    LegalDocumentBenchmarkRoutePlanReplayService,
)


ALIGNMENT_ID = "legal-document-benchmark-route-plan-research-alignment"


@dataclass(frozen=True)
class RoutePlanResearchSource:
    id: str
    title: str
    url: str
    source_type: str
    signal: str
    local_interpretation: str

    def to_api(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RoutePlanAlignmentDimension:
    id: str
    title: str
    source_ids: tuple[str, ...]
    scenario_ids: tuple[str, ...]
    user_need_ids: tuple[str, ...]
    route_requirement: str
    release_gate_links: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_ids"] = list(self.source_ids)
        data["scenario_ids"] = list(self.scenario_ids)
        data["user_need_ids"] = list(self.user_need_ids)
        data["release_gate_links"] = list(self.release_gate_links)
        return data


class LegalDocumentBenchmarkRoutePlanResearchAlignmentService:
    """Map public research/source signals to local route-plan replay evidence."""

    def __init__(self, replay_service: LegalDocumentBenchmarkRoutePlanReplayService | None = None) -> None:
        self.replay_service = replay_service or LegalDocumentBenchmarkRoutePlanReplayService()

    def build_alignment(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        replay = self.replay_service.run_replay(data.get("route_plan_replay") if "route_plan_replay" in data else data)
        sources = self._sources()
        dimensions = self._dimensions()
        replay_results = {
            str(result.get("id") or ""): result
            for result in replay.get("replay_results", [])
            if isinstance(result, dict)
        }
        rows = [self._alignment_row(dimension, replay_results) for dimension in dimensions]
        failed_rows = [row for row in rows if row["alignment_status"] == "gap"]
        review_rows = [row for row in rows if row["alignment_status"] == "review_required"]
        checks = self._checks(replay, rows, sources)
        blocking_check_ids = [check["id"] for check in checks if check["status"] == "fail"]
        warning_check_ids = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking_check_ids or failed_rows else ("ready_with_review" if warning_check_ids or review_rows else "ready")

        return {
            "id": ALIGNMENT_ID,
            "title": "Legal document benchmark route-plan research alignment",
            "status": status,
            "method": {
                "type": ALIGNMENT_ID,
                "version": "2026-06-10",
                "notes": [
                    "Maps public research and official model-source signals to local route-plan replay scenarios.",
                    "Uses stored source URLs and deterministic replay metadata only; it does not browse, download datasets, or call models at runtime.",
                    "Blocks research-alignment claims when route-plan replay scenarios drift from cheap-first expectations.",
                ],
            },
            "summary": {
                "source_count": len(sources),
                "dimension_count": len(rows),
                "aligned_count": sum(1 for row in rows if row["alignment_status"] == "aligned"),
                "review_count": len(review_rows),
                "gap_count": len(failed_rows),
                "route_plan_replay_status": replay["status"],
                "replay_scenario_count": replay["summary"]["scenario_count"],
                "replay_failed_count": replay["summary"]["fail_count"],
                "premium_block_count": replay["summary"]["premium_block_count"],
                "routed_to_recommended_count": replay["summary"]["routed_to_recommended_count"],
                "rejected_sensitive_scenario_count": replay["summary"]["rejected_sensitive_scenario_count"],
                "official_model_source_count": sum(1 for source in sources if source.source_type == "official-model-doc"),
                "paper_source_count": sum(1 for source in sources if source.source_type == "paper-benchmark"),
                "model_calls": "not_required",
                "network_access": "disabled",
                "dataset_downloaded": False,
                "raw_public_benchmark_text_returned": False,
                "raw_fixture_snippets_returned": False,
                "raw_outputs_returned": False,
            },
            "source_anchors": [source.to_api() for source in sources],
            "source_urls": [source.url for source in sources],
            "alignment_dimensions": [dimension.to_api() for dimension in dimensions],
            "alignment_rows": rows,
            "checks": checks,
            "blocking_check_ids": blocking_check_ids,
            "warning_check_ids": warning_check_ids,
            "linked_replay_summary": {
                "id": replay["id"],
                "status": replay["status"],
                "scenario_count": replay["summary"]["scenario_count"],
                "fail_count": replay["summary"]["fail_count"],
                "premium_block_count": replay["summary"]["premium_block_count"],
                "routed_to_recommended_count": replay["summary"]["routed_to_recommended_count"],
            },
            "recommended_actions": self._recommended_actions(status, rows),
            "privacy_boundary": {
                "metadata_only": True,
                "source_urls_returned": True,
                "returns_public_benchmark_text": False,
                "returns_raw_fixture_snippets": False,
                "returns_raw_scenario_payload": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "calls_model": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "paper_reproduction_claimed": False,
                "official_source_refresh_completed": False,
                "production_accuracy_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "allowed_claim": (
                    "Local route-plan replay scenarios are mapped to stored public research and model-source anchors."
                ),
                "forbidden_claims": [
                    "Do not claim LegalBench-RAG, LexEval, FrugalGPT, or Gemini official benchmark results.",
                    "Do not claim live model execution, production legal quality, public benchmark scores, or official source refresh.",
                ],
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_research_alignment.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_replay.py tests/test_legal_document_benchmark_route_plan.py -q",
            ],
        }

    def _alignment_row(
        self,
        dimension: RoutePlanAlignmentDimension,
        replay_results: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        scenario_results = [replay_results.get(scenario_id) for scenario_id in dimension.scenario_ids]
        missing_scenarios = [
            scenario_id
            for scenario_id, result in zip(dimension.scenario_ids, scenario_results)
            if result is None
        ]
        failed_scenarios = [
            str(result.get("id"))
            for result in scenario_results
            if isinstance(result, dict) and result.get("status") != "pass"
        ]
        observed_models = [
            str(result.get("actual", {}).get("resolved_model"))
            for result in scenario_results
            if isinstance(result, dict) and result.get("actual", {}).get("resolved_model")
        ]
        observed_route_bands = [
            str(result.get("actual", {}).get("route_band"))
            for result in scenario_results
            if isinstance(result, dict) and result.get("actual", {}).get("route_band")
        ]
        gap_reasons = []
        if missing_scenarios:
            gap_reasons.append("missing_replay_scenarios")
        if failed_scenarios:
            gap_reasons.append("failed_replay_scenarios")
        if dimension.id == "premium-cascade-and-block" and not self._has_premium_cascade(replay_results):
            gap_reasons.append("premium_cascade_or_block_missing")
        if dimension.id == "grounded-legal-opinion-route" and "gemini-3.1-flash-lite" not in observed_models:
            gap_reasons.append("grounded_flash_lite_route_missing")
        alignment_status = "gap" if failed_scenarios else ("review_required" if missing_scenarios or gap_reasons else "aligned")
        return {
            "id": dimension.id,
            "title": dimension.title,
            "source_ids": list(dimension.source_ids),
            "scenario_ids": list(dimension.scenario_ids),
            "user_need_ids": list(dimension.user_need_ids),
            "release_gate_links": list(dimension.release_gate_links),
            "alignment_status": alignment_status,
            "release_action": "block_claims" if alignment_status == "gap" else "maintainer_review" if alignment_status == "review_required" else "allow_metadata_claim",
            "route_requirement": dimension.route_requirement,
            "observed_models": observed_models,
            "observed_route_bands": observed_route_bands,
            "missing_scenario_ids": missing_scenarios,
            "failed_scenario_ids": failed_scenarios,
            "gap_reasons": gap_reasons,
            "metadata_only": True,
            "recommended_action": self._row_action(alignment_status, dimension),
        }

    def _checks(
        self,
        replay: dict[str, Any],
        rows: list[dict[str, Any]],
        sources: tuple[RoutePlanResearchSource, ...],
    ) -> list[dict[str, Any]]:
        source_ids = {source.id for source in sources}
        return [
            self._check(
                "route-plan-replay-ready",
                "pass" if replay["status"] == "pass" else "fail",
                "Route-plan replay must pass before research alignment can support release evidence.",
            ),
            self._check(
                "gemini-official-source-anchors-present",
                "pass" if {"google-gemini-models", "google-gemini-pricing"} <= source_ids else "fail",
                "Gemini route claims must remain linked to stored official model and pricing source URLs.",
            ),
            self._check(
                "legalbench-rag-grounded-route-covered",
                "pass"
                if any(row["id"] == "grounded-legal-opinion-route" and row["alignment_status"] == "aligned" for row in rows)
                else "fail",
                "LegalBench-RAG style grounding signals should map to the grounded legal-opinion route.",
            ),
            self._check(
                "lexeval-zh-cn-document-family-covered",
                "pass"
                if any(row["id"] == "zh-cn-document-task-family" and row["alignment_status"] == "aligned" for row in rows)
                else "warn",
                "LexEval style Chinese legal task-family coverage should map to local synthetic document routes.",
            ),
            self._check(
                "metadata-only-boundary",
                "pass",
                "Research alignment returns source URLs, route metadata, checks, and counts only.",
            ),
        ]

    def _check(self, check_id: str, status: str, reason: str) -> dict[str, str]:
        return {"id": check_id, "status": status, "reason": reason}

    def _has_premium_cascade(self, replay_results: dict[str, dict[str, Any]]) -> bool:
        routed = replay_results.get("unapproved-premium-routes-to-recommended", {})
        blocked = replay_results.get("approved-premium-remains-blocked", {})
        return (
            routed.get("status") == "pass"
            and routed.get("actual", {}).get("routed_to_recommended_model") is True
            and blocked.get("status") == "pass"
            and "no-premium-primary-defaults" in blocked.get("actual", {}).get("blocking_check_ids", [])
        )

    def _row_action(self, status: str, dimension: RoutePlanAlignmentDimension) -> str:
        if status == "gap":
            return f"Block research-alignment claims for {dimension.id} until replay scenarios pass."
        if status == "review_required":
            return f"Review missing route-plan replay coverage before citing {dimension.id} as aligned."
        return "Keep this source mapping as metadata-only release evidence."

    def _recommended_actions(self, status: str, rows: list[dict[str, Any]]) -> list[str]:
        if status == "blocked":
            return [
                "Fix failing route-plan replay scenarios before citing research alignment in release evidence.",
                "Keep public benchmark and official-source claims metadata-only until replay and source review pass.",
            ]
        return [
            "Use this alignment after route-plan replay and before any public benchmark or default-promotion claim.",
            "Keep LegalBench-RAG and LexEval as task-shape references only until license and sampling review pass.",
        ]

    def _sources(self) -> tuple[RoutePlanResearchSource, ...]:
        return (
            RoutePlanResearchSource(
                id="google-gemini-models",
                title="Google Gemini API model documentation",
                url="https://ai.google.dev/gemini-api/docs/models",
                source_type="official-model-doc",
                signal="Gemini model-family and capability metadata should be reviewed before default route claims.",
                local_interpretation="Keep Flash-Lite and Flash route claims linked to official model documentation.",
            ),
            RoutePlanResearchSource(
                id="google-gemini-pricing",
                title="Google Gemini API pricing documentation",
                url="https://ai.google.dev/gemini-api/docs/pricing",
                source_type="official-model-doc",
                signal="Cheap-first routing needs explicit pricing-source anchors before cost claims.",
                local_interpretation="Treat local catalog costs as review metadata until official price refresh is completed.",
            ),
            RoutePlanResearchSource(
                id="frugalgpt",
                title="FrugalGPT cost-quality cascade",
                url="https://arxiv.org/abs/2305.05176",
                source_type="paper-routing",
                signal="Cheap-first cascades should use low-cost models first and escalate selectively.",
                local_interpretation="Map unapproved premium requests to recommended budgeted routes and block premium defaults.",
            ),
            RoutePlanResearchSource(
                id="legalbench-rag",
                title="LegalBench-RAG legal retrieval benchmark",
                url="https://arxiv.org/abs/2408.10343",
                source_type="paper-benchmark",
                signal="Legal RAG work should separate retrieval, citation grounding, and answer support.",
                local_interpretation="Keep legal-opinion route evidence grounded and separate from public benchmark score claims.",
            ),
            RoutePlanResearchSource(
                id="lexeval",
                title="LexEval Chinese legal benchmark",
                url="https://arxiv.org/abs/2409.20288",
                source_type="paper-benchmark",
                signal="Chinese legal evaluation should cover cognition, reasoning, and generation task families.",
                local_interpretation="Map zh-CN legal-document tasks to local synthetic document route families only.",
            ),
        )

    def _dimensions(self) -> tuple[RoutePlanAlignmentDimension, ...]:
        return (
            RoutePlanAlignmentDimension(
                id="gemini-cheap-first-source-routing",
                title="Gemini official source anchored cheap-first routes",
                source_ids=("google-gemini-models", "google-gemini-pricing"),
                scenario_ids=("contract-review-default-balanced", "evidence-catalog-default-flash-lite"),
                user_need_ids=("gemini-cheap-first-routing", "low-resource-testing"),
                route_requirement="Routine route-plan scenarios start with Flash-Lite or Flash metadata before premium routes.",
                release_gate_links=("legal-document-benchmark-route-plan-replay", "modelops-gemini-official-cheap-first-source-review"),
            ),
            RoutePlanAlignmentDimension(
                id="premium-cascade-and-block",
                title="FrugalGPT-style premium cascade and block",
                source_ids=("frugalgpt",),
                scenario_ids=("unapproved-premium-routes-to-recommended", "approved-premium-remains-blocked"),
                user_need_ids=("gemini-cheap-first-routing", "reviewer-visibility"),
                route_requirement="Unapproved premium requests route down; approved premium primary routes remain blocked for local smoke runs.",
                release_gate_links=("legal-document-benchmark-route-plan-replay", "model-cost-guardrails"),
            ),
            RoutePlanAlignmentDimension(
                id="grounded-legal-opinion-route",
                title="LegalBench-RAG-style grounded legal-opinion route",
                source_ids=("legalbench-rag",),
                scenario_ids=("legal-opinion-grounded-flash-lite",),
                user_need_ids=("grounded-legal-output", "low-resource-testing"),
                route_requirement="Legal opinion smoke evidence uses grounded-research route metadata without public benchmark text.",
                release_gate_links=("legal-document-benchmark-route-plan-replay", "legal-rag-benchmark-alignment"),
            ),
            RoutePlanAlignmentDimension(
                id="zh-cn-document-task-family",
                title="LexEval-style zh-CN document task-family coverage",
                source_ids=("lexeval",),
                scenario_ids=("contract-review-default-balanced", "evidence-catalog-default-flash-lite", "legal-opinion-grounded-flash-lite"),
                user_need_ids=("grounded-legal-output", "low-resource-testing"),
                route_requirement="Chinese legal document review, classification, and grounded opinion tasks map to local synthetic route families.",
                release_gate_links=("legal-document-benchmark-route-plan-replay", "legal-benchmark-research-refresh"),
            ),
        )
