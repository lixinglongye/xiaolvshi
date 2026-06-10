from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from services.gemini_newapi_observed_model_extraction import safe_model_id
from services.legal_document_benchmark_route_plan import LegalDocumentBenchmarkRoutePlanService


REPLAY_ID = "legal-document-benchmark-route-plan-replay"
MAX_SCENARIOS = 20
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\bbearer\s+[A-Za-z0-9._-]{10,}|password|secret|api[_-]?key|authorization|token)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RoutePlanReplayScenario:
    id: str
    case_id: str
    override_primary_task: str | None
    override_primary_model: str | None
    override_approval: bool
    expected_plan_status: str
    expected_primary_task: str
    expected_resolved_model: str
    expected_cost_tier: str
    expected_route_band: str
    expected_routed_to_recommended: bool
    expected_blocking_check_ids: tuple[str, ...]
    rationale: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["expected_blocking_check_ids"] = list(self.expected_blocking_check_ids)
        return data


class LegalDocumentBenchmarkRoutePlanReplayService:
    """Replay legal-document benchmark route-plan scenarios without model calls."""

    def __init__(self, route_plan_service: LegalDocumentBenchmarkRoutePlanService | None = None) -> None:
        self.route_plan_service = route_plan_service or LegalDocumentBenchmarkRoutePlanService()

    def run_replay(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        raw_scenarios = data.get("scenarios")
        require_complete_coverage = not isinstance(raw_scenarios, list)
        sensitive_count = self._sensitive_scenario_count(raw_scenarios)
        scenarios = self._scenarios(raw_scenarios)
        results = [self._run_scenario(scenario) for scenario in scenarios]
        failed = [item for item in results if item["status"] == "fail"]
        blocked_plan_count = sum(1 for item in results if item["actual"]["plan_status"] == "blocked")
        routed_to_recommended_count = sum(
            1 for item in results if item["actual"]["routed_to_recommended_model"] is True
        )
        premium_block_count = sum(
            1 for item in results if "no-premium-primary-defaults" in item["actual"]["blocking_check_ids"]
        )
        checks = self._aggregate_checks(
            results=results,
            failed=failed,
            premium_block_count=premium_block_count,
            routed_to_recommended_count=routed_to_recommended_count,
            require_complete_coverage=require_complete_coverage,
        )
        blocking_check_ids = [check["id"] for check in checks if check["status"] == "fail"]

        return {
            "id": REPLAY_ID,
            "status": "fail" if failed or blocking_check_ids else "pass",
            "summary": {
                "scenario_count": len(results),
                "pass_count": sum(1 for item in results if item["status"] == "pass"),
                "fail_count": len(failed),
                "blocked_plan_count": blocked_plan_count,
                "routed_to_recommended_count": routed_to_recommended_count,
                "premium_block_count": premium_block_count,
                "rejected_sensitive_scenario_count": sensitive_count,
                "model_calls": "not_required",
                "network_access": "disabled",
                "raw_fixture_snippets_returned": False,
                "raw_outputs_returned": False,
            },
            "method": {
                "type": REPLAY_ID,
                "version": "2026-06-10",
                "inputs": [
                    "legal-document benchmark case ids",
                    "route-plan override metadata",
                    "expected cheap-first routing outcomes",
                ],
                "notes": [
                    "Each scenario calls the local route-plan service with sanitized metadata only.",
                    "Scenario checks compare status, route band, selected model, budget tier, and premium-block ids.",
                    "No NewAPI, Gemini, gateway, benchmark execution, or external dataset call is made.",
                ],
            },
            "replay_results": results,
            "checks": checks,
            "blocking_check_ids": blocking_check_ids,
            "recommended_actions": self._recommended_actions(failed, blocking_check_ids),
            "privacy_boundary": {
                "returns_fixture_snippets": False,
                "returns_raw_candidate_outputs": False,
                "returns_raw_model_outputs": False,
                "returns_prompts": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_access": False,
                "raw_scenario_payload_echoed": False,
                "output_scope": "scenario ids, case ids, expected route metadata, actual route metadata, checks, and counts",
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "production_accuracy_claimed": False,
                "real_client_document_coverage_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "allowed_claim": (
                    "Local synthetic route-plan scenarios replay expected cheap-first and premium-block behavior."
                ),
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_replay.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan.py tests/test_model_runtime_router.py -q",
            ],
        }

    def _run_scenario(self, scenario: RoutePlanReplayScenario) -> dict[str, Any]:
        plan = self.route_plan_service.build_plan(self._route_plan_payload(scenario))
        rows = {row["case_id"]: row for row in plan["case_route_rows"]}
        row = rows.get(scenario.case_id)
        actual = self._actual(plan, row)
        checks = [
            self._check("case-present", row is not None, scenario.case_id, actual["case_id"]),
            self._check("plan-status", plan["status"] == scenario.expected_plan_status, scenario.expected_plan_status, plan["status"]),
            self._check(
                "primary-task",
                actual["primary_task"] == scenario.expected_primary_task,
                scenario.expected_primary_task,
                actual["primary_task"],
            ),
            self._check(
                "resolved-model",
                actual["resolved_model"] == scenario.expected_resolved_model,
                scenario.expected_resolved_model,
                actual["resolved_model"],
            ),
            self._check(
                "cost-tier",
                actual["cost_tier"] == scenario.expected_cost_tier,
                scenario.expected_cost_tier,
                actual["cost_tier"],
            ),
            self._check(
                "route-band",
                actual["route_band"] == scenario.expected_route_band,
                scenario.expected_route_band,
                actual["route_band"],
            ),
            self._check(
                "routed-to-recommended",
                actual["routed_to_recommended_model"] == scenario.expected_routed_to_recommended,
                scenario.expected_routed_to_recommended,
                actual["routed_to_recommended_model"],
            ),
            self._check(
                "blocking-checks",
                set(actual["blocking_check_ids"]) == set(scenario.expected_blocking_check_ids),
                list(scenario.expected_blocking_check_ids),
                actual["blocking_check_ids"],
            ),
            self._check(
                "metadata-only-boundary",
                plan["summary"]["model_calls"] == "not_required"
                and plan["summary"]["network_access"] == "disabled"
                and plan["privacy_boundary"]["model_calls"] is False
                and plan["privacy_boundary"]["network_access"] is False,
                "metadata-only local replay",
                "metadata-only local replay"
                if plan["privacy_boundary"]["model_calls"] is False
                else "unexpected model-call boundary",
            ),
        ]
        failed = [check for check in checks if check["status"] == "fail"]

        return {
            "id": scenario.id,
            "status": "fail" if failed else "pass",
            "scenario": scenario.to_api(),
            "actual": actual,
            "checks": checks,
            "failures": [check["id"] for check in failed],
            "recommended_action": self._scenario_action(scenario, failed),
        }

    def _route_plan_payload(self, scenario: RoutePlanReplayScenario) -> dict[str, Any]:
        override: dict[str, Any] = {}
        if scenario.override_primary_task:
            override["primary_task"] = scenario.override_primary_task
        if scenario.override_primary_model:
            override["primary_model"] = scenario.override_primary_model
        if scenario.override_approval:
            override["allow_over_budget_model"] = True
        if not override:
            return {}
        return {"case_route_overrides": {scenario.case_id: override}}

    def _actual(self, plan: dict[str, Any], row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            return {
                "plan_status": plan["status"],
                "case_id": None,
                "document_type": None,
                "override_applied": False,
                "primary_task": None,
                "requested_model": None,
                "resolved_model": None,
                "cost_tier": None,
                "route_band": None,
                "routed_to_recommended_model": None,
                "blocking_check_ids": list(plan["blocking_check_ids"]),
                "warning_check_ids": list(plan["warning_check_ids"]),
            }
        return {
            "plan_status": plan["status"],
            "case_id": row["case_id"],
            "document_type": row["document_type"],
            "override_applied": row["override_applied"],
            "primary_task": row["primary_task"],
            "requested_model": row["primary_route"]["requested_model"],
            "resolved_model": row["primary_route"]["resolved_model"],
            "cost_tier": row["primary_route"]["cost_tier"],
            "route_band": row["route_band"],
            "routed_to_recommended_model": row["primary_route"]["routed_to_recommended_model"],
            "blocking_check_ids": list(plan["blocking_check_ids"]),
            "warning_check_ids": list(plan["warning_check_ids"]),
        }

    def _check(self, check_id: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
        return {
            "id": check_id,
            "status": "pass" if passed else "fail",
            "expected": expected,
            "actual": actual,
            "reason": "Scenario expectation matched the route-plan metadata."
            if passed
            else "Route-plan replay drifted from the expected cheap-first behavior.",
        }

    def _aggregate_checks(
        self,
        *,
        results: list[dict[str, Any]],
        failed: list[dict[str, Any]],
        premium_block_count: int,
        routed_to_recommended_count: int,
        require_complete_coverage: bool,
    ) -> list[dict[str, Any]]:
        premium_block_passed = premium_block_count >= 1 or not require_complete_coverage
        routed_to_recommended_passed = routed_to_recommended_count >= 1 or not require_complete_coverage
        return [
            {
                "id": "route-plan-replay-scenarios-pass",
                "status": "pass" if not failed else "fail",
                "reason": "All route-plan replay scenarios matched expected cheap-first metadata."
                if not failed
                else "One or more route-plan replay scenarios drifted.",
                "scenario_ids": [item["id"] for item in failed],
            },
            {
                "id": "premium-primary-block-replayed",
                "status": "pass" if premium_block_passed else "fail",
                "reason": "Replay includes an approved premium override that remains blocked."
                if premium_block_count >= 1
                else "Submitted scenario subset did not request premium-block coverage."
                if not require_complete_coverage
                else "Replay did not prove that premium benchmark primary routes remain blocked.",
                "scenario_ids": [
                    item["id"]
                    for item in results
                    if "no-premium-primary-defaults" in item["actual"]["blocking_check_ids"]
                ],
            },
            {
                "id": "unapproved-premium-routes-down",
                "status": "pass" if routed_to_recommended_passed else "fail",
                "reason": "Replay includes an unapproved premium override routed back to a budgeted model."
                if routed_to_recommended_count >= 1
                else "Submitted scenario subset did not request unapproved premium route-down coverage."
                if not require_complete_coverage
                else "Replay did not prove unapproved premium requests route back to a recommended model.",
                "scenario_ids": [
                    item["id"] for item in results if item["actual"]["routed_to_recommended_model"] is True
                ],
            },
            {
                "id": "metadata-only-boundary",
                "status": "pass",
                "reason": "Replay returns scenario and route metadata only; it does not execute models or gateways.",
                "scenario_ids": [item["id"] for item in results],
            },
        ]

    def _recommended_actions(self, failed: list[dict[str, Any]], blocking_check_ids: list[str]) -> list[str]:
        if failed or blocking_check_ids:
            return [
                "Review failing route-plan replay scenarios before relying on the benchmark route plan.",
                "Keep premium benchmark primary routes behind Flash-Lite prechecks until the replay passes.",
            ]
        return [
            "Use this replay before changing route-plan defaults or expanding benchmark execution.",
            "Keep real model execution as a separate reviewed handoff after metadata replay passes.",
        ]

    def _scenario_action(self, scenario: RoutePlanReplayScenario, failed: list[dict[str, Any]]) -> str:
        if failed:
            return f"Review scenario {scenario.id}; failing checks: {', '.join(check['id'] for check in failed)}."
        if scenario.expected_blocking_check_ids:
            return "Premium override remains blocked as expected."
        if scenario.expected_routed_to_recommended:
            return "Unapproved premium override routes back to the recommended budgeted model."
        return "Scenario remains aligned with cheap-first benchmark route expectations."

    def _scenarios(self, raw_scenarios: Any) -> list[RoutePlanReplayScenario]:
        if not isinstance(raw_scenarios, list):
            return list(self._default_scenarios())
        scenarios: list[RoutePlanReplayScenario] = []
        for index, item in enumerate(raw_scenarios[:MAX_SCENARIOS], start=1):
            if not isinstance(item, dict):
                continue
            scenarios.append(
                RoutePlanReplayScenario(
                    id=self._safe_token(item.get("id")) or f"submitted-route-plan-replay-{index}",
                    case_id=self._safe_case_id(item.get("case_id")) or "ldoc-contract-review-mini",
                    override_primary_task=self._safe_task(item.get("override_primary_task")),
                    override_primary_model=safe_model_id(item.get("override_primary_model")) or None,
                    override_approval=item.get("override_approval") is True,
                    expected_plan_status=self._safe_status(item.get("expected_plan_status")) or "ready",
                    expected_primary_task=self._safe_task(item.get("expected_primary_task")) or "review",
                    expected_resolved_model=safe_model_id(item.get("expected_resolved_model")) or "gemini-2.5-flash",
                    expected_cost_tier=self._safe_cost_tier(item.get("expected_cost_tier")) or "low",
                    expected_route_band=self._safe_route_band(item.get("expected_route_band"))
                    or "balanced_after_cheap_precheck",
                    expected_routed_to_recommended=item.get("expected_routed_to_recommended") is True,
                    expected_blocking_check_ids=tuple(
                        self._safe_check_id(check_id)
                        for check_id in (
                            item.get("expected_blocking_check_ids")
                            if isinstance(item.get("expected_blocking_check_ids"), list)
                            else []
                        )
                        if self._safe_check_id(check_id)
                    ),
                    rationale="Submitted metadata-only route-plan replay scenario; raw rationale is not echoed.",
                )
            )
        return scenarios or list(self._default_scenarios())

    def _default_scenarios(self) -> tuple[RoutePlanReplayScenario, ...]:
        return (
            RoutePlanReplayScenario(
                id="contract-review-default-balanced",
                case_id="ldoc-contract-review-mini",
                override_primary_task=None,
                override_primary_model=None,
                override_approval=False,
                expected_plan_status="ready",
                expected_primary_task="review",
                expected_resolved_model="gemini-2.5-flash",
                expected_cost_tier="low",
                expected_route_band="balanced_after_cheap_precheck",
                expected_routed_to_recommended=False,
                expected_blocking_check_ids=(),
                rationale="Default contract review route should remain balanced only after cheap prechecks.",
            ),
            RoutePlanReplayScenario(
                id="evidence-catalog-default-flash-lite",
                case_id="ldoc-evidence-catalog-mini",
                override_primary_task=None,
                override_primary_model=None,
                override_approval=False,
                expected_plan_status="ready",
                expected_primary_task="classification",
                expected_resolved_model="gemini-2.5-flash-lite",
                expected_cost_tier="lowest",
                expected_route_band="cheap_primary_after_precheck",
                expected_routed_to_recommended=False,
                expected_blocking_check_ids=(),
                rationale="Evidence catalog classification should stay on Flash-Lite.",
            ),
            RoutePlanReplayScenario(
                id="unapproved-premium-routes-to-recommended",
                case_id="ldoc-contract-review-mini",
                override_primary_task="review",
                override_primary_model="gemini-2.5-pro",
                override_approval=False,
                expected_plan_status="ready",
                expected_primary_task="review",
                expected_resolved_model="gemini-2.5-flash",
                expected_cost_tier="low",
                expected_route_band="balanced_after_cheap_precheck",
                expected_routed_to_recommended=True,
                expected_blocking_check_ids=(),
                rationale="Unapproved premium review requests should route back to the recommended Flash model.",
            ),
            RoutePlanReplayScenario(
                id="approved-premium-remains-blocked",
                case_id="ldoc-contract-review-mini",
                override_primary_task="review",
                override_primary_model="gemini-2.5-pro",
                override_approval=True,
                expected_plan_status="blocked",
                expected_primary_task="review",
                expected_resolved_model="gemini-2.5-pro",
                expected_cost_tier="premium",
                expected_route_band="blocked_premium_default",
                expected_routed_to_recommended=False,
                expected_blocking_check_ids=("no-premium-primary-defaults",),
                rationale="Even simulated approval must keep local benchmark premium primary routes blocked.",
            ),
            RoutePlanReplayScenario(
                id="legal-opinion-grounded-flash-lite",
                case_id="ldoc-legal-opinion-mini",
                override_primary_task=None,
                override_primary_model=None,
                override_approval=False,
                expected_plan_status="ready",
                expected_primary_task="grounded-research",
                expected_resolved_model="gemini-3.1-flash-lite",
                expected_cost_tier="lowest",
                expected_route_band="cheap_grounded_or_structured",
                expected_routed_to_recommended=False,
                expected_blocking_check_ids=(),
                rationale="Grounded legal-opinion smoke evidence should stay on the cheapest grounded route.",
            ),
        )

    def _sensitive_scenario_count(self, raw_scenarios: Any) -> int:
        if not isinstance(raw_scenarios, list):
            return 0
        return sum(1 for item in raw_scenarios[:MAX_SCENARIOS] if self._contains_sensitive_value(item))

    def _contains_sensitive_value(self, value: Any) -> bool:
        if isinstance(value, dict):
            return any(self._contains_sensitive_value(child) for child in value.values())
        if isinstance(value, (list, tuple, set)):
            return any(self._contains_sensitive_value(child) for child in value)
        if value is None:
            return False
        return bool(SENSITIVE_VALUE_PATTERN.search(str(value)[:4096]))

    def _safe_token(self, value: Any) -> str:
        if self._contains_sensitive_value(value):
            return ""
        raw = str(value or "").strip().lower()[:100]
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")

    def _safe_case_id(self, value: Any) -> str:
        token = self._safe_token(value)
        return token if token.startswith("ldoc-") else ""

    def _safe_task(self, value: Any) -> str | None:
        token = self._safe_token(value).replace("_", "-")
        if token in {"classification", "fast", "review", "document-generation", "grounded-research", "pdf"}:
            return token
        return None

    def _safe_status(self, value: Any) -> str:
        token = self._safe_token(value).replace("-", "_")
        if token in {"ready", "ready_with_review", "blocked"}:
            return token
        return ""

    def _safe_cost_tier(self, value: Any) -> str:
        token = self._safe_token(value)
        if token in {"lowest", "low", "medium", "premium", "unverified"}:
            return token
        return ""

    def _safe_route_band(self, value: Any) -> str:
        token = self._safe_token(value).replace("-", "_")
        if token in {
            "cheap_primary_after_precheck",
            "cheap_grounded_or_structured",
            "balanced_after_cheap_precheck",
            "blocked_premium_default",
        }:
            return token
        return ""

    def _safe_check_id(self, value: Any) -> str:
        token = self._safe_token(value)
        return token if token in {"no-premium-primary-defaults"} else ""
