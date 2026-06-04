from __future__ import annotations

from typing import Any

from services.legal_fixture_run_report import LegalFixtureRunReportService


RAW_FIELD_NAMES = {
    "api_key",
    "authorization",
    "content",
    "gateway_response",
    "output_text",
    "raw_output",
    "raw_response",
    "secret",
}
STATUS_RANK = {
    "not_run": 0,
    "pass": 1,
    "warn": 2,
    "fail": 3,
}
ESCALATING_STEPS = {"apply_high_priority_improvements", "escalate_selected_fixture"}


class LegalFixtureRegressionService:
    """Compare two cheap-first fixture runs without storing raw model outputs."""

    def __init__(self, run_report_service: LegalFixtureRunReportService | None = None) -> None:
        self.run_report_service = run_report_service or LegalFixtureRunReportService()

    def build_comparison(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        baseline_payload, current_payload, policy = self._split_payload(payload)
        baseline = self.run_report_service.build_report(baseline_payload)
        current = self.run_report_service.build_report(current_payload)
        fixture_deltas = self._fixture_deltas(baseline, current, policy)
        regressed = [row for row in fixture_deltas if row["regression_reason_codes"]]
        newly_blocking = [row for row in fixture_deltas if row["newly_blocking"]]
        resolved_blocking = [row for row in fixture_deltas if row["resolved_blocking"]]
        current_observed = current["summary"]["observed_fixture_count"]
        baseline_observed = baseline["summary"]["observed_fixture_count"]
        cost_delta = self._cost_delta(baseline, current)
        status = self._status(current_observed, baseline_observed, regressed, newly_blocking, cost_delta, policy)

        return {
            "status": status,
            "release_decision": self._release_decision(status),
            "method": {
                "type": "cheap-first-legal-fixture-regression-comparison",
                "notes": [
                    "Compares two fixture-run-report payloads using deterministic local scoring only.",
                    "Flags fixture-scoped regressions before cheap-first default changes are promoted.",
                    "Does not call a model, gateway, or public benchmark source.",
                ],
            },
            "summary": {
                "fixture_count": current["summary"]["fixture_count"],
                "baseline_observed_fixture_count": baseline_observed,
                "current_observed_fixture_count": current_observed,
                "compared_fixture_count": len(fixture_deltas),
                "improved_fixture_count": sum(1 for row in fixture_deltas if row["score_delta"] > 0),
                "regressed_fixture_count": len(regressed),
                "newly_blocking_fixture_count": len(newly_blocking),
                "resolved_blocking_fixture_count": len(resolved_blocking),
                "baseline_release_decision": baseline["release_decision"],
                "current_release_decision": current["release_decision"],
                "score_delta_avg": self._average_delta(fixture_deltas),
                "cost_delta_usd": cost_delta["cost_delta_usd"],
                "cost_delta_ratio": cost_delta["cost_delta_ratio"],
                "dropped_raw_field_count": self._raw_field_count(payload),
            },
            "policy": policy,
            "fixture_deltas": fixture_deltas,
            "regressed_fixture_ids": [row["fixture_id"] for row in regressed],
            "newly_blocking_fixture_ids": [row["fixture_id"] for row in newly_blocking],
            "resolved_blocking_fixture_ids": [row["fixture_id"] for row in resolved_blocking],
            "recommended_actions": self._recommended_actions(status, regressed, newly_blocking, resolved_blocking, cost_delta),
            "privacy_note": (
                "The comparison uses supplied fixture observations only for local scoring. It returns metadata deltas, "
                "not raw model outputs, gateway responses, prompts, client documents, emails, credentials, or headers."
            ),
            "validation_commands": [
                "python -m pytest tests/test_legal_fixture_regression.py tests/test_legal_fixture_run_report.py -q",
            ],
        }

    def _split_payload(self, payload: dict[str, Any] | None) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any]]:
        default_policy = {
            "score_regression_threshold": -0.15,
            "cost_increase_warn_ratio": 0.25,
            "missing_current_fixture_is_regression": True,
        }
        if not isinstance(payload, dict):
            return None, None, default_policy
        policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
        merged_policy = {
            **default_policy,
            "score_regression_threshold": self._number_or_default(
                policy.get("score_regression_threshold"),
                default_policy["score_regression_threshold"],
                minimum=-1.0,
                maximum=0.0,
            ),
            "cost_increase_warn_ratio": self._number_or_default(
                policy.get("cost_increase_warn_ratio"),
                default_policy["cost_increase_warn_ratio"],
                minimum=0.0,
                maximum=10.0,
            ),
            "missing_current_fixture_is_regression": bool(
                policy.get("missing_current_fixture_is_regression", default_policy["missing_current_fixture_is_regression"])
            ),
        }
        baseline = payload.get("baseline") if isinstance(payload.get("baseline"), dict) else None
        current = payload.get("current") if isinstance(payload.get("current"), dict) else None
        return baseline, current, merged_policy

    def _fixture_deltas(self, baseline: dict[str, Any], current: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
        baseline_rows = {row["fixture_id"]: row for row in baseline["fixture_reports"]}
        current_rows = {row["fixture_id"]: row for row in current["fixture_reports"]}
        fixture_ids = sorted(set(baseline_rows) | set(current_rows))
        return [
            self._fixture_delta(fixture_id, baseline_rows.get(fixture_id), current_rows.get(fixture_id), policy)
            for fixture_id in fixture_ids
        ]

    def _fixture_delta(
        self,
        fixture_id: str,
        baseline: dict[str, Any] | None,
        current: dict[str, Any] | None,
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        baseline_status = self._smoke_status(baseline)
        current_status = self._smoke_status(current)
        baseline_score = self._score(baseline)
        current_score = self._score(current)
        score_delta = round(current_score - baseline_score, 4)
        baseline_next = self._next_step(baseline)
        current_next = self._next_step(current)
        reasons = self._regression_reasons(
            baseline_status,
            current_status,
            baseline_next,
            current_next,
            score_delta,
            policy,
        )
        return {
            "fixture_id": fixture_id,
            "title": (current or baseline or {}).get("title"),
            "baseline_status": baseline_status,
            "current_status": current_status,
            "baseline_score": baseline_score,
            "current_score": current_score,
            "score_delta": score_delta,
            "baseline_next_step": baseline_next,
            "current_next_step": current_next,
            "baseline_observed_model": self._safe_string((baseline or {}).get("observed_model")),
            "current_observed_model": self._safe_string((current or {}).get("observed_model")),
            "baseline_observed_cost_usd": self._number_or_none((baseline or {}).get("observed_cost_usd")),
            "current_observed_cost_usd": self._number_or_none((current or {}).get("observed_cost_usd")),
            "missing_signal_delta": self._count(current, "missing_signal_count") - self._count(baseline, "missing_signal_count"),
            "missing_task_delta": self._count(current, "missing_task_count") - self._count(baseline, "missing_task_count"),
            "newly_blocking": baseline_next not in ESCALATING_STEPS and current_next in ESCALATING_STEPS,
            "resolved_blocking": baseline_next in ESCALATING_STEPS and current_next not in ESCALATING_STEPS,
            "regression_reason_codes": reasons,
        }

    def _regression_reasons(
        self,
        baseline_status: str,
        current_status: str,
        baseline_next: str,
        current_next: str,
        score_delta: float,
        policy: dict[str, Any],
    ) -> list[str]:
        reasons: list[str] = []
        if baseline_status != "not_run" and current_status == "not_run" and policy["missing_current_fixture_is_regression"]:
            reasons.append("current_fixture_missing")
        if STATUS_RANK.get(current_status, 99) > STATUS_RANK.get(baseline_status, 99):
            reasons.append("smoke_status_worsened")
        if baseline_next not in ESCALATING_STEPS and current_next in ESCALATING_STEPS:
            reasons.append("new_escalation_required")
        if score_delta <= policy["score_regression_threshold"]:
            reasons.append("score_regression")
        return reasons

    def _cost_delta(self, baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, float | None]:
        baseline_cost = baseline["summary"]["observed_cost_usd"]
        current_cost = current["summary"]["observed_cost_usd"]
        if baseline_cost is None or current_cost is None:
            return {"cost_delta_usd": None, "cost_delta_ratio": None}
        delta = round(float(current_cost) - float(baseline_cost), 8)
        if baseline_cost <= 0:
            ratio = None if current_cost <= 0 else 1.0
        else:
            ratio = round(delta / float(baseline_cost), 4)
        return {"cost_delta_usd": delta, "cost_delta_ratio": ratio}

    def _status(
        self,
        current_observed: int,
        baseline_observed: int,
        regressed: list[dict[str, Any]],
        newly_blocking: list[dict[str, Any]],
        cost_delta: dict[str, float | None],
        policy: dict[str, Any],
    ) -> str:
        if not current_observed and not baseline_observed:
            return "not_run"
        if newly_blocking or any("score_regression" in row["regression_reason_codes"] for row in regressed):
            return "fail"
        if regressed:
            return "warn"
        cost_ratio = cost_delta.get("cost_delta_ratio")
        if cost_ratio is not None and cost_ratio > policy["cost_increase_warn_ratio"]:
            return "warn"
        return "pass"

    def _release_decision(self, status: str) -> str:
        return {
            "not_run": "run_baseline_and_current_fixture_batches",
            "fail": "block_default_promotion_until_regressions_are_fixed",
            "warn": "review_cost_or_warning_deltas_before_release",
            "pass": "current_fixture_run_is_stable_or_improved",
        }.get(status, "review_cost_or_warning_deltas_before_release")

    def _recommended_actions(
        self,
        status: str,
        regressed: list[dict[str, Any]],
        newly_blocking: list[dict[str, Any]],
        resolved_blocking: list[dict[str, Any]],
        cost_delta: dict[str, float | None],
    ) -> list[str]:
        if status == "not_run":
            return ["Submit baseline and current fixture-run-report payloads before comparing regression risk."]
        actions: list[str] = []
        if newly_blocking:
            actions.append("Block default promotion and fix newly blocking fixtures: " + ", ".join(row["fixture_id"] for row in newly_blocking[:6]) + ".")
        elif regressed:
            actions.append("Review regressed fixtures before release: " + ", ".join(row["fixture_id"] for row in regressed[:6]) + ".")
        if resolved_blocking:
            actions.append("Archive resolved fixture blockers as evidence: " + ", ".join(row["fixture_id"] for row in resolved_blocking[:6]) + ".")
        if cost_delta.get("cost_delta_ratio") is not None and cost_delta["cost_delta_ratio"] > 0:
            actions.append(f"Review observed fixture cost delta before expanding the run: {cost_delta['cost_delta_usd']} USD.")
        if not actions:
            actions.append("Current fixture run is stable or improved; attach this comparison to release evidence.")
        return actions[:6]

    def _average_delta(self, rows: list[dict[str, Any]]) -> float | None:
        observed = [row["score_delta"] for row in rows if row["baseline_status"] != "not_run" or row["current_status"] != "not_run"]
        if not observed:
            return None
        return round(sum(observed) / len(observed), 4)

    def _raw_field_count(self, value: Any) -> int:
        if isinstance(value, dict):
            count = sum(1 for key in value if str(key).lower() in RAW_FIELD_NAMES)
            return count + sum(self._raw_field_count(item) for item in value.values())
        if isinstance(value, list):
            return sum(self._raw_field_count(item) for item in value)
        return 0

    def _smoke_status(self, row: dict[str, Any] | None) -> str:
        return str((row or {}).get("smoke_status") or "not_run")

    def _score(self, row: dict[str, Any] | None) -> float:
        return self._number_or_none((row or {}).get("score")) or 0.0

    def _next_step(self, row: dict[str, Any] | None) -> str:
        return str((row or {}).get("recommended_next_step") or "run_cheap_first_fixture")

    def _count(self, row: dict[str, Any] | None, key: str) -> int:
        value = (row or {}).get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    def _safe_string(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value)
        if any(token in text.lower() for token in ("sk-", "bearer ", "@", "http://", "https://")):
            return "redacted"
        return text

    def _number_or_none(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return round(float(value), 8)
        return None

    def _number_or_default(self, value: Any, default: float, minimum: float, maximum: float) -> float:
        parsed = self._number_or_none(value)
        if parsed is None:
            return default
        return min(max(parsed, minimum), maximum)
