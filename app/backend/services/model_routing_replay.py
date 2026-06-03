from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_catalog import model_profile
from services.model_escalation_policy import ModelEscalationPolicyService


COST_RANK = {"lowest": 0, "low": 1, "medium": 2, "premium": 3, "unknown": 99}


@dataclass(frozen=True)
class RoutingReplayScenario:
    id: str
    task: str
    signals: tuple[str, ...]
    expected_decision: str
    max_cost_tier: str
    expected_operator_review: bool
    rationale: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["signals"] = list(self.signals)
        return data


class ModelRoutingReplayService:
    """Replay deterministic routing scenarios to catch cheap-first regressions."""

    def __init__(self, escalation_policy: ModelEscalationPolicyService | None = None) -> None:
        self.escalation_policy = escalation_policy or ModelEscalationPolicyService()

    def run_replay(self) -> dict[str, Any]:
        results = [self._run_scenario(scenario) for scenario in self._scenarios()]
        failed = [item for item in results if item["status"] == "fail"]
        warnings = [item for item in results if item["status"] == "warn"]

        return {
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "method": {
                "type": "deterministic-routing-replay",
                "notes": [
                    "Scenarios replay expected legal workflow routing decisions without calling an AI model.",
                    "The replay checks decision type, model cost tier, and operator-review requirements.",
                    "No prompts, documents, user identifiers, or credentials are stored in replay fixtures.",
                ],
            },
            "summary": {
                "scenario_count": len(results),
                "passed_count": sum(1 for item in results if item["status"] == "pass"),
                "warning_count": len(warnings),
                "failed_count": len(failed),
                "cheap_start_count": sum(
                    1
                    for item in results
                    if item["actual"].get("decision") == "continue"
                    and item["actual"].get("cost_tier") in {"lowest", "low"}
                ),
                "premium_operator_review_count": sum(
                    1
                    for item in results
                    if item["actual"].get("cost_tier") == "premium"
                    and item["actual"].get("requires_operator_review")
                ),
                "hard_stop_count": sum(1 for item in results if item["actual"].get("decision") == "stop"),
            },
            "scenarios": results,
        }

    def _run_scenario(self, scenario: RoutingReplayScenario) -> dict[str, Any]:
        evaluation = self.escalation_policy.evaluate(scenario.task, scenario.signals)
        next_step = evaluation.get("next_step") or {}
        model_id = next_step.get("resolved_model")
        profile = model_profile(model_id) if model_id else None
        cost_tier = profile.cost_tier if profile else ("none" if model_id is None else "unknown")
        requires_operator_review = bool(next_step.get("requires_operator_review", False))

        check_results = [
            self._check_decision(evaluation.get("decision"), scenario.expected_decision),
            self._check_cost_tier(cost_tier, scenario.max_cost_tier),
            self._check_operator_review(requires_operator_review, scenario.expected_operator_review),
            self._check_stop_has_no_model(evaluation.get("decision"), model_id),
        ]
        failed = [check for check in check_results if check["status"] == "fail"]
        warnings = [check for check in check_results if check["status"] == "warn"]

        return {
            "id": scenario.id,
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "scenario": scenario.to_api(),
            "actual": {
                "decision": evaluation.get("decision"),
                "resolved_model": model_id,
                "cost_tier": cost_tier,
                "requires_operator_review": requires_operator_review,
                "reasons": evaluation.get("reasons", []),
            },
            "checks": check_results,
            "recommended_action": self._recommended_action(failed, warnings, scenario),
        }

    def _check_decision(self, actual: str | None, expected: str) -> dict[str, Any]:
        return {
            "id": "decision",
            "status": "pass" if actual == expected else "fail",
            "expected": expected,
            "actual": actual,
            "reason": "Routing decision matches scenario expectation."
            if actual == expected
            else "Routing decision drifted from the expected cheap-first cascade behavior.",
        }

    def _check_cost_tier(self, actual: str, max_allowed: str) -> dict[str, Any]:
        if actual == "none":
            return {
                "id": "cost-tier",
                "status": "pass",
                "expected": f"<= {max_allowed}",
                "actual": actual,
                "reason": "Hard-stop scenarios do not spend model budget.",
            }
        actual_rank = COST_RANK.get(actual, COST_RANK["unknown"])
        allowed_rank = COST_RANK.get(max_allowed, COST_RANK["unknown"])
        if actual == "unknown":
            status = "warn"
        else:
            status = "pass" if actual_rank <= allowed_rank else "fail"
        return {
            "id": "cost-tier",
            "status": status,
            "expected": f"<= {max_allowed}",
            "actual": actual,
            "reason": "Selected model stays within scenario budget."
            if status == "pass"
            else (
                "Selected model is not in the priced catalog; verify gateway billing before making it a default."
                if status == "warn"
                else "Selected model exceeds the scenario budget."
            ),
        }

    def _check_operator_review(self, actual: bool, expected: bool) -> dict[str, Any]:
        return {
            "id": "operator-review",
            "status": "pass" if actual == expected else "fail",
            "expected": expected,
            "actual": actual,
            "reason": "Operator-review requirement matches premium exception policy."
            if actual == expected
            else "Operator-review requirement changed and may allow premium spend without review.",
        }

    def _check_stop_has_no_model(self, decision: str | None, model_id: str | None) -> dict[str, Any]:
        if decision != "stop":
            return {
                "id": "stop-spend",
                "status": "pass",
                "expected": "not-applicable",
                "actual": "not-applicable",
                "reason": "Scenario is not a hard stop.",
            }
        return {
            "id": "stop-spend",
            "status": "pass" if model_id is None else "fail",
            "expected": None,
            "actual": model_id,
            "reason": "Hard-stop signals avoid extra model calls."
            if model_id is None
            else "Hard-stop scenario still selected a model.",
        }

    def _recommended_action(
        self,
        failed: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        scenario: RoutingReplayScenario,
    ) -> str:
        if failed:
            failed_ids = ", ".join(check["id"] for check in failed)
            return f"Review routing policy for {scenario.id}; failing checks: {failed_ids}."
        if warnings:
            warning_ids = ", ".join(check["id"] for check in warnings)
            return f"Verify gateway pricing before promoting this route; warnings: {warning_ids}."
        return "Route is aligned with the expected cheap-first policy."

    def _scenarios(self) -> tuple[RoutingReplayScenario, ...]:
        return (
            RoutingReplayScenario(
                id="fast-clean-starts-cheap",
                task="fast",
                signals=(),
                expected_decision="continue",
                max_cost_tier="lowest",
                expected_operator_review=False,
                rationale="Routine preflight and triage should start on the cheapest text/JSON-capable model.",
            ),
            RoutingReplayScenario(
                id="fast-low-confidence-verifies-balanced",
                task="fast",
                signals=("low_confidence",),
                expected_decision="verify",
                max_cost_tier="low",
                expected_operator_review=False,
                rationale="Low confidence should verify with balanced review before any premium exception.",
            ),
            RoutingReplayScenario(
                id="ocr-clean-starts-cheap",
                task="ocr",
                signals=(),
                expected_decision="continue",
                max_cost_tier="lowest",
                expected_operator_review=False,
                rationale="Routine OCR and extraction assist should start on the cheapest vision-capable model.",
            ),
            RoutingReplayScenario(
                id="classification-schema-failure-retries-balanced",
                task="classification",
                signals=("schema_missing_required",),
                expected_decision="escalate",
                max_cost_tier="low",
                expected_operator_review=False,
                rationale="Schema failures may retry on the balanced model but should not jump to premium.",
            ),
            RoutingReplayScenario(
                id="ocr-uncertain-verifies-balanced",
                task="ocr",
                signals=("ocr_uncertain",),
                expected_decision="verify",
                max_cost_tier="low",
                expected_operator_review=False,
                rationale="Uncertain OCR should verify extraction quality with a balanced model.",
            ),
            RoutingReplayScenario(
                id="review-citation-failure-premium-reviewed",
                task="review",
                signals=("citation_audit_fail",),
                expected_decision="escalate",
                max_cost_tier="premium",
                expected_operator_review=True,
                rationale="Citation audit failure can justify a premium exception only with operator review.",
            ),
            RoutingReplayScenario(
                id="review-weak-citations-premium-reviewed",
                task="review",
                signals=("weak_citations",),
                expected_decision="verify",
                max_cost_tier="premium",
                expected_operator_review=True,
                rationale="Weak citations can request premium verification but must keep an operator-review gate.",
            ),
            RoutingReplayScenario(
                id="privacy-hard-stop",
                task="review",
                signals=("privacy_high",),
                expected_decision="stop",
                max_cost_tier="lowest",
                expected_operator_review=False,
                rationale="High privacy risk should stop before spending more model budget.",
            ),
            RoutingReplayScenario(
                id="pdf-clean-premium-exception",
                task="pdf",
                signals=(),
                expected_decision="continue",
                max_cost_tier="premium",
                expected_operator_review=False,
                rationale="Large PDF and final-review work is the explicit premium exception path.",
            ),
            RoutingReplayScenario(
                id="pdf-extraction-failure-hard-stop",
                task="pdf",
                signals=("extraction_quality_fail",),
                expected_decision="stop",
                max_cost_tier="lowest",
                expected_operator_review=False,
                rationale="Failed extraction quality should stop before a costly PDF review call.",
            ),
        )
