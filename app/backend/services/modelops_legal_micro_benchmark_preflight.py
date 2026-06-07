from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import (
    LegalDocumentFactConsistencyBenchmarkService,
)
from services.legal_fixture_local_run_package import LegalFixtureLocalRunPackageService
from services.legal_fixture_quick_suite import LegalFixtureQuickSuiteService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)


DEFAULT_FIXTURE_LIMIT = 2
DEFAULT_DOCUMENT_CASE_LIMIT = 2
DEFAULT_FACT_CASE_LIMIT = 1


class ModelOpsLegalMicroBenchmarkPreflightService:
    """Build a laptop-safe cheap-first legal benchmark preflight packet."""

    def __init__(
        self,
        quick_suite_service: LegalFixtureQuickSuiteService | None = None,
        local_run_package_service: LegalFixtureLocalRunPackageService | None = None,
        document_benchmark_service: LegalDocumentBenchmarkSuiteService | None = None,
        fact_consistency_service: LegalDocumentFactConsistencyBenchmarkService | None = None,
        benchmark_gate_service: ModelOpsLegalFixtureCheapFirstBenchmarkGateService | None = None,
    ) -> None:
        self.quick_suite_service = quick_suite_service or LegalFixtureQuickSuiteService()
        self.local_run_package_service = local_run_package_service or LegalFixtureLocalRunPackageService()
        self.document_benchmark_service = document_benchmark_service or LegalDocumentBenchmarkSuiteService()
        self.fact_consistency_service = fact_consistency_service or LegalDocumentFactConsistencyBenchmarkService()
        self.benchmark_gate_service = benchmark_gate_service or ModelOpsLegalFixtureCheapFirstBenchmarkGateService()

    def build_packet(
        self,
        fixture_limit: int = DEFAULT_FIXTURE_LIMIT,
        document_case_limit: int = DEFAULT_DOCUMENT_CASE_LIMIT,
        fact_case_limit: int = DEFAULT_FACT_CASE_LIMIT,
    ) -> dict[str, Any]:
        fixture_limit = self._limit(fixture_limit, default=DEFAULT_FIXTURE_LIMIT, maximum=4)
        document_case_limit = self._limit(document_case_limit, default=DEFAULT_DOCUMENT_CASE_LIMIT, maximum=7)
        fact_case_limit = self._limit(fact_case_limit, default=DEFAULT_FACT_CASE_LIMIT, maximum=4)
        quick_suite = self.quick_suite_service.build_suite(fixture_limit)
        local_package = self.local_run_package_service.build_package(fixture_limit)
        document_suite = self.document_benchmark_service.build_suite()
        fact_suite = self.fact_consistency_service.build_suite()
        gate = self.benchmark_gate_service.build_gate()
        fixture_items = self._fixture_items(quick_suite, local_package)
        document_items = self._document_items(document_suite, document_case_limit)
        fact_items = self._fact_items(fact_suite, fact_case_limit)
        checks = self._checks(quick_suite, local_package, document_suite, fact_suite, fixture_items)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]

        return {
            "id": "modelops-legal-micro-benchmark-preflight",
            "status": "blocked" if blocking else ("review_required" if warnings else "ready"),
            "method": {
                "type": "modelops-legal-micro-benchmark-preflight",
                "notes": [
                    "Builds a reviewer packet for the smallest cheap-first legal benchmark run.",
                    "Uses existing synthetic fixture ids, document case ids, fact case ids, cost estimates, and follow-up gates only.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or the network.",
                ],
            },
            "summary": {
                "fixture_limit": fixture_limit,
                "document_case_limit": document_case_limit,
                "fact_case_limit": fact_case_limit,
                "selected_fixture_count": len(fixture_items),
                "document_case_count": len(document_items),
                "fact_consistency_case_count": len(fact_items),
                "request_file_count": local_package["summary"]["request_file_count"],
                "max_parallel_requests": 1,
                "estimated_cheap_first_cost_usd": local_package["summary"]["estimated_cheap_first_cost_usd"],
                "cheap_first_model_count": len({item["model"] for item in fixture_items if item["model"]}),
                "follow_up_endpoint_count": len(self._follow_up_endpoints()),
                "gate_status_before_run": gate["status"],
                "benchmark_gate_required": True,
                "default_change_allowed": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "gateway_called": False,
                "network_called": False,
            },
            "fixture_run_items": fixture_items,
            "document_check_items": document_items,
            "fact_consistency_items": fact_items,
            "run_sequence": self._run_sequence(fixture_items, document_items, fact_items),
            "follow_up_endpoints": self._follow_up_endpoints(),
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "cheap_first_policy": {
                "primary_strategy": "run_selected_fixtures_on_lowest_cost_gemini_first",
                "primary_models": sorted({item["model"] for item in fixture_items if item["model"]}),
                "escalation_allowed_before_smoke_score": False,
                "premium_default_allowed": False,
                "max_parallel_requests": 1,
                "default_change_allowed_from_preflight_alone": False,
                "post_run_gate": "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_document_case_ids": True,
                "returns_fact_consistency_case_ids": True,
                "returns_expected_counts": True,
                "returns_request_body": False,
                "returns_messages": False,
                "returns_prompt_text": False,
                "returns_fixture_excerpt": False,
                "returns_document_snippet": False,
                "returns_generated_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_response": False,
                "returns_credentials": False,
                "model_calls": False,
                "network_called": False,
            },
            "claim_boundary": {
                "live_gateway_quality_claimed": False,
                "public_benchmark_scores_claimed": False,
                "production_legal_accuracy_claimed": False,
                "automatic_default_change_claimed": False,
                "legal_advice_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_micro_benchmark_preflight.py tests/test_legal_fixture_local_run_package.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _fixture_items(self, quick_suite: dict[str, Any], local_package: dict[str, Any]) -> list[dict[str, Any]]:
        package_by_fixture = {
            row["fixture_id"]: row
            for row in local_package.get("request_files", [])
            if isinstance(row, dict) and row.get("fixture_id")
        }
        items: list[dict[str, Any]] = []
        for order, fixture in enumerate(quick_suite.get("selected_fixtures", []), start=1):
            if not isinstance(fixture, dict):
                continue
            package_row = package_by_fixture.get(str(fixture.get("fixture_id")), {})
            items.append(
                {
                    "id": f"micro-fixture-{order:02d}-{fixture['fixture_id']}",
                    "order": order,
                    "fixture_id": fixture["fixture_id"],
                    "title": fixture["title"],
                    "matter_type": fixture["matter_type"],
                    "task": fixture["task"],
                    "model": package_row.get("model") or fixture.get("model"),
                    "model_cost_tier": package_row.get("model_cost_tier") or fixture.get("model_cost_tier"),
                    "estimated_request_cost_usd": package_row.get("estimated_request_cost_usd")
                    if package_row
                    else fixture.get("estimated_request_cost_usd"),
                    "prompt_tokens_estimate": fixture.get("prompt_tokens_estimate"),
                    "completion_tokens_budget": fixture.get("completion_tokens_budget"),
                    "expected_route_count": len(fixture.get("expected_routes") or []),
                    "expected_task_count": len(fixture.get("expected_tasks") or []),
                    "expected_signal_count": len(fixture.get("expected_signals") or []),
                    "public_source_count": len(fixture.get("public_source_ids") or []),
                    "result_template_target": "observations",
                    "release_action": "run_serial_cheap_first_then_score_fixture_smoke",
                    "raw_fixture_text_returned": False,
                    "request_body_returned": False,
                    "gateway_called": False,
                }
            )
        return items

    def _document_items(self, document_suite: dict[str, Any], limit: int) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for order, case in enumerate(document_suite.get("benchmark_cases", [])[:limit], start=1):
            if not isinstance(case, dict):
                continue
            items.append(
                {
                    "id": f"micro-document-{order:02d}-{case['id']}",
                    "order": order,
                    "case_id": case["id"],
                    "title": case["title"],
                    "document_type": case["document_type"],
                    "matter_type": case["matter_type"],
                    "required_section_count": len(case.get("required_sections") or []),
                    "expected_citation_count": len(case.get("expected_citations") or []),
                    "expected_risk_label_count": len(case.get("expected_risk_labels") or []),
                    "check_ids": ["document_structure", "citation_presence", "pii_exclusion", "risk_labeling"],
                    "release_action": "include_metadata_counts_in_cheap_first_gate_payload",
                    "raw_document_snippet_returned": False,
                    "candidate_text_returned": False,
                }
            )
        return items

    def _fact_items(self, fact_suite: dict[str, Any], limit: int) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for order, case in enumerate(fact_suite.get("benchmark_cases", [])[:limit], start=1):
            if not isinstance(case, dict):
                continue
            items.append(
                {
                    "id": f"micro-fact-{order:02d}-{case['id']}",
                    "order": order,
                    "case_id": case["id"],
                    "title": case["title"],
                    "document_type": case["document_type"],
                    "matter_type": case["matter_type"],
                    "amount_expectation_count": len(case.get("amount_expectations") or []),
                    "deadline_expectation_count": len(case.get("deadline_expectations") or []),
                    "required_fact_count": len(case.get("required_fact_ids") or []),
                    "contradiction_pair_count": len(case.get("contradiction_pairs") or []),
                    "check_ids": [
                        "amount_consistency",
                        "deadline_consistency",
                        "required_fact_presence",
                        "contradiction_exclusion",
                        "raw_input_exclusion",
                    ],
                    "release_action": "include_structured_counts_in_cheap_first_gate_payload",
                    "raw_document_text_returned": False,
                    "candidate_text_returned": False,
                }
            )
        return items

    def _checks(
        self,
        quick_suite: dict[str, Any],
        local_package: dict[str, Any],
        document_suite: dict[str, Any],
        fact_suite: dict[str, Any],
        fixture_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        estimated_cost = local_package.get("summary", {}).get("estimated_cheap_first_cost_usd")
        return [
            {
                "id": "quick-suite-ready",
                "status": "pass" if quick_suite.get("status") == "ready" else "warn",
                "reason": f"Quick suite status is {quick_suite.get('status')}.",
            },
            {
                "id": "local-run-package-ready",
                "status": "pass" if local_package.get("status") == "ready" else "warn",
                "reason": f"Local run package status is {local_package.get('status')}.",
            },
            {
                "id": "micro-fixtures-selected",
                "status": "pass" if fixture_items else "fail",
                "reason": f"Selected {len(fixture_items)} cheap-first fixture rows.",
            },
            {
                "id": "document-benchmark-ready",
                "status": "pass" if document_suite.get("status") == "ready" else "warn",
                "reason": f"Document benchmark suite status is {document_suite.get('status')}.",
            },
            {
                "id": "fact-consistency-ready",
                "status": "pass" if fact_suite.get("status") == "ready" else "warn",
                "reason": f"Fact consistency suite status is {fact_suite.get('status')}.",
            },
            {
                "id": "serial-low-resource-budget",
                "status": "pass"
                if local_package.get("summary", {}).get("max_parallel_requests") == 1
                else "warn",
                "reason": "Max parallel requests stays at 1 for small local machines.",
            },
            {
                "id": "cheap-first-cost-cap",
                "status": "pass" if isinstance(estimated_cost, int | float) and estimated_cost < 0.01 else "warn",
                "reason": f"Estimated selected cheap-first cost is {estimated_cost}.",
            },
            {
                "id": "metadata-only-boundary",
                "status": "pass",
                "reason": "Preflight returns ids, counts, costs, endpoints, and flags only.",
            },
        ]

    def _run_sequence(
        self,
        fixture_items: list[dict[str, Any]],
        document_items: list[dict[str, Any]],
        fact_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "order": 1,
                "id": "prepare-local-run-package",
                "action": "Fetch the maintenance local-run-package with a small fixture_limit.",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/local-run-package",
                "item_count": len(fixture_items),
                "model_call": False,
            },
            {
                "order": 2,
                "id": "run-cheap-first-fixtures-serially",
                "action": "Run selected cheap-first fixture requests one at a time outside source control.",
                "fixture_ids": [item["fixture_id"] for item in fixture_items],
                "max_parallel_requests": 1,
                "model_call": "manual_only",
            },
            {
                "order": 3,
                "id": "score-legal-document-metadata",
                "action": "Score document structure, citation, PII, and risk-label counts from normalized metadata.",
                "case_ids": [item["case_id"] for item in document_items],
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                "model_call": False,
            },
            {
                "order": 4,
                "id": "score-fact-consistency-metadata",
                "action": "Score amount, deadline, required-fact, contradiction, and raw-input metadata.",
                "case_ids": [item["case_id"] for item in fact_items],
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/document-fact-consistency",
                "model_call": False,
            },
            {
                "order": 5,
                "id": "submit-cheap-first-benchmark-gate",
                "action": "Submit normalized observations and structured counts to the cheap-first benchmark gate.",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
                "model_call": False,
            },
        ]

    def _follow_up_endpoints(self) -> list[str]:
        return [
            "/api/v1/maintenance/legal-review-benchmark/local-response-normalizer",
            "/api/v1/maintenance/legal-review-benchmark/local-run-review",
            "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
            "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
            "/api/v1/maintenance/legal-review-benchmark/document-fact-consistency",
            "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
            "/api/v1/maintenance/legal-review-benchmark/default-promotion-packet",
        ]

    def _recommended_actions(self, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
        if blocking:
            return ["Fix preflight blockers before running even the cheap Gemini fixture checks."]
        actions = [
            "Run the selected cheap-first fixtures serially before any balanced or premium escalation.",
            "Keep document and fact consistency evidence as structured counts and ids only.",
            "Use the cheap-first benchmark gate result before changing Gemini defaults.",
        ]
        if warnings:
            actions.append("Review preflight warnings before relying on the packet for release evidence.")
        return actions

    def _limit(self, value: int, *, default: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(1, min(parsed, maximum))
