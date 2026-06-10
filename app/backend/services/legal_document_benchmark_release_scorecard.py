from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_document_benchmark_route_plan import LegalDocumentBenchmarkRoutePlanService
from services.legal_document_benchmark_route_plan_execution_claim_gate import (
    LegalDocumentBenchmarkRoutePlanExecutionClaimGateService,
)
from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_coverage_claim_policy import LegalDocumentCoverageClaimPolicyService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService


SCORECARD_ID = "legal-document-benchmark-release-scorecard"
SAFE_COVERAGE_CLAIM = (
    "Repository tests include synthetic local fixtures covering civil complaints, defense answers, "
    "lawyer letters, contract review, evidence catalogs, settlement agreements, and legal opinions."
)
SAFE_EXECUTION_CLAIM = (
    "Repository-backed metadata-only route-plan execution review packet supports sanitized release evidence."
)


class LegalDocumentBenchmarkReleaseScorecardService:
    """Aggregate local legal-document benchmark readiness into one reviewer scorecard."""

    def __init__(
        self,
        suite_service: LegalDocumentBenchmarkSuiteService | None = None,
        coverage_service: LegalDocumentBenchmarkCoverageService | None = None,
        route_plan_service: LegalDocumentBenchmarkRoutePlanService | None = None,
        fact_service: LegalDocumentFactConsistencyBenchmarkService | None = None,
        claim_policy_service: LegalDocumentCoverageClaimPolicyService | None = None,
        execution_claim_gate_service: LegalDocumentBenchmarkRoutePlanExecutionClaimGateService | None = None,
    ) -> None:
        self.suite_service = suite_service or LegalDocumentBenchmarkSuiteService()
        self.coverage_service = coverage_service or LegalDocumentBenchmarkCoverageService()
        self.route_plan_service = route_plan_service or LegalDocumentBenchmarkRoutePlanService()
        self.fact_service = fact_service or LegalDocumentFactConsistencyBenchmarkService()
        self.claim_policy_service = claim_policy_service or LegalDocumentCoverageClaimPolicyService()
        self.execution_claim_gate_service = (
            execution_claim_gate_service or LegalDocumentBenchmarkRoutePlanExecutionClaimGateService()
        )

    def build_scorecard(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        suite = self.suite_service.build_suite()
        coverage = self.coverage_service.build_matrix()
        route_plan = self.route_plan_service.build_plan(
            data.get("route_plan") if isinstance(data.get("route_plan"), dict) else None
        )
        fact_suite = self.fact_service.build_suite()
        document_evaluation = self.suite_service.evaluate_outputs(
            data.get("document_outputs") if isinstance(data.get("document_outputs"), dict) else None
        )
        fact_evaluation = self.fact_service.evaluate_outputs(
            data.get("fact_outputs") if isinstance(data.get("fact_outputs"), dict) else None
        )
        coverage_claim_policy = self.claim_policy_service.evaluate(
            self._claims(data.get("coverage_claims"), SAFE_COVERAGE_CLAIM)
        )
        execution_claim_gate = self.execution_claim_gate_service.evaluate(
            self._execution_claim_payload(data)
        )

        components = [
            self._component(
                "document_benchmark_suite",
                "Document benchmark suite",
                suite["status"],
                {"case_count": suite["summary"]["case_count"], "check_count": suite["summary"]["check_count"]},
            ),
            self._component(
                "document_coverage_matrix",
                "Document coverage matrix",
                coverage["status"],
                {
                    "covered_document_type_count": coverage["summary"]["covered_document_type_count"],
                    "missing_document_type_count": coverage["summary"]["missing_document_type_count"],
                },
            ),
            self._component(
                "cheap_first_route_plan",
                "Cheap-first route plan",
                route_plan["status"],
                {
                    "case_count": route_plan["summary"]["case_count"],
                    "premium_primary_case_count": route_plan["summary"]["premium_primary_case_count"],
                    "estimated_primary_cost_usd": route_plan["summary"]["estimated_primary_cost_usd"],
                },
                route_plan.get("blocking_check_ids", []),
                route_plan.get("warning_check_ids", []),
            ),
            self._component(
                "fact_consistency_suite",
                "Fact consistency suite",
                fact_suite["status"],
                {"case_count": fact_suite["summary"]["case_count"], "check_count": fact_suite["summary"]["check_count"]},
            ),
            self._component(
                "document_output_evaluation",
                "Document output evaluation",
                self._evaluation_status(document_evaluation["status"]),
                {
                    "score": document_evaluation["score"],
                    "case_count": document_evaluation["case_count"],
                    "not_run_case_count": document_evaluation["not_run_case_count"],
                    "blocking_case_count": len(document_evaluation["blocking_case_ids"]),
                },
                document_evaluation["blocking_case_ids"],
            ),
            self._component(
                "fact_consistency_evaluation",
                "Fact consistency evaluation",
                self._evaluation_status(fact_evaluation["status"]),
                {
                    "score": fact_evaluation["score"],
                    "case_count": fact_evaluation["case_count"],
                    "not_run_case_count": fact_evaluation["not_run_case_count"],
                    "blocking_case_count": len(fact_evaluation["blocking_case_ids"]),
                },
                fact_evaluation["blocking_case_ids"],
            ),
            self._component(
                "coverage_claim_policy",
                "Coverage claim policy",
                coverage_claim_policy["status"],
                {
                    "claim_count": coverage_claim_policy["summary"]["claim_count"],
                    "blocked_count": coverage_claim_policy["summary"]["blocked_count"],
                    "review_required_count": coverage_claim_policy["summary"]["review_required_count"],
                },
            ),
            self._component(
                "execution_claim_gate",
                "Execution claim gate",
                execution_claim_gate["status"],
                {
                    "claim_count": execution_claim_gate["summary"]["claim_count"],
                    "blocked_claim_count": execution_claim_gate["summary"]["blocked_claim_count"],
                    "review_required_claim_count": execution_claim_gate["summary"]["review_required_claim_count"],
                    "ready_for_release_packet": execution_claim_gate["summary"]["ready_for_release_packet"],
                },
                execution_claim_gate.get("blocking_claim_hashes", []),
                execution_claim_gate.get("review_claim_hashes", []),
            ),
        ]
        status = self._overall_status(components)
        ready_components = sum(1 for component in components if component["status"] in {"ready", "pass"})
        review_components = sum(1 for component in components if component["status"] == "review_required")
        blocked_components = sum(1 for component in components if component["status"] == "blocked")

        return {
            "id": SCORECARD_ID,
            "title": "Legal document benchmark release scorecard",
            "status": status,
            "policy_version": "legal-document-benchmark-release-scorecard-v1",
            "summary": {
                "component_count": len(components),
                "ready_component_count": ready_components,
                "review_required_component_count": review_components,
                "blocked_component_count": blocked_components,
                "scorecard_score": round(100 * ready_components / max(1, len(components))),
                "document_case_count": suite["summary"]["case_count"],
                "covered_document_type_count": coverage["summary"]["covered_document_type_count"],
                "fact_case_count": fact_suite["summary"]["case_count"],
                "route_plan_status": route_plan["status"],
                "execution_claim_gate_status": execution_claim_gate["status"],
                "release_claim_ready": status == "ready",
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "benchmark_executed": False,
                "release_record_written": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "raw_text_returned": False,
            },
            "component_rows": components,
            "blocking_component_ids": [
                component["id"] for component in components if component["status"] == "blocked"
            ],
            "review_component_ids": [
                component["id"] for component in components if component["status"] == "review_required"
            ],
            "source_summaries": {
                "document_benchmark_suite": {
                    "status": suite["status"],
                    "case_count": suite["summary"]["case_count"],
                    "check_count": suite["summary"]["check_count"],
                },
                "document_coverage_matrix": {
                    "status": coverage["status"],
                    "covered_document_type_count": coverage["summary"]["covered_document_type_count"],
                    "missing_document_type_count": coverage["summary"]["missing_document_type_count"],
                },
                "cheap_first_route_plan": {
                    "status": route_plan["status"],
                    "case_count": route_plan["summary"]["case_count"],
                    "premium_primary_case_count": route_plan["summary"]["premium_primary_case_count"],
                    "estimated_total_cost_usd": round(
                        route_plan["summary"]["estimated_precheck_cost_usd"]
                        + route_plan["summary"]["estimated_primary_cost_usd"],
                        6,
                    ),
                },
                "fact_consistency_suite": {
                    "status": fact_suite["status"],
                    "case_count": fact_suite["summary"]["case_count"],
                    "check_count": fact_suite["summary"]["check_count"],
                },
                "coverage_claim_policy": {
                    "status": coverage_claim_policy["status"],
                    "claim_count": coverage_claim_policy["summary"]["claim_count"],
                    "blocked_count": coverage_claim_policy["summary"]["blocked_count"],
                },
                "execution_claim_gate": {
                    "status": execution_claim_gate["status"],
                    "claim_count": execution_claim_gate["summary"]["claim_count"],
                    "ready_for_release_packet": execution_claim_gate["summary"]["ready_for_release_packet"],
                },
            },
            "release_decision": {
                "can_reference_local_synthetic_coverage": coverage_claim_policy["status"] == "ready",
                "can_reference_execution_review_packet": execution_claim_gate["status"] == "ready",
                "can_claim_public_benchmark_scores": False,
                "can_claim_live_provider_execution": False,
                "can_claim_production_legal_quality": False,
                "can_claim_default_change_or_traffic_shift": False,
                "requires_manual_review": status != "ready",
            },
            "recommended_actions": self._recommended_actions(status, components),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_snippets": False,
                "returns_raw_document_text": False,
                "returns_generated_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_responses": False,
                "returns_request_bodies": False,
                "returns_response_bodies": False,
                "returns_headers": False,
                "returns_credentials": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "benchmark_executed": False,
                "release_record_written": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "live_provider_execution_claimed": False,
                "production_quality_claimed": False,
                "real_client_document_coverage_claimed": False,
                "release_approval_claimed": False,
                "default_change_claimed": False,
                "traffic_shift_claimed": False,
                "allowed_release_claim_scope": (
                    "local synthetic legal-document fixture coverage and metadata-only route-plan evidence"
                ),
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_release_scorecard.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_fact_consistency_benchmark.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan.py tests/test_legal_document_benchmark_route_plan_execution_claim_gate.py -q",
            ],
        }

    def _claims(self, value: Any, fallback: str) -> list[str]:
        if isinstance(value, list):
            return [str(item or "") for item in value[:40]]
        if isinstance(value, dict):
            return [str(item or "") for _, item in sorted(value.items())[:40]]
        if isinstance(value, str):
            return [value]
        return [fallback]

    def _execution_claim_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if isinstance(data.get("observations"), list):
            payload["observations"] = data["observations"]
        if isinstance(data.get("execution_readiness"), dict):
            payload["execution_readiness"] = data["execution_readiness"]
        if isinstance(data.get("execution_result_archive"), dict):
            payload["execution_result_archive"] = data["execution_result_archive"]
        if isinstance(data.get("execution_result_handoff"), dict):
            payload["execution_result_handoff"] = data["execution_result_handoff"]
        if isinstance(data.get("execution_review_packet"), dict):
            payload["execution_review_packet"] = data["execution_review_packet"]
        payload["claims"] = self._claims(data.get("execution_claims"), SAFE_EXECUTION_CLAIM)
        return payload

    def _evaluation_status(self, status: str) -> str:
        if status == "pass":
            return "ready"
        if status == "fail":
            return "blocked"
        return "review_required"

    def _component(
        self,
        component_id: str,
        title: str,
        status: str,
        metrics: dict[str, Any],
        blocking_ids: list[str] | None = None,
        warning_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        normalized_status = self._normalized_status(status)
        release_action = (
            "attach_to_release_scorecard"
            if normalized_status == "ready"
            else "review_before_release"
            if normalized_status == "review_required"
            else "block_release_claim"
        )
        return {
            "id": component_id,
            "title": title,
            "status": normalized_status,
            "source_status": status,
            "release_action": release_action,
            "metrics": metrics,
            "blocking_ids": list(blocking_ids or []),
            "warning_ids": list(warning_ids or []),
        }

    def _normalized_status(self, status: str) -> str:
        if status in {"ready", "pass"}:
            return "ready"
        if status in {"blocked", "fail"}:
            return "blocked"
        return "review_required"

    def _overall_status(self, components: list[dict[str, Any]]) -> str:
        if any(component["status"] == "blocked" for component in components):
            return "blocked"
        if any(component["status"] == "review_required" for component in components):
            return "review_required"
        return "ready"

    def _recommended_actions(self, status: str, components: list[dict[str, Any]]) -> list[str]:
        if status == "ready":
            return [
                "Use the scorecard as local synthetic benchmark release evidence only.",
                "Keep public benchmark scores, live provider execution, production quality, default changes, and traffic shifts out of release wording.",
            ]
        blocked = [component["id"] for component in components if component["status"] == "blocked"]
        if blocked:
            return [
                f"Clear blocked scorecard components before public release claims: {', '.join(blocked)}.",
                "Rewrite release wording to local synthetic fixture evidence and metadata-only route-plan evidence.",
            ]
        review = [component["id"] for component in components if component["status"] == "review_required"]
        return [
            f"Review or complete scorecard components before release claims: {', '.join(review)}.",
            "Run only laptop-safe local checks and sanitized route-plan observations before moving from review_required to ready.",
        ]
