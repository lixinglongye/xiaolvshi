from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from services.model_catalog import (
    estimate_token_cost_usd,
    model_profile,
    premium_text_model,
    resolve_model,
)
from services.model_cost_forecast import ModelCostForecastService
from services.model_escalation_policy import ModelEscalationPolicyService
from services.model_routing_replay import ModelRoutingReplayService


COST_TIER_RANK = {"lowest": 0, "low": 1, "medium": 2, "premium": 3, "unknown": 99}


@dataclass(frozen=True)
class CostRegressionThreshold:
    warn_min_savings_ratio: float
    fail_min_savings_ratio: float
    warn_max_monthly_cost_usd: float
    fail_max_monthly_cost_usd: float
    max_initial_cost_tier: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CostRegressionScenario:
    id: str
    task: str
    display_name: str
    monthly_units: int
    prompt_tokens_per_unit: int
    completion_tokens_per_unit: int
    expected_escalation_rate: float
    escalation_signals: tuple[str, ...]
    premium_baseline_alias: str
    threshold: CostRegressionThreshold
    rationale: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["escalation_signals"] = list(self.escalation_signals)
        data["threshold"] = self.threshold.to_api()
        return data


class ModelCostRegressionSnapshotService:
    """Build deterministic cost regression snapshots for cheap-first model routing."""

    def __init__(
        self,
        *,
        forecast_service: ModelCostForecastService | None = None,
        routing_replay_service: ModelRoutingReplayService | None = None,
        escalation_policy: ModelEscalationPolicyService | None = None,
    ) -> None:
        self.forecast_service = forecast_service or ModelCostForecastService()
        self.routing_replay_service = routing_replay_service or ModelRoutingReplayService()
        self.escalation_policy = escalation_policy or ModelEscalationPolicyService()

    def build_snapshots(
        self,
        *,
        model_overrides: Mapping[str, str] | None = None,
        threshold_overrides: Mapping[str, Mapping[str, float | str]] | None = None,
    ) -> dict[str, Any]:
        """Return local-only cost snapshots and drift checks.

        ``model_overrides`` and ``threshold_overrides`` are intended for tests and
        release dry-runs. They do not read environment variables, call networks, or
        persist any supplied value.
        """

        forecast = self.forecast_service.build_forecast()
        routing_replay = self.routing_replay_service.run_replay()
        scenarios = self._scenarios(threshold_overrides or {})
        snapshots = [self._snapshot(scenario, model_overrides or {}) for scenario in scenarios]
        regression_checks = self._regression_checks(snapshots, forecast, routing_replay)

        failed = [
            check
            for snapshot in snapshots
            for check in snapshot["checks"]
            if check["status"] == "fail"
        ] + [check for check in regression_checks if check["status"] == "fail"]
        warnings = [
            check
            for snapshot in snapshots
            for check in snapshot["checks"]
            if check["status"] == "warn"
        ] + [check for check in regression_checks if check["status"] == "warn"]
        total_cheap = round(sum(snapshot["cheap_first_monthly_cost_usd"] or 0 for snapshot in snapshots), 6)
        total_baseline = round(sum(snapshot["premium_baseline_monthly_cost_usd"] or 0 for snapshot in snapshots), 6)

        return {
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "method": {
                "type": "deterministic-model-cost-regression-snapshots",
                "source_basis": [
                    "Local model catalog pricing and cost tiers.",
                    "Cost forecast profile volumes and token-shape assumptions.",
                    "Routing replay expectations for cheap-first escalation behavior.",
                ],
                "drift_thresholds": {
                    "savings_ratio": "warn below warn_min_savings_ratio; fail below fail_min_savings_ratio",
                    "monthly_cost": "warn above warn_max_monthly_cost_usd; fail above fail_max_monthly_cost_usd",
                    "initial_cost_tier": "fail when the first model exceeds the scenario max_initial_cost_tier",
                },
            },
            "summary": {
                "snapshot_count": len(snapshots),
                "passed_count": sum(1 for snapshot in snapshots if snapshot["status"] == "pass"),
                "warning_count": sum(1 for snapshot in snapshots if snapshot["status"] == "warn"),
                "failed_count": sum(1 for snapshot in snapshots if snapshot["status"] == "fail"),
                "regression_check_count": len(regression_checks),
                "cheap_first_monthly_cost_usd": total_cheap,
                "premium_baseline_monthly_cost_usd": total_baseline,
                "estimated_savings_usd": _savings_usd(total_cheap, total_baseline),
                "estimated_savings_ratio": _savings_ratio(total_cheap, total_baseline),
                "forecast_status": forecast.get("status"),
                "routing_replay_status": routing_replay.get("status"),
            },
            "snapshots": snapshots,
            "regression_checks": regression_checks,
            "recommended_actions": self._recommended_actions(snapshots, regression_checks),
            "privacy_note": (
                "Snapshots use fixed synthetic volumes, token counts, model ids, and status metadata only. "
                "They never store prompts, legal documents, user identifiers, API keys, or gateway credentials."
            ),
            "validation_commands": [
                "cd app/backend",
                "python -m pytest tests/test_model_cost_regression_snapshots.py -q",
            ],
        }

    def _snapshot(
        self,
        scenario: CostRegressionScenario,
        model_overrides: Mapping[str, str],
    ) -> dict[str, Any]:
        initial_model = model_overrides.get(scenario.task) or resolve_model(None, task=scenario.task)
        escalation_model = (
            model_overrides.get(f"{scenario.task}:escalation")
            or self._escalation_model(scenario.task, scenario.escalation_signals)
        )
        baseline_model = (
            model_overrides.get(f"{scenario.task}:baseline")
            or resolve_model(scenario.premium_baseline_alias, task=scenario.task)
            or premium_text_model()
        )

        initial_unit_cost = estimate_token_cost_usd(
            initial_model,
            scenario.prompt_tokens_per_unit,
            scenario.completion_tokens_per_unit,
        )
        escalation_unit_cost = estimate_token_cost_usd(
            escalation_model,
            scenario.prompt_tokens_per_unit,
            scenario.completion_tokens_per_unit,
        )
        baseline_unit_cost = estimate_token_cost_usd(
            baseline_model,
            scenario.prompt_tokens_per_unit,
            scenario.completion_tokens_per_unit,
        )
        cheap_first_monthly = _cascade_monthly_cost(
            initial_unit_cost,
            escalation_unit_cost,
            scenario.monthly_units,
            scenario.expected_escalation_rate,
        )
        baseline_monthly = _monthly_cost(baseline_unit_cost, scenario.monthly_units)
        savings_ratio = _savings_ratio(cheap_first_monthly, baseline_monthly)
        savings_usd = _savings_usd(cheap_first_monthly, baseline_monthly)

        checks = [
            self._priced_models_check(initial_unit_cost, escalation_unit_cost, baseline_unit_cost),
            self._savings_check(scenario.threshold, savings_ratio),
            self._monthly_cost_check(scenario.threshold, cheap_first_monthly),
            self._initial_cost_tier_check(scenario.threshold, initial_model),
            self._baseline_check(initial_model, baseline_model, cheap_first_monthly, baseline_monthly),
        ]
        failed = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]

        return {
            "id": scenario.id,
            "task": scenario.task,
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "scenario": scenario.to_api(),
            "current": {
                "initial_model": initial_model,
                "initial_cost_tier": self._cost_tier(initial_model),
                "escalation_model": escalation_model,
                "escalation_cost_tier": self._cost_tier(escalation_model),
                "premium_baseline_model": baseline_model,
                "premium_baseline_cost_tier": self._cost_tier(baseline_model),
                "expected_escalation_rate": scenario.expected_escalation_rate,
            },
            "initial_unit_cost_usd": initial_unit_cost,
            "escalation_unit_cost_usd": escalation_unit_cost,
            "premium_baseline_unit_cost_usd": baseline_unit_cost,
            "cheap_first_monthly_cost_usd": cheap_first_monthly,
            "premium_baseline_monthly_cost_usd": baseline_monthly,
            "estimated_savings_usd": savings_usd,
            "estimated_savings_ratio": savings_ratio,
            "checks": checks,
            "recommended_action": self._snapshot_action(failed, warnings, scenario),
        }

    def _regression_checks(
        self,
        snapshots: list[dict[str, Any]],
        forecast: dict[str, Any],
        routing_replay: dict[str, Any],
    ) -> list[dict[str, Any]]:
        forecast_tasks = {
            row.get("task")
            for row in forecast.get("profiles", [])
            if isinstance(row, dict) and row.get("task")
        }
        snapshot_tasks = {snapshot["task"] for snapshot in snapshots}
        missing_from_forecast = sorted(snapshot_tasks - forecast_tasks)
        routing_status = routing_replay.get("status")
        high_volume_failures = [
            snapshot["id"]
            for snapshot in snapshots
            if snapshot["task"] in {"fast", "classification", "ocr"}
            and snapshot["current"]["initial_cost_tier"] not in {"lowest", "low"}
        ]

        return [
            {
                "id": "forecast-profile-coverage",
                "status": "pass" if not missing_from_forecast else "warn",
                "expected": sorted(snapshot_tasks),
                "actual": sorted(forecast_tasks),
                "reason": "All snapshot tasks are represented in the local cost forecast."
                if not missing_from_forecast
                else f"Snapshot tasks missing from forecast profiles: {', '.join(missing_from_forecast)}.",
            },
            {
                "id": "routing-replay-health",
                "status": "pass" if routing_status == "pass" else ("fail" if routing_status == "fail" else "warn"),
                "expected": "pass",
                "actual": routing_status,
                "reason": "Routing replay agrees with cheap-first expectations."
                if routing_status == "pass"
                else "Routing replay drift can invalidate cost snapshots.",
            },
            {
                "id": "high-volume-default-tier",
                "status": "fail" if high_volume_failures else "pass",
                "expected": "fast/classification/ocr initial tiers in lowest or low",
                "actual": high_volume_failures,
                "reason": "High-volume tasks still start on low-cost models."
                if not high_volume_failures
                else "High-volume tasks moved to medium or premium defaults.",
            },
        ]

    def _scenarios(
        self,
        threshold_overrides: Mapping[str, Mapping[str, float | str]],
    ) -> tuple[CostRegressionScenario, ...]:
        scenarios = (
            CostRegressionScenario(
                id="fast-routing-5000",
                task="fast",
                display_name="Preflight, routing, and light extraction",
                monthly_units=5_000,
                prompt_tokens_per_unit=1_200,
                completion_tokens_per_unit=180,
                expected_escalation_rate=0.04,
                escalation_signals=("low_confidence",),
                premium_baseline_alias="auto-pdf",
                threshold=CostRegressionThreshold(
                    warn_min_savings_ratio=0.70,
                    fail_min_savings_ratio=0.50,
                    warn_max_monthly_cost_usd=3.0,
                    fail_max_monthly_cost_usd=6.0,
                    max_initial_cost_tier="lowest",
                ),
                rationale="Fast workflow traffic is frequent and should preserve very high savings against a premium-only baseline.",
            ),
            CostRegressionScenario(
                id="classification-2500",
                task="classification",
                display_name="Material classification",
                monthly_units=2_500,
                prompt_tokens_per_unit=1_600,
                completion_tokens_per_unit=220,
                expected_escalation_rate=0.06,
                escalation_signals=("schema_missing_required",),
                premium_baseline_alias="auto-pdf",
                threshold=CostRegressionThreshold(
                    warn_min_savings_ratio=0.70,
                    fail_min_savings_ratio=0.50,
                    warn_max_monthly_cost_usd=2.5,
                    fail_max_monthly_cost_usd=5.0,
                    max_initial_cost_tier="lowest",
                ),
                rationale="Classifier defaults should remain cheap because it runs before expensive legal review.",
            ),
            CostRegressionScenario(
                id="ocr-extraction-3500",
                task="ocr",
                display_name="OCR and extraction assist",
                monthly_units=3_500,
                prompt_tokens_per_unit=1_800,
                completion_tokens_per_unit=260,
                expected_escalation_rate=0.08,
                escalation_signals=("ocr_uncertain",),
                premium_baseline_alias="auto-pdf",
                threshold=CostRegressionThreshold(
                    warn_min_savings_ratio=0.70,
                    fail_min_savings_ratio=0.50,
                    warn_max_monthly_cost_usd=3.0,
                    fail_max_monthly_cost_usd=6.0,
                    max_initial_cost_tier="lowest",
                ),
                rationale="OCR runs per page or chunk, so model cost drift compounds quickly.",
            ),
            CostRegressionScenario(
                id="review-quality-450",
                task="review",
                display_name="Balanced legal review",
                monthly_units=450,
                prompt_tokens_per_unit=22_000,
                completion_tokens_per_unit=5_500,
                expected_escalation_rate=0.12,
                escalation_signals=("quality_gate_fail",),
                premium_baseline_alias="auto-pdf",
                threshold=CostRegressionThreshold(
                    warn_min_savings_ratio=0.30,
                    fail_min_savings_ratio=0.10,
                    warn_max_monthly_cost_usd=20.0,
                    fail_max_monthly_cost_usd=30.0,
                    max_initial_cost_tier="low",
                ),
                rationale="Routine review can use balanced models, but premium escalation should remain an exception path.",
            ),
            CostRegressionScenario(
                id="pdf-premium-exception-80",
                task="pdf",
                display_name="Large PDF and final review",
                monthly_units=80,
                prompt_tokens_per_unit=110_000,
                completion_tokens_per_unit=12_000,
                expected_escalation_rate=0.0,
                escalation_signals=(),
                premium_baseline_alias="auto-pdf",
                threshold=CostRegressionThreshold(
                    warn_min_savings_ratio=0.0,
                    fail_min_savings_ratio=-0.01,
                    warn_max_monthly_cost_usd=120.0,
                    fail_max_monthly_cost_usd=150.0,
                    max_initial_cost_tier="premium",
                ),
                rationale="Large PDFs are explicit premium exceptions; the regression guard keeps their volume visible.",
            ),
        )
        return tuple(self._apply_threshold_overrides(scenario, threshold_overrides) for scenario in scenarios)

    def _apply_threshold_overrides(
        self,
        scenario: CostRegressionScenario,
        threshold_overrides: Mapping[str, Mapping[str, float | str]],
    ) -> CostRegressionScenario:
        overrides = threshold_overrides.get(scenario.id) or threshold_overrides.get(scenario.task)
        if not overrides:
            return scenario
        allowed = set(CostRegressionThreshold.__dataclass_fields__)
        threshold = replace(
            scenario.threshold,
            **{key: value for key, value in overrides.items() if key in allowed},
        )
        return replace(scenario, threshold=threshold)

    def _priced_models_check(
        self,
        initial_unit_cost: float | None,
        escalation_unit_cost: float | None,
        baseline_unit_cost: float | None,
    ) -> dict[str, Any]:
        missing = [
            name
            for name, value in (
                ("initial", initial_unit_cost),
                ("escalation", escalation_unit_cost),
                ("premium-baseline", baseline_unit_cost),
            )
            if value is None
        ]
        return {
            "id": "priced-models",
            "status": "fail" if missing else "pass",
            "expected": "all models priced in local catalog",
            "actual": missing,
            "reason": "All selected models have local pricing metadata."
            if not missing
            else "Add catalog pricing before using this snapshot for release decisions.",
        }

    def _savings_check(
        self,
        threshold: CostRegressionThreshold,
        savings_ratio: float | None,
    ) -> dict[str, Any]:
        if savings_ratio is None:
            status = "fail"
            reason = "Savings ratio cannot be computed without priced current and baseline models."
        elif savings_ratio < threshold.fail_min_savings_ratio:
            status = "fail"
            reason = "Cheap-first savings fell below the fail threshold."
        elif savings_ratio < threshold.warn_min_savings_ratio:
            status = "warn"
            reason = "Cheap-first savings fell below the warning threshold."
        else:
            status = "pass"
            reason = "Cheap-first savings remain above configured drift thresholds."
        return {
            "id": "savings-ratio",
            "status": status,
            "expected": {
                "warn_min_savings_ratio": threshold.warn_min_savings_ratio,
                "fail_min_savings_ratio": threshold.fail_min_savings_ratio,
            },
            "actual": savings_ratio,
            "reason": reason,
        }

    def _monthly_cost_check(
        self,
        threshold: CostRegressionThreshold,
        cheap_first_monthly: float | None,
    ) -> dict[str, Any]:
        if cheap_first_monthly is None:
            status = "fail"
            reason = "Monthly cost cannot be computed without local pricing metadata."
        elif cheap_first_monthly > threshold.fail_max_monthly_cost_usd:
            status = "fail"
            reason = "Cheap-first monthly cost exceeded the fail threshold."
        elif cheap_first_monthly > threshold.warn_max_monthly_cost_usd:
            status = "warn"
            reason = "Cheap-first monthly cost exceeded the warning threshold."
        else:
            status = "pass"
            reason = "Cheap-first monthly cost remains within drift thresholds."
        return {
            "id": "monthly-cost",
            "status": status,
            "expected": {
                "warn_max_monthly_cost_usd": threshold.warn_max_monthly_cost_usd,
                "fail_max_monthly_cost_usd": threshold.fail_max_monthly_cost_usd,
            },
            "actual": cheap_first_monthly,
            "reason": reason,
        }

    def _initial_cost_tier_check(
        self,
        threshold: CostRegressionThreshold,
        initial_model: str,
    ) -> dict[str, Any]:
        actual = self._cost_tier(initial_model)
        actual_rank = COST_TIER_RANK.get(actual, COST_TIER_RANK["unknown"])
        allowed_rank = COST_TIER_RANK.get(threshold.max_initial_cost_tier, COST_TIER_RANK["unknown"])
        if actual == "unknown":
            status = "warn"
            reason = "Initial model is not in the local catalog; verify gateway pricing before release."
        elif actual_rank > allowed_rank:
            status = "fail"
            reason = "Initial model cost tier exceeded the snapshot threshold."
        else:
            status = "pass"
            reason = "Initial model cost tier is within the snapshot threshold."
        return {
            "id": "initial-cost-tier",
            "status": status,
            "expected": f"<= {threshold.max_initial_cost_tier}",
            "actual": actual,
            "reason": reason,
        }

    def _baseline_check(
        self,
        initial_model: str,
        baseline_model: str,
        cheap_first_monthly: float | None,
        baseline_monthly: float | None,
    ) -> dict[str, Any]:
        baseline_tier = self._cost_tier(baseline_model)
        if baseline_tier != "premium":
            status = "fail"
            reason = "Baseline model is not premium, so the premium-only comparison is invalid."
        elif cheap_first_monthly is None or baseline_monthly is None:
            status = "fail"
            reason = "Baseline comparison cannot be computed without pricing metadata."
        elif initial_model != baseline_model and cheap_first_monthly >= baseline_monthly:
            status = "fail"
            reason = "Cheap-first route is not cheaper than the premium-only baseline."
        else:
            status = "pass"
            reason = "Premium-only baseline is valid for this snapshot."
        return {
            "id": "premium-baseline",
            "status": status,
            "expected": "premium baseline and cheap-first cost <= baseline",
            "actual": {
                "initial_model": initial_model,
                "baseline_model": baseline_model,
                "baseline_cost_tier": baseline_tier,
            },
            "reason": reason,
        }

    def _escalation_model(self, task: str, signals: tuple[str, ...]) -> str:
        evaluation = self.escalation_policy.evaluate(task, signals)
        next_step = evaluation.get("next_step") or {}
        if isinstance(next_step, dict) and next_step.get("resolved_model"):
            return str(next_step["resolved_model"])
        return resolve_model(None, task=task) or premium_text_model()

    def _cost_tier(self, model_id: str | None) -> str:
        profile = model_profile(model_id or "")
        return profile.cost_tier if profile else "unknown"

    def _snapshot_action(
        self,
        failed: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        scenario: CostRegressionScenario,
    ) -> str:
        if failed:
            return f"Block release until {scenario.id} cost drift is reviewed: {_check_ids(failed)}."
        if warnings:
            return f"Review {scenario.id} before changing model defaults: {_check_ids(warnings)}."
        return "Snapshot is within cheap-first cost regression thresholds."

    def _recommended_actions(
        self,
        snapshots: list[dict[str, Any]],
        regression_checks: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            snapshot["recommended_action"]
            for snapshot in snapshots
            if snapshot["status"] in {"warn", "fail"}
        ]
        actions.extend(
            f"Review regression check {check['id']}: {check['reason']}"
            for check in regression_checks
            if check["status"] in {"warn", "fail"}
        )
        if not actions:
            return [
                "Keep cheap-first defaults for fast, classification, and OCR tasks.",
                "Continue treating large PDF review as an explicit premium exception.",
                "Run these snapshots before changing model defaults or gateway pricing assumptions.",
            ]
        return actions


def _monthly_cost(unit_cost: float | None, monthly_units: int) -> float | None:
    if unit_cost is None:
        return None
    return round(unit_cost * max(0, monthly_units), 6)


def _cascade_monthly_cost(
    initial_unit_cost: float | None,
    escalation_unit_cost: float | None,
    monthly_units: int,
    escalation_rate: float,
) -> float | None:
    if initial_unit_cost is None or escalation_unit_cost is None:
        return None
    units = max(0, monthly_units)
    rate = max(0.0, min(1.0, escalation_rate))
    return round(units * initial_unit_cost + units * rate * escalation_unit_cost, 6)


def _savings_ratio(cheap_first_cost: float | None, baseline_cost: float | None) -> float | None:
    if cheap_first_cost is None or baseline_cost is None or baseline_cost <= 0:
        return None
    return round((baseline_cost - cheap_first_cost) / baseline_cost, 4)


def _savings_usd(cheap_first_cost: float | None, baseline_cost: float | None) -> float | None:
    if cheap_first_cost is None or baseline_cost is None:
        return None
    return round(baseline_cost - cheap_first_cost, 6)


def _check_ids(checks: list[dict[str, Any]]) -> str:
    return ", ".join(str(check["id"]) for check in checks)
