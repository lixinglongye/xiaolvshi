from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_catalog import model_profile
from services.route_telemetry_repository import RouteTelemetryRepositoryService


@dataclass(frozen=True)
class RouteTelemetryOpsThresholds:
    warn_failure_rate: float = 0.08
    fail_failure_rate: float = 0.20
    warn_over_budget_ratio: float = 0.10
    fail_over_budget_ratio: float = 0.25
    warn_operator_review_ratio: float = 0.10
    fail_operator_review_ratio: float = 0.25
    warn_premium_ratio: float = 0.10
    fail_premium_ratio: float = 0.25
    warn_unknown_model_count: int = 1
    fail_unknown_model_count: int = 3

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class RouteTelemetryOpsSummaryService:
    """Summarize persisted route telemetry into cheap-first operations evidence."""

    def __init__(
        self,
        repository_service: RouteTelemetryRepositoryService | None = None,
        thresholds: RouteTelemetryOpsThresholds | None = None,
    ) -> None:
        self.repository_service = repository_service or RouteTelemetryRepositoryService()
        self.thresholds = thresholds or RouteTelemetryOpsThresholds()

    def build_summary(self, repository_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        repository = repository_payload if isinstance(repository_payload, dict) else self.repository_service.build_repository()
        daily_rows = self._daily_rows(repository)
        totals = self._totals(repository, daily_rows)
        checks = self._checks(repository, totals)
        status = self._status(checks, totals)
        return {
            "status": status,
            "method": {
                "type": "persisted-route-telemetry-ops-summary",
                "notes": [
                    "Consumes sanitized route telemetry repository aggregates only.",
                    "Highlights cheap-first downgrades, premium drift, over-budget pressure, failures, and unknown models.",
                    "Does not read prompts, legal text, request bodies, response bodies, credentials, emails, or raw model outputs.",
                ],
            },
            "thresholds": self.thresholds.to_api(),
            "summary": {
                **totals,
                "repository_status": str(repository.get("status") or "missing"),
                "raw_payload_storage_allowed": bool((_dict(repository.get("summary"))).get("raw_payload_storage_allowed")),
                "storage_mode": str((_dict(repository.get("summary"))).get("storage_mode") or "unknown"),
            },
            "daily_rows": daily_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in checks if check["status"] == "fail"],
            "warning_check_ids": [check["id"] for check in checks if check["status"] == "warn"],
            "recommended_actions": self._recommended_actions(status, checks, totals),
            "release_guardrails": [
                "Do not treat empty telemetry as proof that production routing is healthy.",
                "Use this summary with fixture, cost, selector, and repository validation gates before changing defaults.",
                "Keep legal text, prompts, raw model output, gateway payloads, credentials, and emails out of telemetry storage.",
            ],
            "privacy_boundary": {
                "source": "route_telemetry_repository daily buckets and totals",
                "raw_payload_storage_allowed": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "credentials_included": False,
                "raw_model_output_included": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_ops_summary.py -q",
                "python -m pytest tests/test_route_telemetry_repository.py tests/test_model_route_telemetry.py -q",
            ],
        }

    def _daily_rows(self, repository: dict[str, Any]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for bucket in _list(repository.get("daily_buckets")):
            if not isinstance(bucket, dict):
                continue
            day = str(bucket.get("day") or "unknown")
            row = grouped.setdefault(
                day,
                {
                    "day": day,
                    "request_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "downgrade_count": 0,
                    "over_budget_count": 0,
                    "operator_review_count": 0,
                    "premium_request_count": 0,
                    "estimated_cost_usd_sum": 0.0,
                    "models": {},
                },
            )
            requests = _int(bucket.get("request_count"))
            model = str(bucket.get("resolved_model") or "unknown")
            row["request_count"] += requests
            row["success_count"] += _int(bucket.get("success_count"))
            row["failure_count"] += _int(bucket.get("failure_count"))
            row["downgrade_count"] += requests if bool(bucket.get("routed_to_recommended_model")) else 0
            row["over_budget_count"] += requests if bool(bucket.get("is_over_budget")) else 0
            row["operator_review_count"] += requests if bool(bucket.get("requires_operator_review")) else 0
            row["premium_request_count"] += requests if _cost_tier(model) == "premium" else 0
            row["estimated_cost_usd_sum"] = round(row["estimated_cost_usd_sum"] + _float(bucket.get("estimated_cost_usd_sum")), 8)
            row["models"][model] = row["models"].get(model, 0) + requests

        rows = []
        for row in grouped.values():
            requests = max(0, row["request_count"])
            rows.append(
                {
                    **row,
                    "failure_rate": _ratio(row["failure_count"], requests),
                    "downgrade_ratio": _ratio(row["downgrade_count"], requests),
                    "over_budget_ratio": _ratio(row["over_budget_count"], requests),
                    "operator_review_ratio": _ratio(row["operator_review_count"], requests),
                    "premium_request_ratio": _ratio(row["premium_request_count"], requests),
                    "models": dict(sorted(row["models"].items())),
                }
            )
        return sorted(rows, key=lambda item: item["day"])

    def _totals(self, repository: dict[str, Any], daily_rows: list[dict[str, Any]]) -> dict[str, Any]:
        repo_summary = _dict(repository.get("summary"))
        repo_totals = _dict(repository.get("totals"))
        request_count = sum(_int(row.get("request_count")) for row in daily_rows)
        failure_count = sum(_int(row.get("failure_count")) for row in daily_rows)
        downgrade_count = sum(_int(row.get("downgrade_count")) for row in daily_rows)
        over_budget_count = sum(_int(row.get("over_budget_count")) for row in daily_rows)
        operator_review_count = sum(_int(row.get("operator_review_count")) for row in daily_rows)
        premium_count = sum(_int(row.get("premium_request_count")) for row in daily_rows)
        estimated_cost = round(sum(_float(row.get("estimated_cost_usd_sum")) for row in daily_rows), 8)
        unknown_model_count = _int(repo_totals.get("unknown_model_count"))
        return {
            "stored_event_count": _int(repo_summary.get("stored_event_count")),
            "daily_bucket_count": _int(repo_summary.get("daily_bucket_count")),
            "request_count": request_count,
            "success_count": sum(_int(row.get("success_count")) for row in daily_rows),
            "failure_count": failure_count,
            "downgrade_count": downgrade_count,
            "over_budget_count": over_budget_count,
            "operator_review_count": operator_review_count,
            "premium_request_count": premium_count,
            "unknown_model_count": unknown_model_count,
            "estimated_cost_usd_sum": estimated_cost,
            "failure_rate": _ratio(failure_count, request_count),
            "downgrade_ratio": _ratio(downgrade_count, request_count),
            "over_budget_ratio": _ratio(over_budget_count, request_count),
            "operator_review_ratio": _ratio(operator_review_count, request_count),
            "premium_request_ratio": _ratio(premium_count, request_count),
            "empty_repository": request_count == 0,
        }

    def _checks(self, repository: dict[str, Any], totals: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            self._status_check(
                "repository-ready",
                "pass" if str(repository.get("status") or "") in {"ready", "pass", "warn"} else "fail",
                "Route telemetry repository is available for operations summary.",
            ),
            self._ratio_check("failure-rate", totals["failure_rate"], totals["request_count"], self.thresholds.warn_failure_rate, self.thresholds.fail_failure_rate),
            self._ratio_check("over-budget-ratio", totals["over_budget_ratio"], totals["request_count"], self.thresholds.warn_over_budget_ratio, self.thresholds.fail_over_budget_ratio),
            self._ratio_check("operator-review-ratio", totals["operator_review_ratio"], totals["request_count"], self.thresholds.warn_operator_review_ratio, self.thresholds.fail_operator_review_ratio),
            self._ratio_check("premium-request-ratio", totals["premium_request_ratio"], totals["request_count"], self.thresholds.warn_premium_ratio, self.thresholds.fail_premium_ratio),
            self._count_check("unknown-model-count", totals["unknown_model_count"], self.thresholds.warn_unknown_model_count, self.thresholds.fail_unknown_model_count),
        ]

    def _status_check(self, check_id: str, status: str, reason: str) -> dict[str, Any]:
        return {"id": check_id, "status": status, "value": 0, "reason": reason}

    def _ratio_check(self, check_id: str, value: float, requests: int, warn: float, fail: float) -> dict[str, Any]:
        status = "pass"
        if requests > 0:
            if value >= fail:
                status = "fail"
            elif value >= warn:
                status = "warn"
        return {
            "id": check_id,
            "status": status,
            "value": round(value, 4),
            "ratio": round(value, 4),
            "warn_threshold": warn,
            "fail_threshold": fail,
            "reason": self._ratio_reason(check_id, requests),
        }

    def _count_check(self, check_id: str, value: int, warn: int, fail: int) -> dict[str, Any]:
        status = "fail" if value >= fail else ("warn" if value >= warn else "pass")
        return {
            "id": check_id,
            "status": status,
            "value": value,
            "warn_threshold": warn,
            "fail_threshold": fail,
            "reason": "Unknown-price models should be cataloged before release evidence relies on them.",
        }

    def _ratio_reason(self, check_id: str, requests: int) -> str:
        if requests <= 0:
            return "No persisted route events yet; collect staging traffic before treating telemetry as production evidence."
        return {
            "failure-rate": "Persistent route failures can hide retries, manual reruns, or gateway instability.",
            "over-budget-ratio": "Over-budget route pressure should stay exceptional under cheap-first routing.",
            "operator-review-ratio": "Operator review routes should remain explicit exceptions.",
            "premium-request-ratio": "Premium requests should not become a silent default for routine work.",
        }.get(check_id, "Route telemetry operations check.")

    def _status(self, checks: list[dict[str, Any]], totals: dict[str, Any]) -> str:
        if any(check["status"] == "fail" for check in checks):
            return "fail"
        if any(check["status"] == "warn" for check in checks):
            return "warn"
        return "ready" if totals["empty_repository"] else "pass"

    def _recommended_actions(self, status: str, checks: list[dict[str, Any]], totals: dict[str, Any]) -> list[str]:
        if totals["empty_repository"]:
            return ["Collect sanitized staging route events before using telemetry as production operations evidence."]
        actions = [f"Review {check['id']} before changing model defaults." for check in checks if check["status"] != "pass"]
        return actions or ["Route telemetry operations are within cheap-first guardrails."]


def _cost_tier(model: str) -> str:
    profile = model_profile(model)
    return profile.cost_tier if profile else "unknown"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _ratio(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(max(0, value) / total, 4)
