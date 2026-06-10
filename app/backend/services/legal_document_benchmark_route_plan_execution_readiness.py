from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_route_plan import LegalDocumentBenchmarkRoutePlanService
from services.legal_document_benchmark_route_plan_replay import LegalDocumentBenchmarkRoutePlanReplayService
from services.legal_document_benchmark_route_plan_research_alignment import (
    LegalDocumentBenchmarkRoutePlanResearchAlignmentService,
)


READINESS_ID = "legal-document-benchmark-route-plan-execution-readiness"


class LegalDocumentBenchmarkRoutePlanExecutionReadinessService:
    """Build a metadata-only pre-execution packet for legal document benchmark routing."""

    def __init__(
        self,
        route_plan_service: LegalDocumentBenchmarkRoutePlanService | None = None,
        replay_service: LegalDocumentBenchmarkRoutePlanReplayService | None = None,
        alignment_service: LegalDocumentBenchmarkRoutePlanResearchAlignmentService | None = None,
    ) -> None:
        self.route_plan_service = route_plan_service or LegalDocumentBenchmarkRoutePlanService()
        self.replay_service = replay_service or LegalDocumentBenchmarkRoutePlanReplayService(self.route_plan_service)
        self.alignment_service = alignment_service or LegalDocumentBenchmarkRoutePlanResearchAlignmentService(
            self.replay_service
        )

    def build_packet(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        route_plan_payload = self._route_plan_payload(data)
        replay_payload = self._replay_payload(data)
        alignment_payload = self._alignment_payload(data, replay_payload)

        route_plan = self.route_plan_service.build_plan(route_plan_payload)
        replay = self.replay_service.run_replay(replay_payload)
        alignment = self.alignment_service.build_alignment(alignment_payload)
        gates = self._gates(route_plan, replay, alignment)
        blocking_gate_ids = [gate["id"] for gate in gates if gate["status"] == "fail"]
        warning_gate_ids = [gate["id"] for gate in gates if gate["status"] == "warn"]
        status = "blocked" if blocking_gate_ids else ("ready_with_review" if warning_gate_ids else "ready")
        estimated_total_cost = round(
            route_plan["summary"]["estimated_precheck_cost_usd"]
            + route_plan["summary"]["estimated_primary_cost_usd"],
            6,
        )

        return {
            "id": READINESS_ID,
            "title": "Legal document benchmark route-plan execution readiness",
            "status": status,
            "summary": {
                "route_plan_status": route_plan["status"],
                "route_plan_case_count": route_plan["summary"]["case_count"],
                "route_plan_override_count": route_plan["summary"]["override_count"],
                "replay_status": replay["status"],
                "replay_scenario_count": replay["summary"]["scenario_count"],
                "replay_failed_count": replay["summary"]["fail_count"],
                "research_alignment_status": alignment["status"],
                "research_alignment_dimension_count": alignment["summary"]["dimension_count"],
                "research_alignment_gap_count": alignment["summary"]["gap_count"],
                "source_anchor_count": alignment["summary"]["source_count"],
                "gate_count": len(gates),
                "passing_gate_count": sum(1 for gate in gates if gate["status"] == "pass"),
                "warning_gate_count": len(warning_gate_ids),
                "blocking_gate_count": len(blocking_gate_ids),
                "estimated_total_route_cost_usd": estimated_total_cost,
                "model_calls": "not_required",
                "network_access": "disabled",
                "benchmark_execution": "not_started",
                "manual_execution_ready": status != "blocked",
                "maintainer_approval_recorded": False,
            },
            "source_summaries": {
                "route_plan": {
                    "id": route_plan["id"],
                    "status": route_plan["status"],
                    "case_count": route_plan["summary"]["case_count"],
                    "premium_primary_case_count": route_plan["summary"]["premium_primary_case_count"],
                    "blocking_check_ids": list(route_plan["blocking_check_ids"]),
                    "warning_check_ids": list(route_plan["warning_check_ids"]),
                },
                "route_plan_replay": {
                    "id": replay["id"],
                    "status": replay["status"],
                    "scenario_count": replay["summary"]["scenario_count"],
                    "fail_count": replay["summary"]["fail_count"],
                    "premium_block_count": replay["summary"]["premium_block_count"],
                    "routed_to_recommended_count": replay["summary"]["routed_to_recommended_count"],
                    "rejected_sensitive_scenario_count": replay["summary"]["rejected_sensitive_scenario_count"],
                },
                "research_alignment": {
                    "id": alignment["id"],
                    "status": alignment["status"],
                    "source_count": alignment["summary"]["source_count"],
                    "dimension_count": alignment["summary"]["dimension_count"],
                    "gap_count": alignment["summary"]["gap_count"],
                    "blocking_check_ids": list(alignment["blocking_check_ids"]),
                    "warning_check_ids": list(alignment["warning_check_ids"]),
                },
            },
            "pre_execution_gates": gates,
            "blocking_gate_ids": blocking_gate_ids,
            "warning_gate_ids": warning_gate_ids,
            "manual_run_packet": {
                "recommended_fixture_limit": 3,
                "max_parallel_model_requests": 1,
                "default_execution_mode": "manual_serial",
                "default_model_strategy": "cheap_first_gemini",
                "requires_maintainer_review": True,
                "records_approval": False,
                "executes_benchmark": False,
                "next_actions": self._next_actions(status, blocking_gate_ids, warning_gate_ids),
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_route_metadata": True,
                "returns_source_urls": True,
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
                "writes_configuration": False,
                "shifts_traffic": False,
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "paper_reproduction_claimed": False,
                "production_accuracy_claimed": False,
                "real_client_document_coverage_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "benchmark_executed": False,
                "maintainer_approval_claimed": False,
                "allowed_claim": (
                    "Local synthetic legal-document benchmark routing has a metadata-only execution readiness packet."
                ),
                "forbidden_claims": [
                    "Do not claim public benchmark scores, live Gemini/NewAPI execution, or paper reproduction.",
                    "Do not claim maintainer approval, default-model changes, traffic shifts, or real client-document coverage.",
                ],
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_readiness.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_replay.py tests/test_legal_document_benchmark_route_plan_research_alignment.py -q",
            ],
        }

    def _route_plan_payload(self, data: dict[str, Any]) -> dict[str, Any] | None:
        route_plan = data.get("route_plan")
        if isinstance(route_plan, dict):
            return route_plan
        if isinstance(data.get("case_route_overrides"), dict):
            return {"case_route_overrides": data.get("case_route_overrides")}
        return None

    def _replay_payload(self, data: dict[str, Any]) -> dict[str, Any] | None:
        replay = data.get("route_plan_replay")
        if isinstance(replay, dict):
            return replay
        if isinstance(data.get("scenarios"), list):
            return {"scenarios": data.get("scenarios")}
        return None

    def _alignment_payload(self, data: dict[str, Any], replay_payload: dict[str, Any] | None) -> dict[str, Any] | None:
        alignment = data.get("research_alignment")
        if isinstance(alignment, dict):
            return alignment
        if replay_payload is not None:
            return {"route_plan_replay": replay_payload}
        return None

    def _gates(
        self,
        route_plan: dict[str, Any],
        replay: dict[str, Any],
        alignment: dict[str, Any],
    ) -> list[dict[str, str]]:
        return [
            self._gate(
                "route-plan-not-blocked",
                "pass" if route_plan["status"] != "blocked" else "fail",
                "Cheap-first route plan must not be blocked before manual benchmark execution.",
            ),
            self._gate(
                "route-plan-coverage-ready",
                "pass"
                if route_plan["source_summaries"]["legal_document_benchmark_coverage"]["missing_document_type_count"]
                == 0
                else "warn",
                "Synthetic document coverage should be locally complete before execution.",
            ),
            self._gate(
                "replay-scenarios-pass",
                "pass" if replay["status"] == "pass" else "fail",
                "Route-plan replay scenarios must pass before benchmark execution planning.",
            ),
            self._gate(
                "premium-block-replayed",
                "pass" if replay["summary"]["premium_block_count"] >= 1 else "fail",
                "Premium-default blocking must be replayed before maintainers trust cheap-first routing.",
            ),
            self._gate(
                "research-alignment-ready",
                "pass" if alignment["status"] == "ready" else "fail",
                "Research/source alignment must be ready before public source anchors support route planning.",
            ),
            self._gate(
                "official-source-anchors-present",
                "pass" if alignment["summary"]["official_model_source_count"] >= 2 else "fail",
                "Gemini model and pricing source anchors must stay present.",
            ),
            self._gate(
                "low-resource-execution-plan",
                "pass",
                "Manual execution remains serial and laptop-safe with max_parallel_model_requests=1.",
            ),
            self._gate(
                "metadata-only-boundary",
                "pass"
                if self._metadata_only(route_plan, replay, alignment)
                else "fail",
                "Readiness packet must not call models, download datasets, or return raw benchmark material.",
            ),
            self._gate(
                "manual-approval-not-claimed",
                "pass",
                "The packet can prepare manual execution review but does not record approval or signoff.",
            ),
        ]

    def _gate(self, gate_id: str, status: str, reason: str) -> dict[str, str]:
        return {
            "id": gate_id,
            "status": status,
            "reason": reason,
            "release_action": "block_manual_run" if status == "fail" else "review" if status == "warn" else "allow_review",
        }

    def _metadata_only(
        self,
        route_plan: dict[str, Any],
        replay: dict[str, Any],
        alignment: dict[str, Any],
    ) -> bool:
        return (
            route_plan["privacy_boundary"]["model_calls"] is False
            and route_plan["privacy_boundary"]["network_access"] is False
            and replay["privacy_boundary"]["model_calls"] is False
            and replay["privacy_boundary"]["network_access"] is False
            and alignment["privacy_boundary"]["calls_model"] is False
            and alignment["privacy_boundary"]["network_called"] is False
            and alignment["privacy_boundary"]["returns_raw_scenario_payload"] is False
        )

    def _next_actions(self, status: str, blocking_gate_ids: list[str], warning_gate_ids: list[str]) -> list[str]:
        if status == "blocked":
            return [
                f"Resolve blocking readiness gates: {', '.join(blocking_gate_ids)}.",
                "Rerun route-plan replay and research alignment before any manual benchmark execution.",
            ]
        if warning_gate_ids:
            return [
                f"Review warning readiness gates: {', '.join(warning_gate_ids)}.",
                "Keep the run manual, serial, and cheap-first until warning evidence is resolved.",
            ]
        return [
            "Prepare a manual serial low-resource benchmark run with fixture_limit=3 and max_parallel_model_requests=1.",
            "Record sanitized validation metadata after the run; do not store prompts, raw legal text, model output, or credentials.",
        ]
