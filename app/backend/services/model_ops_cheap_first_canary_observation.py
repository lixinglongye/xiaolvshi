from __future__ import annotations

import re
from typing import Any


FORBIDDEN_KEY_PATTERN = re.compile(
    r"(api[_-]?key|authorization|password|secret|prompt|headers?|raw[_-]?(model[_-]?)?output|raw[_-]?response|legal[_-]?text|client[_-]?email|email)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")


class ModelOpsCheapFirstCanaryObservationService:
    """Evaluate sanitized cheap-first canary observations without executing rollout."""

    def build_review(self, payload: Any = None, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        canary_plan = _dict(data.get("cheap_first_canary_plan"))
        observations_payload = _dict(payload)
        forbidden_field_count = _count_forbidden_keys(observations_payload)
        secret_like_value_count = _count_secret_like_values(observations_payload)
        observations = [
            row
            for row in _list(observations_payload.get("observations"))
            if isinstance(row, dict)
        ]
        step_index = {
            str(step.get("id") or ""): step
            for step in _list(canary_plan.get("canary_steps"))
            if isinstance(step, dict) and step.get("id")
        }
        rows = [
            self._row(observation, step_index)
            for observation in observations[:100]
        ]
        blocking = [row for row in rows if row["status"] == "fail"]
        warnings = [row for row in rows if row["status"] == "warn"]
        passing = [row for row in rows if row["status"] == "pass"]
        if forbidden_field_count or secret_like_value_count:
            status = "fail"
        elif not rows:
            status = "not_supplied"
        elif blocking:
            status = "fail"
        elif warnings:
            status = "review_required"
        else:
            status = "pass"

        return {
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-canary-observation-review",
                "notes": [
                    "Evaluates maintainer-supplied aggregate canary metrics only.",
                    "Does not call NewAPI/Gemini/OpenAI/Google, shift traffic, or persist observations.",
                    "Rejects sensitive field names and secret-like values without echoing them back.",
                ],
            },
            "summary": {
                "observation_count": len(rows),
                "matched_step_count": sum(1 for row in rows if row["source_step_found"]),
                "unmatched_step_count": sum(1 for row in rows if not row["source_step_found"]),
                "passing_observation_count": len(passing),
                "warning_observation_count": len(warnings),
                "failing_observation_count": len(blocking),
                "rollback_trigger_breach_count": sum(
                    1
                    for row in rows
                    for check in row["checks"]
                    if check["status"] == "fail" and check["id"] != "traffic-on-held-step"
                ),
                "total_request_count": sum(row["request_count"] for row in rows),
                "forbidden_payload_field_count": forbidden_field_count,
                "secret_like_value_count": secret_like_value_count,
                "source_plan_status": str(canary_plan.get("status") or "missing"),
                "configuration_written": False,
                "gateway_called": False,
                "traffic_shifted": False,
                "raw_payload_echoed": False,
            },
            "thresholds": {
                "failure_rate_max": 0.02,
                "over_budget_route_ratio_max": 0.01,
                "premium_request_ratio_max": 0.05,
                "operator_review_route_ratio_max": 0.10,
                "minimum_request_count": 20,
            },
            "observation_rows": rows,
            "blocking_observation_ids": [row["id"] for row in blocking],
            "warning_observation_ids": [row["id"] for row in warnings],
            "recommended_actions": self._recommended_actions(
                status,
                forbidden_field_count,
                secret_like_value_count,
                blocking,
                warnings,
                passing,
            ),
            "privacy_boundary": {
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "raw_payload_echoed": False,
                "configuration_written": False,
                "network_called": False,
                "traffic_shifted": False,
                "output_scope": "aggregate canary counts, ratios, status codes, and reason codes only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "automatic_canary_rollout_claimed": False,
                "production_traffic_shifted": False,
                "public_benchmark_scores_included": False,
                "production_accuracy_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_canary_observation.py tests/test_model_ops_cheap_first_canary_plan.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _row(self, observation: dict[str, Any], step_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
        step_id = _safe_token(observation.get("step_id"), "unknown-step")
        source_step = step_index.get(step_id)
        request_count = _safe_int(observation.get("request_count"))
        failure_count = _safe_int(observation.get("failure_count"))
        over_budget_count = _safe_int(observation.get("over_budget_count"))
        premium_request_count = _safe_int(observation.get("premium_request_count")) + _safe_int(
            observation.get("unknown_price_model_count")
        )
        operator_review_count = _safe_int(observation.get("operator_review_count"))
        failure_rate = _ratio(failure_count, request_count)
        over_budget_route_ratio = _ratio(over_budget_count, request_count)
        premium_request_ratio = _ratio(premium_request_count, request_count)
        operator_review_route_ratio = _ratio(operator_review_count, request_count)

        checks = [
            self._check("failure-rate", failure_rate, 0.02, "fail"),
            self._check("over-budget-route-ratio", over_budget_route_ratio, 0.01, "fail"),
            self._check("premium-request-ratio", premium_request_ratio, 0.05, "fail"),
            self._check("operator-review-route-ratio", operator_review_route_ratio, 0.10, "fail"),
            self._check("minimum-request-count", float(request_count), 20.0, "warn", lower_bound=True),
            self._traffic_allowed_check(source_step, request_count),
            {
                "id": "source-step-found",
                "status": "pass" if source_step else "warn",
                "value": 1 if source_step else 0,
                "threshold": 1,
                "reason": "Observation is linked to a current canary plan step." if source_step else "Observation step id does not match the current canary plan.",
            },
        ]
        if any(check["status"] == "fail" for check in checks):
            status = "fail"
        elif any(check["status"] == "warn" for check in checks):
            status = "warn"
        else:
            status = "pass"

        return {
            "id": f"canary-observation-{step_id}",
            "step_id": step_id,
            "task": _safe_token(observation.get("task") or (source_step or {}).get("task"), "unknown"),
            "phase": _safe_token(observation.get("phase") or (source_step or {}).get("phase"), "unknown"),
            "status": status,
            "source_step_found": bool(source_step),
            "request_count": request_count,
            "failure_count": failure_count,
            "over_budget_count": over_budget_count,
            "premium_request_count": premium_request_count,
            "operator_review_count": operator_review_count,
            "failure_rate": failure_rate,
            "over_budget_route_ratio": over_budget_route_ratio,
            "premium_request_ratio": premium_request_ratio,
            "operator_review_route_ratio": operator_review_route_ratio,
            "checks": checks,
            "reason_codes": [check["id"] for check in checks if check["status"] != "pass"],
            "action": self._action(status, source_step),
        }

    def _traffic_allowed_check(self, source_step: dict[str, Any] | None, request_count: int) -> dict[str, Any]:
        step_status = str((source_step or {}).get("step_status") or "").strip().lower()
        traffic_on_held_step = step_status in {"blocked", "review_required"} and request_count > 0
        return {
            "id": "traffic-on-held-step",
            "status": "fail" if traffic_on_held_step else "pass",
            "value": request_count,
            "threshold": 0,
            "reason": (
                "Observed traffic is not allowed for blocked or review-required canary steps."
                if traffic_on_held_step
                else "Observed traffic is compatible with the source canary step status."
            ),
        }

    def _check(
        self,
        check_id: str,
        value: float,
        threshold: float,
        fail_status: str,
        *,
        lower_bound: bool = False,
    ) -> dict[str, Any]:
        failed = value < threshold if lower_bound else value > threshold
        status = fail_status if failed else "pass"
        comparator = "at least" if lower_bound else "at most"
        return {
            "id": check_id,
            "status": status,
            "value": value,
            "threshold": threshold,
            "reason": f"Observed value must be {comparator} {threshold}.",
        }

    def _action(self, status: str, source_step: dict[str, Any] | None) -> str:
        if status == "fail":
            return "Do not advance the canary; rollback or keep the previous default until failing metrics are reviewed."
        if status == "warn":
            return "Hold the canary for maintainer review before increasing batch size."
        if source_step:
            return "Canary observation passes thresholds; maintainer may review the next staged step."
        return "Observation passes numeric thresholds but needs source-step mapping review."

    def _recommended_actions(
        self,
        status: str,
        forbidden_field_count: int,
        secret_like_value_count: int,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        passing: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if forbidden_field_count or secret_like_value_count:
            actions.append("Remove forbidden fields or secret-like values and resubmit aggregate canary metrics only.")
        if blocking:
            actions.append("Rollback or hold canary steps with failing threshold checks before any batch increase.")
        if warnings:
            actions.append("Review unmatched or low-volume canary observations before treating them as release evidence.")
        if passing and status == "pass":
            actions.append("Attach these aggregate observations to the maintainer review packet before any explicit default edit.")
        if status == "not_supplied":
            actions.append("Submit aggregate canary observations after a maintainer-approved local or staging canary window.")
        return actions or ["No canary observation actions were generated."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    if isinstance(value, float):
        return max(0, int(value))
    return 0


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _safe_token(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower().replace(" ", "-")[:100]
    if not text or SECRET_VALUE_PATTERN.search(text):
        return fallback
    cleaned = re.sub(r"[^a-z0-9_.:-]+", "-", text).strip("-")
    return cleaned or fallback


def _count_forbidden_keys(value: Any) -> int:
    if isinstance(value, dict):
        count = sum(1 for key in value if FORBIDDEN_KEY_PATTERN.search(str(key)))
        return count + sum(_count_forbidden_keys(item) for item in value.values())
    if isinstance(value, list):
        return sum(_count_forbidden_keys(item) for item in value)
    return 0


def _count_secret_like_values(value: Any) -> int:
    if isinstance(value, dict):
        return sum(_count_secret_like_values(item) for item in value.values())
    if isinstance(value, list):
        return sum(_count_secret_like_values(item) for item in value)
    if isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        return 1
    return 0
