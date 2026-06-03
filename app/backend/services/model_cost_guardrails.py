from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_catalog import model_profile


@dataclass(frozen=True)
class CostGuardrailThresholds:
    monthly_budget_usd: float = 100.0
    warn_budget_ratio: float = 0.7
    fail_budget_ratio: float = 1.0
    warn_failure_rate: float = 0.08
    fail_failure_rate: float = 0.2
    warn_premium_request_ratio: float = 0.2
    fail_premium_request_ratio: float = 0.4
    warn_unpriced_model_count: int = 1
    fail_unpriced_model_count: int = 3

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class ModelCostGuardrailService:
    """Evaluate model usage and forecast data against cost-control guardrails."""

    def evaluate(
        self,
        usage_snapshot: dict[str, Any],
        cost_forecast: dict[str, Any],
        thresholds: CostGuardrailThresholds | None = None,
    ) -> dict[str, Any]:
        thresholds = thresholds or CostGuardrailThresholds()
        totals = _dict(usage_snapshot.get("totals"))
        models = _dict(usage_snapshot.get("models"))
        forecast_summary = _dict(cost_forecast.get("summary"))

        checks = [
            self._budget_check(totals, forecast_summary, thresholds),
            self._failure_rate_check(totals, thresholds),
            self._premium_ratio_check(models, totals, thresholds),
            self._unpriced_model_check(totals, thresholds),
            self._forecast_savings_check(forecast_summary),
        ]
        status = self._status(checks)

        return {
            "status": status,
            "thresholds": thresholds.to_api(),
            "summary": {
                "request_count": _int(totals.get("requests")),
                "estimated_cost_usd": _float(totals.get("estimated_cost_usd")),
                "forecast_cheap_first_monthly_cost_usd": _float(
                    forecast_summary.get("cheap_first_monthly_cost_usd")
                ),
                "forecast_premium_baseline_monthly_cost_usd": _float(
                    forecast_summary.get("premium_baseline_monthly_cost_usd")
                ),
                "forecast_savings_ratio": forecast_summary.get("estimated_savings_ratio"),
                "premium_request_ratio": self._premium_request_ratio(models, totals),
                "failure_rate": self._failure_rate(totals),
                "unpriced_model_count": _int(totals.get("unpriced_model_count")),
            },
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in checks if check["status"] == "fail"],
            "warning_check_ids": [check["id"] for check in checks if check["status"] == "warn"],
            "recommended_actions": self._recommended_actions(checks),
        }

    def _budget_check(
        self,
        totals: dict[str, Any],
        forecast_summary: dict[str, Any],
        thresholds: CostGuardrailThresholds,
    ) -> dict[str, Any]:
        actual = _float(totals.get("estimated_cost_usd"))
        forecast = _float(forecast_summary.get("cheap_first_monthly_cost_usd"))
        budget = thresholds.monthly_budget_usd
        ratio = actual / budget if budget > 0 else 0.0
        status = "pass"
        if ratio >= thresholds.fail_budget_ratio:
            status = "fail"
        elif ratio >= thresholds.warn_budget_ratio:
            status = "warn"
        return {
            "id": "actual-cost-budget",
            "status": status,
            "value": round(actual, 6),
            "ratio": round(ratio, 4),
            "limit": budget,
            "forecast_reference_usd": round(forecast, 6),
            "reason": "In-process estimated cost compared with monthly budget threshold.",
        }

    def _failure_rate_check(self, totals: dict[str, Any], thresholds: CostGuardrailThresholds) -> dict[str, Any]:
        failure_rate = self._failure_rate(totals)
        status = "pass"
        if failure_rate >= thresholds.fail_failure_rate:
            status = "fail"
        elif failure_rate >= thresholds.warn_failure_rate:
            status = "warn"
        return {
            "id": "model-failure-rate",
            "status": status,
            "value": round(failure_rate, 4),
            "warn_threshold": thresholds.warn_failure_rate,
            "fail_threshold": thresholds.fail_failure_rate,
            "reason": "High failure rate can cause retries, escalations, and unpredictable cost.",
        }

    def _premium_ratio_check(
        self,
        models: dict[str, Any],
        totals: dict[str, Any],
        thresholds: CostGuardrailThresholds,
    ) -> dict[str, Any]:
        ratio = self._premium_request_ratio(models, totals)
        status = "pass"
        if ratio >= thresholds.fail_premium_request_ratio:
            status = "fail"
        elif ratio >= thresholds.warn_premium_request_ratio:
            status = "warn"
        return {
            "id": "premium-request-ratio",
            "status": status,
            "value": round(ratio, 4),
            "warn_threshold": thresholds.warn_premium_request_ratio,
            "fail_threshold": thresholds.fail_premium_request_ratio,
            "reason": "Premium use should remain an exception rather than the default path.",
        }

    def _unpriced_model_check(
        self,
        totals: dict[str, Any],
        thresholds: CostGuardrailThresholds,
    ) -> dict[str, Any]:
        count = _int(totals.get("unpriced_model_count"))
        status = "pass"
        if count >= thresholds.fail_unpriced_model_count:
            status = "fail"
        elif count >= thresholds.warn_unpriced_model_count:
            status = "warn"
        return {
            "id": "unpriced-models",
            "status": status,
            "value": count,
            "warn_threshold": thresholds.warn_unpriced_model_count,
            "fail_threshold": thresholds.fail_unpriced_model_count,
            "reason": "Unknown-price gateway models should be added to the catalog before budget decisions rely on them.",
        }

    def _forecast_savings_check(self, forecast_summary: dict[str, Any]) -> dict[str, Any]:
        savings_ratio = forecast_summary.get("estimated_savings_ratio")
        value = float(savings_ratio) if isinstance(savings_ratio, (int, float)) else 0.0
        status = "pass" if value >= 0.5 else "warn"
        return {
            "id": "cheap-first-savings",
            "status": status,
            "value": round(value, 4),
            "warn_threshold": 0.5,
            "reason": "Cheap-first defaults should preserve material savings versus premium-only baseline.",
        }

    def _status(self, checks: list[dict[str, Any]]) -> str:
        if any(check["status"] == "fail" for check in checks):
            return "fail"
        if any(check["status"] == "warn" for check in checks):
            return "warn"
        return "pass"

    def _recommended_actions(self, checks: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        for check in checks:
            if check["status"] == "pass":
                continue
            if check["id"] == "actual-cost-budget":
                actions.append("Review monthly budget, forecast assumptions, and recent high-cost stages.")
            elif check["id"] == "model-failure-rate":
                actions.append("Inspect recent model errors before increasing retry or escalation limits.")
            elif check["id"] == "premium-request-ratio":
                actions.append("Audit premium model callers and restore cheap-first defaults where possible.")
            elif check["id"] == "unpriced-models":
                actions.append("Add unpriced gateway models to model_catalog.py or avoid them in default routes.")
            elif check["id"] == "cheap-first-savings":
                actions.append("Re-evaluate forecast profiles because cheap-first savings are below target.")
        if not actions:
            actions.append("Cost guardrails are passing; continue monitoring usage and forecast drift.")
        return actions

    def _failure_rate(self, totals: dict[str, Any]) -> float:
        requests = _int(totals.get("requests"))
        if not requests:
            return 0.0
        return _int(totals.get("failures")) / requests

    def _premium_request_ratio(self, models: dict[str, Any], totals: dict[str, Any]) -> float:
        requests = _int(totals.get("requests"))
        if not requests:
            return 0.0
        premium_requests = 0
        for model_id, data in models.items():
            profile = model_profile(str(model_id))
            if profile and profile.cost_tier == "premium":
                premium_requests += _int(_dict(data).get("requests"))
        return premium_requests / requests


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
