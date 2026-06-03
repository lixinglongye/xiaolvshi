from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RouteGuardrailThresholds:
    warn_over_budget_route_ratio: float = 0.1
    fail_over_budget_route_ratio: float = 0.25
    warn_downgrade_ratio: float = 0.15
    fail_downgrade_ratio: float = 0.35
    warn_operator_review_ratio: float = 0.1
    fail_operator_review_ratio: float = 0.25
    warn_failure_rate: float = 0.08
    fail_failure_rate: float = 0.2
    warn_unknown_price_model_count: int = 1
    fail_unknown_price_model_count: int = 3
    warn_allowed_over_budget_count: int = 1
    fail_allowed_over_budget_count: int = 3

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class ModelRouteGuardrailService:
    """Evaluate aggregate runtime route telemetry against cheap-first guardrails."""

    def evaluate(
        self,
        route_telemetry: dict[str, Any],
        thresholds: RouteGuardrailThresholds | None = None,
    ) -> dict[str, Any]:
        thresholds = thresholds or RouteGuardrailThresholds()
        telemetry = _dict(route_telemetry)
        totals = _dict(telemetry.get("totals"))
        summary = _dict(telemetry.get("summary"))
        request_count = _int(summary.get("request_count") if "request_count" in summary else totals.get("requests"))
        failure_rate = _ratio(_int(totals.get("failures")), request_count)
        over_budget_ratio = _summary_ratio(
            summary,
            "over_budget_request_ratio",
            totals,
            "over_budget_requested",
            request_count,
        )
        downgrade_ratio = _summary_ratio(
            summary,
            "downgrade_ratio",
            totals,
            "downgraded_to_recommended",
            request_count,
        )
        operator_review_ratio = _ratio(_int(totals.get("operator_review_requested")), request_count)
        unknown_price_count = _summary_count(summary, "unknown_price_model_count", totals, "unknown_price_model")
        allowed_over_budget_count = _summary_count(summary, "allowed_over_budget_count", totals, "allowed_over_budget")

        checks = [
            self._telemetry_ready_check(telemetry, request_count),
            self._ratio_check(
                check_id="route-failure-rate",
                value=failure_rate,
                request_count=request_count,
                warn_threshold=thresholds.warn_failure_rate,
                fail_threshold=thresholds.fail_failure_rate,
                reason="High route failure rate can trigger retries, escalations, or manual reruns.",
                no_data_reason="No routed text calls recorded yet; validate failure rate after staging traffic.",
            ),
            self._ratio_check(
                check_id="over-budget-route-ratio",
                value=over_budget_ratio,
                request_count=request_count,
                warn_threshold=thresholds.warn_over_budget_route_ratio,
                fail_threshold=thresholds.fail_over_budget_route_ratio,
                reason="Over-budget requested models should remain rare and reviewable.",
                no_data_reason="No routed text calls recorded yet; validate over-budget routing after staging traffic.",
            ),
            self._ratio_check(
                check_id="downgrade-ratio",
                value=downgrade_ratio,
                request_count=request_count,
                warn_threshold=thresholds.warn_downgrade_ratio,
                fail_threshold=thresholds.fail_downgrade_ratio,
                reason="Frequent downgrades mean callers are requesting models above the task budget.",
                no_data_reason="No routed text calls recorded yet; validate downgrade pressure after staging traffic.",
            ),
            self._ratio_check(
                check_id="operator-review-route-ratio",
                value=operator_review_ratio,
                request_count=request_count,
                warn_threshold=thresholds.warn_operator_review_ratio,
                fail_threshold=thresholds.fail_operator_review_ratio,
                reason="Operator-review-gated requests should stay exceptional.",
                no_data_reason="No routed text calls recorded yet; validate review-gated routing after staging traffic.",
            ),
            self._count_check(
                check_id="unknown-price-route-count",
                value=unknown_price_count,
                warn_threshold=thresholds.warn_unknown_price_model_count,
                fail_threshold=thresholds.fail_unknown_price_model_count,
                reason="Unknown-price gateway models should be added to the catalog before release evidence relies on them.",
            ),
            self._count_check(
                check_id="allowed-over-budget-count",
                value=allowed_over_budget_count,
                warn_threshold=thresholds.warn_allowed_over_budget_count,
                fail_threshold=thresholds.fail_allowed_over_budget_count,
                reason="Allowed over-budget requests require maintainer review before they become defaults.",
            ),
        ]

        status = self._status(checks)
        return {
            "status": status,
            "thresholds": thresholds.to_api(),
            "summary": {
                "request_count": request_count,
                "failure_rate": failure_rate,
                "over_budget_route_ratio": over_budget_ratio,
                "downgrade_ratio": downgrade_ratio,
                "operator_review_route_ratio": operator_review_ratio,
                "unknown_price_model_count": unknown_price_count,
                "allowed_over_budget_count": allowed_over_budget_count,
            },
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in checks if check["status"] == "fail"],
            "warning_check_ids": [check["id"] for check in checks if check["status"] == "warn"],
            "recommended_actions": self._recommended_actions(checks),
        }

    def _telemetry_ready_check(self, telemetry: dict[str, Any], request_count: int) -> dict[str, Any]:
        ready = telemetry.get("status") == "ready"
        return {
            "id": "route-telemetry-ready",
            "status": "pass" if ready else "fail",
            "value": request_count,
            "reason": (
                "Route telemetry is available for aggregate guardrail evaluation."
                if ready
                else "Route telemetry is missing or not ready; guardrail evidence cannot be trusted."
            ),
        }

    def _ratio_check(
        self,
        *,
        check_id: str,
        value: float,
        request_count: int,
        warn_threshold: float,
        fail_threshold: float,
        reason: str,
        no_data_reason: str,
    ) -> dict[str, Any]:
        status = "pass"
        if request_count > 0:
            if value >= fail_threshold:
                status = "fail"
            elif value >= warn_threshold:
                status = "warn"
        return {
            "id": check_id,
            "status": status,
            "value": round(value, 4),
            "ratio": round(value, 4),
            "warn_threshold": warn_threshold,
            "fail_threshold": fail_threshold,
            "reason": reason if request_count > 0 else no_data_reason,
        }

    def _count_check(
        self,
        *,
        check_id: str,
        value: int,
        warn_threshold: int,
        fail_threshold: int,
        reason: str,
    ) -> dict[str, Any]:
        status = "pass"
        if value >= fail_threshold:
            status = "fail"
        elif value >= warn_threshold:
            status = "warn"
        return {
            "id": check_id,
            "status": status,
            "value": value,
            "warn_threshold": warn_threshold,
            "fail_threshold": fail_threshold,
            "reason": reason,
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
            if check["id"] == "route-telemetry-ready":
                actions.append("Ensure route telemetry is returned by /api/v1/aihub/models before collecting release evidence.")
            elif check["id"] == "route-failure-rate":
                actions.append("Inspect gateway errors and retry behavior before increasing model escalation.")
            elif check["id"] == "over-budget-route-ratio":
                actions.append("Audit explicit model overrides and restore task defaults where cheap-first routing is sufficient.")
            elif check["id"] == "downgrade-ratio":
                actions.append("Update callers that request premium models when the task budget recommends a cheaper default.")
            elif check["id"] == "operator-review-route-ratio":
                actions.append("Review premium exceptions and document why operator approval is needed.")
            elif check["id"] == "unknown-price-route-count":
                actions.append("Add unknown gateway models to model_catalog.py before relying on them for release routing.")
            elif check["id"] == "allowed-over-budget-count":
                actions.append("Review allowed over-budget requests and avoid making them default routes without approval.")
        if not actions:
            actions.append("Route guardrails are passing; continue monitoring runtime routing drift.")
        return actions


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


def _summary_ratio(
    summary: dict[str, Any],
    summary_key: str,
    totals: dict[str, Any],
    total_key: str,
    request_count: int,
) -> float:
    if summary_key in summary:
        return _float(summary.get(summary_key))
    return _ratio(_int(totals.get(total_key)), request_count)


def _summary_count(
    summary: dict[str, Any],
    summary_key: str,
    totals: dict[str, Any],
    total_key: str,
) -> int:
    if summary_key in summary:
        return _int(summary.get(summary_key))
    return _int(totals.get(total_key))


def _ratio(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(value / total, 4)
