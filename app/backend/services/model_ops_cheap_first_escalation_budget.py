from __future__ import annotations

import re
from typing import Any


FORBIDDEN_KEY_PATTERN = re.compile(
    r"(api[_-]?key|authorization|password|secret|prompt|headers?|raw[_-]?(model[_-]?)?output|raw[_-]?response|legal[_-]?text|document[_-]?text|client[_-]?email|email|request[_-]?body|response[_-]?body)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b)"
)


DEFAULT_OBSERVATIONS: tuple[dict[str, Any], ...] = (
    {
        "task": "fast",
        "phase": "steady_state",
        "request_count": 500,
        "primary_failure_count": 8,
        "verification_count": 12,
        "escalation_count": 4,
        "successful_after_escalation_count": 3,
        "premium_escalation_count": 0,
        "operator_review_count": 0,
        "primary_cost_usd": 0.045,
        "verification_cost_usd": 0.012,
        "escalation_cost_usd": 0.018,
        "premium_cost_usd": 0.0,
    },
    {
        "task": "ocr",
        "phase": "steady_state",
        "request_count": 180,
        "primary_failure_count": 6,
        "verification_count": 7,
        "escalation_count": 3,
        "successful_after_escalation_count": 2,
        "premium_escalation_count": 0,
        "operator_review_count": 0,
        "primary_cost_usd": 0.035,
        "verification_cost_usd": 0.011,
        "escalation_cost_usd": 0.016,
        "premium_cost_usd": 0.0,
    },
    {
        "task": "classification",
        "phase": "steady_state",
        "request_count": 260,
        "primary_failure_count": 3,
        "verification_count": 5,
        "escalation_count": 2,
        "successful_after_escalation_count": 2,
        "premium_escalation_count": 0,
        "operator_review_count": 0,
        "primary_cost_usd": 0.026,
        "verification_cost_usd": 0.007,
        "escalation_cost_usd": 0.008,
        "premium_cost_usd": 0.0,
    },
    {
        "task": "review",
        "phase": "steady_state",
        "request_count": 120,
        "primary_failure_count": 5,
        "verification_count": 8,
        "escalation_count": 3,
        "successful_after_escalation_count": 2,
        "premium_escalation_count": 1,
        "operator_review_count": 1,
        "primary_cost_usd": 0.09,
        "verification_cost_usd": 0.05,
        "escalation_cost_usd": 0.08,
        "premium_cost_usd": 0.015,
    },
)


THRESHOLDS = {
    "minimum_request_count": 20,
    "primary_failure_rate_warn": 0.05,
    "primary_failure_rate_fail": 0.12,
    "escalation_rate_warn": 0.08,
    "escalation_rate_fail": 0.18,
    "premium_escalation_rate_warn": 0.02,
    "premium_escalation_rate_fail": 0.05,
    "wasted_escalation_cost_ratio_warn": 0.25,
    "wasted_escalation_cost_ratio_fail": 0.45,
    "escalation_success_rate_warn_min": 0.40,
    "escalation_success_rate_fail_min": 0.20,
}


class ModelOpsCheapFirstEscalationBudgetService:
    """Evaluate cheap-first cascade escalation cost from aggregate metrics only."""

    def build_budget(self, payload: Any = None) -> dict[str, Any]:
        uses_default_observations = payload is None
        data = {"observations": list(DEFAULT_OBSERVATIONS)} if uses_default_observations else _dict(payload)
        forbidden_field_count = _count_forbidden_keys(data)
        secret_like_value_count = _count_secret_like_values(data)
        observations = [
            item
            for item in _list(data.get("observations"))[:100]
            if isinstance(item, dict)
        ]
        rows = [self._row(item) for item in observations]
        row_failures = [row for row in rows if row["status"] == "fail"]
        row_warnings = [row for row in rows if row["status"] == "warn"]
        checks = self._checks(
            rows,
            forbidden_field_count=forbidden_field_count,
            secret_like_value_count=secret_like_value_count,
        )
        blocking_ids = [check["id"] for check in checks if check["status"] == "fail"]
        warning_ids = [check["id"] for check in checks if check["status"] == "warn"]
        if forbidden_field_count or secret_like_value_count or row_failures or blocking_ids:
            status = "fail"
        elif not rows:
            status = "not_supplied"
        elif row_warnings or warning_ids:
            status = "review_required"
        else:
            status = "pass"

        total_cascade_cost = round(sum(row["cascade_cost_usd"] for row in rows), 6)
        total_wasted_cost = round(sum(row["wasted_escalation_cost_usd"] for row in rows), 6)
        total_escalations = sum(row["escalation_count"] for row in rows)
        total_successful_escalations = sum(row["successful_after_escalation_count"] for row in rows)

        return {
            "id": "model-ops-cheap-first-escalation-budget",
            "title": "Cheap-first escalation budget",
            "status": status,
            "method": {
                "type": "model-ops-cheap-first-escalation-budget",
                "notes": [
                    "Evaluates aggregate cheap-first cascade counts before default promotion.",
                    "Flags runaway retries, low-value escalations, premium exceptions without review, and wasted escalation spend.",
                    "Uses built-in synthetic aggregate observations for the default GET route; POST evaluates maintainer-supplied aggregate counts only.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, or any gateway.",
                ],
                "research_basis": [
                    {
                        "id": "frugalgpt",
                        "url": "https://arxiv.org/abs/2305.05176",
                        "signal": "Cost-aware LLM cascades should escalate only when a lower-cost model cannot satisfy the task.",
                    },
                    {
                        "id": "llm-routing-cascade-review",
                        "url": "https://huggingface.co/papers/2410.10347",
                        "signal": "Routing and cascading need quality estimators and explicit cost-performance tradeoff evidence.",
                    },
                ],
            },
            "thresholds": THRESHOLDS,
            "summary": {
                "observation_count": len(rows),
                "default_observation_used": uses_default_observations,
                "passing_observation_count": sum(1 for row in rows if row["status"] == "pass"),
                "warning_observation_count": len(row_warnings),
                "failing_observation_count": len(row_failures),
                "total_request_count": sum(row["request_count"] for row in rows),
                "primary_failure_count": sum(row["primary_failure_count"] for row in rows),
                "verification_count": sum(row["verification_count"] for row in rows),
                "escalation_count": total_escalations,
                "successful_after_escalation_count": total_successful_escalations,
                "premium_escalation_count": sum(row["premium_escalation_count"] for row in rows),
                "operator_review_count": sum(row["operator_review_count"] for row in rows),
                "cascade_cost_usd": total_cascade_cost,
                "primary_cost_usd": round(sum(row["primary_cost_usd"] for row in rows), 6),
                "verification_cost_usd": round(sum(row["verification_cost_usd"] for row in rows), 6),
                "escalation_cost_usd": round(sum(row["escalation_cost_usd"] for row in rows), 6),
                "premium_cost_usd": round(sum(row["premium_cost_usd"] for row in rows), 6),
                "wasted_escalation_cost_usd": total_wasted_cost,
                "wasted_escalation_cost_ratio": _ratio_float(total_wasted_cost, total_cascade_cost),
                "escalation_success_rate": _ratio_float(total_successful_escalations, total_escalations),
                "blocking_check_count": len(blocking_ids),
                "warning_check_count": len(warning_ids),
                "forbidden_payload_field_count": forbidden_field_count,
                "secret_like_value_count": secret_like_value_count,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "raw_payload_echoed": False,
            },
            "budget_rows": rows,
            "checks": checks,
            "blocking_check_ids": blocking_ids,
            "warning_check_ids": warning_ids,
            "blocking_observation_ids": [row["id"] for row in row_failures],
            "warning_observation_ids": [row["id"] for row in row_warnings],
            "recommended_actions": self._recommended_actions(
                status,
                forbidden_field_count=forbidden_field_count,
                secret_like_value_count=secret_like_value_count,
                row_failures=row_failures,
                row_warnings=row_warnings,
            ),
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "phone_numbers_included": False,
                "identity_numbers_included": False,
                "configuration_written": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "output_scope": "aggregate task ids, counts, ratios, cost totals, check ids, and recommended actions only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "production_traffic_claimed": False,
                "automatic_default_change_claimed": False,
                "production_accuracy_claimed": False,
                "public_benchmark_scores_included": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_release_decision.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _row(self, observation: dict[str, Any]) -> dict[str, Any]:
        task = _safe_token(observation.get("task"), "unknown")
        phase = _safe_token(observation.get("phase"), "aggregate")
        request_count = _safe_int(observation.get("request_count"))
        primary_failure_count = _safe_int(observation.get("primary_failure_count") or observation.get("failure_count"))
        verification_count = _safe_int(observation.get("verification_count"))
        escalation_count = _safe_int(observation.get("escalation_count"))
        successful_after_escalation_count = min(
            escalation_count,
            _safe_int(observation.get("successful_after_escalation_count")),
        )
        premium_escalation_count = _safe_int(observation.get("premium_escalation_count") or observation.get("premium_request_count"))
        operator_review_count = _safe_int(observation.get("operator_review_count"))
        primary_cost_usd = _safe_float(observation.get("primary_cost_usd"))
        verification_cost_usd = _safe_float(observation.get("verification_cost_usd"))
        escalation_cost_usd = _safe_float(observation.get("escalation_cost_usd"))
        premium_cost_usd = _safe_float(observation.get("premium_cost_usd"))
        cascade_cost_usd = round(primary_cost_usd + verification_cost_usd + escalation_cost_usd + premium_cost_usd, 6)
        unsuccessful_escalation_count = max(0, escalation_count - successful_after_escalation_count)
        wasted_escalation_cost_usd = round(
            escalation_cost_usd * _ratio_float(unsuccessful_escalation_count, escalation_count),
            6,
        )

        primary_failure_rate = _ratio_float(primary_failure_count, request_count)
        escalation_rate = _ratio_float(escalation_count, request_count)
        premium_escalation_rate = _ratio_float(premium_escalation_count, request_count)
        escalation_success_rate = _ratio_float(successful_after_escalation_count, escalation_count)
        wasted_escalation_cost_ratio = _ratio_float(wasted_escalation_cost_usd, cascade_cost_usd)
        checks = [
            _bounded_check(
                "minimum-request-count",
                float(request_count),
                float(THRESHOLDS["minimum_request_count"]),
                lower_bound=True,
                warn_only=True,
            ),
            _two_level_upper_check(
                "primary-failure-rate",
                primary_failure_rate,
                THRESHOLDS["primary_failure_rate_warn"],
                THRESHOLDS["primary_failure_rate_fail"],
            ),
            _two_level_upper_check(
                "escalation-rate",
                escalation_rate,
                THRESHOLDS["escalation_rate_warn"],
                THRESHOLDS["escalation_rate_fail"],
            ),
            _two_level_upper_check(
                "premium-escalation-rate",
                premium_escalation_rate,
                THRESHOLDS["premium_escalation_rate_warn"],
                THRESHOLDS["premium_escalation_rate_fail"],
            ),
            _two_level_upper_check(
                "wasted-escalation-cost-ratio",
                wasted_escalation_cost_ratio,
                THRESHOLDS["wasted_escalation_cost_ratio_warn"],
                THRESHOLDS["wasted_escalation_cost_ratio_fail"],
            ),
            _two_level_lower_check(
                "escalation-success-rate",
                escalation_success_rate,
                THRESHOLDS["escalation_success_rate_warn_min"],
                THRESHOLDS["escalation_success_rate_fail_min"],
                skip_when=escalation_count == 0,
            ),
            self._premium_review_check(premium_escalation_count, operator_review_count),
        ]
        if any(check["status"] == "fail" for check in checks):
            status = "fail"
        elif any(check["status"] == "warn" for check in checks):
            status = "warn"
        else:
            status = "pass"

        return {
            "id": f"escalation-budget-{task}-{phase}",
            "task": task,
            "phase": phase,
            "status": status,
            "request_count": request_count,
            "primary_failure_count": primary_failure_count,
            "verification_count": verification_count,
            "escalation_count": escalation_count,
            "successful_after_escalation_count": successful_after_escalation_count,
            "premium_escalation_count": premium_escalation_count,
            "operator_review_count": operator_review_count,
            "primary_failure_rate": primary_failure_rate,
            "escalation_rate": escalation_rate,
            "premium_escalation_rate": premium_escalation_rate,
            "escalation_success_rate": escalation_success_rate,
            "primary_cost_usd": primary_cost_usd,
            "verification_cost_usd": verification_cost_usd,
            "escalation_cost_usd": escalation_cost_usd,
            "premium_cost_usd": premium_cost_usd,
            "cascade_cost_usd": cascade_cost_usd,
            "wasted_escalation_cost_usd": wasted_escalation_cost_usd,
            "wasted_escalation_cost_ratio": wasted_escalation_cost_ratio,
            "premium_review_coverage": operator_review_count >= premium_escalation_count,
            "checks": checks,
            "reason_codes": [check["id"] for check in checks if check["status"] != "pass"],
            "recommended_action": self._row_action(status, premium_escalation_count, operator_review_count),
        }

    def _premium_review_check(self, premium_escalation_count: int, operator_review_count: int) -> dict[str, Any]:
        missing_review = premium_escalation_count > operator_review_count
        return {
            "id": "premium-operator-review-coverage",
            "status": "fail" if missing_review else "pass",
            "value": operator_review_count,
            "threshold": premium_escalation_count,
            "reason": (
                "Every premium escalation must have aggregate operator-review coverage."
                if not missing_review
                else "Premium escalations exceed aggregate operator-review coverage."
            ),
        }

    def _checks(
        self,
        rows: list[dict[str, Any]],
        *,
        forbidden_field_count: int,
        secret_like_value_count: int,
    ) -> list[dict[str, Any]]:
        row_checks = [check for row in rows for check in row["checks"]]
        failing_row_checks = [check for check in row_checks if check["status"] == "fail"]
        warning_row_checks = [check for check in row_checks if check["status"] == "warn"]
        return [
            {
                "id": "sanitized-payload-fields",
                "status": "fail" if forbidden_field_count or secret_like_value_count else "pass",
                "reason": (
                    "Payload contains forbidden field names or secret-like values."
                    if forbidden_field_count or secret_like_value_count
                    else "Payload contains only aggregate escalation metrics."
                ),
            },
            {
                "id": "observation-present",
                "status": "warn" if not rows else "pass",
                "reason": "At least one aggregate observation row is present." if rows else "No aggregate escalation observations were supplied.",
            },
            {
                "id": "row-thresholds",
                "status": "fail" if failing_row_checks else ("warn" if warning_row_checks else "pass"),
                "reason": (
                    "One or more aggregate rows breach escalation budget thresholds."
                    if failing_row_checks
                    else (
                        "One or more aggregate rows require escalation budget review."
                        if warning_row_checks
                        else "Aggregate rows satisfy escalation budget thresholds."
                    )
                ),
            },
            {
                "id": "premium-review-coverage",
                "status": "fail"
                if any("premium-operator-review-coverage" in row["reason_codes"] for row in rows)
                else "pass",
                "reason": "Premium escalations have aggregate operator-review coverage."
                if not any("premium-operator-review-coverage" in row["reason_codes"] for row in rows)
                else "At least one row has premium escalations without matching operator review.",
            },
            {
                "id": "no-model-or-gateway-call",
                "status": "pass",
                "reason": "Budget evaluation is offline and metadata-only.",
            },
        ]

    def _row_action(self, status: str, premium_escalation_count: int, operator_review_count: int) -> str:
        if premium_escalation_count > operator_review_count:
            return "Hold premium escalation until aggregate operator-review evidence covers every premium exception."
        if status == "fail":
            return "Reduce retry/escalation pressure or keep the current cheap-first default until budget blockers are reviewed."
        if status == "warn":
            return "Review escalation rates and wasted cost before increasing cheap-first traffic."
        return "Escalation budget is compatible with cheap-first routing for this aggregate row."

    def _recommended_actions(
        self,
        status: str,
        *,
        forbidden_field_count: int,
        secret_like_value_count: int,
        row_failures: list[dict[str, Any]],
        row_warnings: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if forbidden_field_count or secret_like_value_count:
            actions.append("Remove forbidden fields, prompts, raw outputs, credentials, or identifiers before resubmitting aggregate metrics.")
        if row_failures:
            actions.append("Block cheap-first default promotion until failing escalation budget rows are reviewed.")
            actions.extend(f"Fix escalation budget row: {row['task']} / {row['phase']}." for row in row_failures[:5])
        if row_warnings:
            actions.append("Attach maintainer review notes for warning escalation budget rows before canary expansion.")
        if status == "not_supplied":
            actions.append("Submit aggregate cheap-first cascade metrics from local fixtures or staging before treating escalation cost as proven.")
        if not actions:
            actions.append("Keep cheap-first routing active and rerun escalation budget review before any default model change.")
        return _dedupe(actions)


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


def _safe_float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return round(max(0.0, float(value)), 6)
    return 0.0


def _ratio_float(numerator: float | int, denominator: float | int) -> float:
    denominator_float = float(denominator)
    if denominator_float <= 0:
        return 0.0
    return round(float(numerator) / denominator_float, 6)


def _safe_token(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower().replace(" ", "-")[:100]
    if not text or SECRET_VALUE_PATTERN.search(text):
        return fallback
    cleaned = re.sub(r"[^a-z0-9_.:-]+", "-", text).strip("-")
    return cleaned or fallback


def _bounded_check(
    check_id: str,
    value: float,
    threshold: float,
    *,
    lower_bound: bool = False,
    warn_only: bool = False,
) -> dict[str, Any]:
    breached = value < threshold if lower_bound else value > threshold
    status = "warn" if breached and warn_only else ("fail" if breached else "pass")
    comparator = "at least" if lower_bound else "at most"
    return {
        "id": check_id,
        "status": status,
        "value": value,
        "threshold": threshold,
        "reason": f"Observed value must be {comparator} {threshold}.",
    }


def _two_level_upper_check(check_id: str, value: float, warn_threshold: float, fail_threshold: float) -> dict[str, Any]:
    status = "fail" if value > fail_threshold else ("warn" if value > warn_threshold else "pass")
    return {
        "id": check_id,
        "status": status,
        "value": value,
        "warn_threshold": warn_threshold,
        "fail_threshold": fail_threshold,
        "reason": f"Observed value must stay at or below {warn_threshold} for pass and {fail_threshold} for fail.",
    }


def _two_level_lower_check(
    check_id: str,
    value: float,
    warn_threshold: float,
    fail_threshold: float,
    *,
    skip_when: bool = False,
) -> dict[str, Any]:
    if skip_when:
        return {
            "id": check_id,
            "status": "pass",
            "value": value,
            "warn_threshold": warn_threshold,
            "fail_threshold": fail_threshold,
            "reason": "No escalations observed; success-rate check is not applicable.",
        }
    status = "fail" if value < fail_threshold else ("warn" if value < warn_threshold else "pass")
    return {
        "id": check_id,
        "status": status,
        "value": value,
        "warn_threshold": warn_threshold,
        "fail_threshold": fail_threshold,
        "reason": f"Observed value must stay at or above {warn_threshold} for pass and {fail_threshold} for fail.",
    }


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


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
