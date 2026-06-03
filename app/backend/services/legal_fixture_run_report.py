from __future__ import annotations

from typing import Any

from services.legal_fixture_improvement import LegalFixtureImprovementService
from services.legal_fixture_run_plan import LegalFixtureRunPlanService
from services.legal_review_benchmark import LegalReviewBenchmarkService


class LegalFixtureRunReportService:
    """Summarize cheap-first fixture observations into release and escalation decisions."""

    def __init__(
        self,
        benchmark_service: LegalReviewBenchmarkService | None = None,
        improvement_service: LegalFixtureImprovementService | None = None,
        run_plan_service: LegalFixtureRunPlanService | None = None,
    ) -> None:
        self.benchmark_service = benchmark_service or LegalReviewBenchmarkService()
        self.improvement_service = improvement_service or LegalFixtureImprovementService(self.benchmark_service)
        self.run_plan_service = run_plan_service or LegalFixtureRunPlanService()

    def build_report(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        observations, run_metadata = self._split_payload(payload)
        smoke = self.benchmark_service.evaluate_fixture_smoke(observations)
        improvement = self.improvement_service.build_plan(observations)
        run_plan = self.run_plan_service.build_plan()
        fixture_reports = self._fixture_reports(smoke, improvement, run_plan, run_metadata)
        escalation_fixture_ids = [
            item["fixture_id"]
            for item in fixture_reports
            if item["recommended_next_step"] in {"escalate_selected_fixture", "apply_high_priority_improvements"}
        ]
        status = self._status(smoke["status"], improvement["status"], escalation_fixture_ids)
        return {
            "status": status,
            "release_decision": self._release_decision(status),
            "method": {
                "type": "cheap-first-legal-fixture-run-report",
                "notes": [
                    "Evaluates supplied fixture observations only; it does not call any model or gateway.",
                    "Cheap-first defaults are kept only when smoke coverage passes without high-priority actions.",
                    "Escalation decisions are fixture-scoped and should not make premium models the default.",
                ],
            },
            "summary": {
                "fixture_count": smoke["fixture_count"],
                "observed_fixture_count": sum(1 for item in fixture_reports if item["smoke_status"] != "not_run"),
                "passed_fixture_count": smoke["passed_fixture_count"],
                "warning_fixture_count": smoke["warning_fixture_count"],
                "failed_fixture_count": smoke["failed_fixture_count"],
                "not_run_fixture_count": smoke["not_run_fixture_count"],
                "escalation_required_count": len(escalation_fixture_ids),
                "high_priority_improvement_count": improvement["summary"]["high_priority_action_count"],
                "observed_request_count": len(run_metadata),
                "observed_cost_usd": self._observed_cost(run_metadata),
                "cheap_first_estimated_cost_usd": run_plan["summary"]["estimated_min_cost_usd"],
                "worst_case_estimated_cost_usd": run_plan["summary"]["estimated_max_cost_usd"],
            },
            "fixture_reports": fixture_reports,
            "escalation_fixture_ids": escalation_fixture_ids,
            "smoke_result": smoke,
            "improvement_summary": improvement["summary"],
            "run_evidence_template": self._run_evidence_template(run_plan),
            "recommended_actions": self._recommended_actions(status, fixture_reports),
            "privacy_note": (
                "Observed output text is used only for request-scope scoring. The report returns fixture metadata, "
                "scores, and actions, not raw model output text or credentials."
            ),
        }

    def _split_payload(self, payload: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
        if not payload:
            return {}, {}
        observations = payload.get("observations")
        run_metadata = payload.get("run_metadata")
        if isinstance(observations, dict):
            return observations, run_metadata if isinstance(run_metadata, dict) else {}
        return payload, {}

    def _fixture_reports(
        self,
        smoke: dict[str, Any],
        improvement: dict[str, Any],
        run_plan: dict[str, Any],
        run_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        actions_by_fixture: dict[str, list[dict[str, Any]]] = {}
        for action in improvement["actions"]:
            actions_by_fixture.setdefault(action["fixture_id"], []).append(action)

        steps_by_key = {
            (step["fixture_id"], step["phase"]): step
            for step in run_plan["steps"]
        }
        rows: list[dict[str, Any]] = []
        for result in smoke["fixture_results"]:
            fixture_id = result["fixture_id"]
            actions = actions_by_fixture.get(fixture_id, [])
            high_priority = [action for action in actions if action["priority"] == "high"]
            cheap_step = steps_by_key.get((fixture_id, "cheap_first"), {})
            escalation_step = steps_by_key.get((fixture_id, "escalation_if_needed"))
            metadata = run_metadata.get(fixture_id) if isinstance(run_metadata.get(fixture_id), dict) else {}
            rows.append(
                {
                    "fixture_id": fixture_id,
                    "title": result["title"],
                    "smoke_status": result["status"],
                    "score": result["score"],
                    "observed_route": result["observed_route"],
                    "expected_routes": result["expected_routes"],
                    "matched_signal_count": len(result["matched_signals"]),
                    "missing_signal_count": len(result["missing_signals"]),
                    "missing_task_count": len(result["missing_tasks"]),
                    "high_priority_action_count": len(high_priority),
                    "cheap_first_step_id": cheap_step.get("step_id"),
                    "cheap_first_model": cheap_step.get("model"),
                    "escalation_step_id": escalation_step.get("step_id") if escalation_step else None,
                    "escalation_model": escalation_step.get("model") if escalation_step else None,
                    "observed_model": metadata.get("model") or cheap_step.get("model"),
                    "observed_phase": metadata.get("phase") or cheap_step.get("phase"),
                    "observed_cost_usd": self._number_or_none(metadata.get("estimated_cost_usd")),
                    "recommended_next_step": self._next_step(result["status"], bool(escalation_step), high_priority),
                    "missing_signals": result["missing_signals"],
                    "missing_tasks": result["missing_tasks"],
                }
            )
        return rows

    def _next_step(self, smoke_status: str, has_escalation: bool, high_priority: list[dict[str, Any]]) -> str:
        if smoke_status == "not_run":
            return "run_cheap_first_fixture"
        if high_priority:
            return "apply_high_priority_improvements"
        if smoke_status == "fail" and has_escalation:
            return "escalate_selected_fixture"
        if smoke_status == "warn":
            return "review_warning_fixture"
        if smoke_status == "pass":
            return "keep_cheap_first_result"
        return "review_fixture_result"

    def _status(self, smoke_status: str, improvement_status: str, escalation_fixture_ids: list[str]) -> str:
        if smoke_status == "not_run":
            return "not_run"
        if escalation_fixture_ids or improvement_status == "needs_improvement":
            return "needs_escalation"
        if smoke_status == "warn" or improvement_status == "review_recommended":
            return "review_recommended"
        if smoke_status == "pass" and improvement_status == "ready":
            return "ready"
        return "review_recommended"

    def _release_decision(self, status: str) -> str:
        return {
            "not_run": "run_cheap_first_fixture_batches",
            "needs_escalation": "hold_default_changes_and_fix_selected_fixtures",
            "review_recommended": "review_warnings_before_release",
            "ready": "keep_cheap_first_defaults",
        }.get(status, "review_warnings_before_release")

    def _recommended_actions(self, status: str, fixture_reports: list[dict[str, Any]]) -> list[str]:
        if status == "not_run":
            return ["Run fixture-run-plan cheap_first batches, then submit observations to this report endpoint."]
        target_rows = [
            row
            for row in fixture_reports
            if row["recommended_next_step"] in {"apply_high_priority_improvements", "escalate_selected_fixture"}
        ]
        if target_rows:
            return [
                f"{row['fixture_id']}: {row['recommended_next_step']} using {row['escalation_model'] or row['cheap_first_model']}."
                for row in target_rows
            ]
        if status == "review_recommended":
            return ["Review warning fixtures and document any accepted gaps before release readiness is marked pass."]
        return ["Fixture report is ready; keep cheap-first defaults and attach this report to release evidence."]

    def _run_evidence_template(self, run_plan: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_endpoint": "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
            "inputs_to_archive": [
                "fixture-run-plan summary",
                "fixture-smoke score",
                "fixture-improvement summary",
                "selected fixture_reports",
            ],
            "validation_command": (
                "python -m pytest tests/test_legal_fixture_run_report.py "
                "tests/test_legal_fixture_run_plan.py tests/test_legal_review_benchmark.py -q"
            ),
            "expected_cheap_first_cost_usd": run_plan["summary"]["estimated_min_cost_usd"],
            "expected_worst_case_cost_usd": run_plan["summary"]["estimated_max_cost_usd"],
        }

    def _observed_cost(self, run_metadata: dict[str, Any]) -> float | None:
        costs = [
            self._number_or_none(value.get("estimated_cost_usd"))
            for value in run_metadata.values()
            if isinstance(value, dict)
        ]
        known_costs = [value for value in costs if value is not None]
        if not known_costs:
            return None
        return round(sum(known_costs), 8)

    def _number_or_none(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return round(max(0.0, float(value)), 8)
        return None
