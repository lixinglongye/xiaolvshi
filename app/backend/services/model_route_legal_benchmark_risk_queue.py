from __future__ import annotations

from collections import defaultdict
from typing import Any

from services.gemini_newapi_cheap_first_calibration import GeminiNewapiCheapFirstCalibrationService
from services.legal_benchmark_research_refresh import LegalBenchmarkResearchRefreshService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService


class ModelRouteLegalBenchmarkRiskQueueService:
    """Build a metadata-only queue tying cheap-first routes to legal benchmark risk."""

    def __init__(
        self,
        calibration_service: GeminiNewapiCheapFirstCalibrationService | None = None,
        benchmark_refresh_service: LegalBenchmarkResearchRefreshService | None = None,
        benchmark_coverage_service: UserNeedBenchmarkCoverageService | None = None,
    ) -> None:
        self.calibration_service = calibration_service or GeminiNewapiCheapFirstCalibrationService()
        self.benchmark_refresh_service = benchmark_refresh_service or LegalBenchmarkResearchRefreshService()
        self.benchmark_coverage_service = benchmark_coverage_service or UserNeedBenchmarkCoverageService()

    def build_queue(self) -> dict[str, Any]:
        calibration = self.calibration_service.build_calibration()
        refresh = self.benchmark_refresh_service.build_refresh()
        coverage = self.benchmark_coverage_service.build_coverage()
        coverage_by_need = {
            str(row["need_id"]): row
            for row in coverage.get("coverage_rows", [])
            if isinstance(row, dict) and row.get("need_id")
        }
        refresh_by_need = self._refresh_rows_by_need(refresh)
        task_by_id = {
            str(task["id"]): task
            for task in calibration.get("calibration_tasks", [])
            if isinstance(task, dict) and task.get("id")
        }
        queue_rows = [
            self._queue_row(row, task_by_id.get(str(row.get("id")), {}), coverage_by_need, refresh_by_need)
            for row in calibration.get("calibration_rows", [])
            if isinstance(row, dict)
        ]
        user_need_rows = self._user_need_rows(queue_rows, coverage_by_need, refresh_by_need)
        status = self._status(queue_rows)
        validation_commands = self._validation_commands(calibration, refresh, coverage)

        return {
            "status": status,
            "method": {
                "type": "model-route-legal-benchmark-risk-queue",
                "notes": [
                    "Joins cheap-first calibration, public legal benchmark refresh mappings, and user-need coverage.",
                    "Ranks route changes for maintainer review before any Gemini/NewAPI default change.",
                    "Returns metadata only: task IDs, user-need IDs, source IDs, release gates, and validation commands.",
                ],
            },
            "summary": {
                "queue_row_count": len(queue_rows),
                "user_need_row_count": len(user_need_rows),
                "cheap_first_allowed_count": sum(1 for row in queue_rows if row["cheap_first_allowed"]),
                "balanced_precheck_count": sum(1 for row in queue_rows if row["balanced_precheck_required"]),
                "premium_exception_count": sum(1 for row in queue_rows if row["premium_exception_required"]),
                "watch_count": sum(1 for row in queue_rows if row["risk_level"] in {"watch", "operator_exception"}),
                "block_count": sum(1 for row in queue_rows if row["risk_level"] == "block"),
                "benchmark_license_watch_count": sum(
                    1 for row in queue_rows if "benchmark-license-review" in row["reason_codes"]
                ),
                "need_gap_watch_count": sum(1 for row in queue_rows if "user-need-gap" in row["reason_codes"]),
                "calibration_status": calibration["status"],
                "benchmark_refresh_status": refresh["status"],
                "benchmark_coverage_status": coverage["status"],
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "public_benchmark_score_claimed": False,
                "raw_payload_echoed": False,
                "secret_value_included": False,
            },
            "queue_rows": queue_rows,
            "user_need_rows": user_need_rows,
            "routing_policy": {
                "default_strategy": "cheap_first_with_fixture_backed_escalation",
                "cheap_model_start": "gemini-2.5-flash-lite",
                "balanced_precheck_requires": [
                    "passing cheap-first calibration row",
                    "linked legal benchmark refresh row",
                    "covered or partial user-need coverage",
                ],
                "premium_exception_requires": [
                    "operator review",
                    "fixture-backed legal or extraction risk",
                    "release-gate evidence before default promotion",
                ],
                "configuration_write_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
            },
            "recommended_actions": self._recommended_actions(queue_rows, user_need_rows),
            "privacy_boundary": {
                "returns_raw_benchmark_samples": False,
                "returns_public_benchmark_text": False,
                "returns_raw_legal_text": False,
                "returns_raw_model_output": False,
                "returns_prompts": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "network_called": False,
                "newapi_called": False,
                "dataset_downloaded": False,
                "source": "metadata_only_calibration_refresh_and_user_need_coverage",
            },
            "claim_boundary": {
                "production_accuracy_claimed": False,
                "public_benchmark_scores_claimed": False,
                "leaderboard_rank_claimed": False,
                "external_dataset_execution_claimed": False,
                "live_gateway_quality_claimed": False,
                "default_model_changed": False,
            },
            "validation_commands": validation_commands,
        }

    def _queue_row(
        self,
        calibration_row: dict[str, Any],
        task: dict[str, Any],
        coverage_by_need: dict[str, dict[str, Any]],
        refresh_by_need: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        task_id = str(calibration_row.get("id") or task.get("id") or "unknown")
        user_need_ids = [str(item) for item in task.get("user_need_ids", [])]
        coverage_rows = [coverage_by_need[need_id] for need_id in user_need_ids if need_id in coverage_by_need]
        missing_user_need_ids = [need_id for need_id in user_need_ids if need_id not in coverage_by_need]
        refresh_rows = [
            row
            for need_id in user_need_ids
            for row in refresh_by_need.get(need_id, [])
        ]
        source_ids = sorted(
            {
                str(source_id)
                for row in refresh_rows
                for source_id in (row.get("source_ids") or [row.get("source_id")])
                if source_id
            }
        )
        release_gate_links = sorted(
            {
                str(item)
                for item in [
                    *(task.get("release_gate_links") or []),
                    *(calibration_row.get("release_gate_links") or []),
                    *[
                        gate
                        for row in refresh_rows
                        for gate in row.get("release_gate_links", [])
                    ],
                ]
                if item
            }
        )
        decision = str(calibration_row.get("calibration_decision") or "unknown")
        reason_codes = self._reason_codes(calibration_row, coverage_rows, refresh_rows, missing_user_need_ids)
        risk_level = self._risk_level(calibration_row, decision, reason_codes)
        validation_commands = sorted(
            {
                command
                for row in refresh_rows
                for command in row.get("validation_commands", [])
            }
            | set(self._calibration_validation_commands(task_id, decision))
        )

        return {
            "id": f"{task_id}-legal-benchmark-risk",
            "task_id": task_id,
            "task": str(calibration_row.get("task") or task.get("task") or "unknown"),
            "product_area": str(calibration_row.get("product_area") or task.get("product_area") or "unknown"),
            "risk_level": risk_level,
            "priority": self._priority(risk_level, coverage_rows, decision),
            "calibration_status": str(calibration_row.get("status") or "unknown"),
            "calibration_decision": decision,
            "cheap_first_allowed": decision == "keep_cheap_first_default",
            "balanced_precheck_required": decision == "keep_balanced_after_precheck",
            "premium_exception_required": decision == "require_operator_premium_exception",
            "selected_model": calibration_row.get("selected_model"),
            "canonical_model": calibration_row.get("canonical_model"),
            "cost_tier": str(calibration_row.get("cost_tier") or "unknown"),
            "fixture_ids": list(calibration_row.get("fixture_ids") or task.get("fixture_ids") or []),
            "fixture_score": calibration_row.get("fixture_score"),
            "quality_floor": calibration_row.get("quality_floor") or task.get("quality_floor"),
            "research_source_ids": sorted(set([*source_ids, *[str(item) for item in calibration_row.get("research_source_ids", [])]])),
            "user_need_ids": user_need_ids,
            "missing_user_need_ids": missing_user_need_ids,
            "coverage_statuses": sorted({str(row.get("coverage_status") or "unknown") for row in coverage_rows}),
            "public_benchmark_statuses": sorted({str(row.get("public_benchmark_status") or "unknown") for row in coverage_rows}),
            "calibration_statuses": sorted({str(row.get("calibration_status") or "unknown") for row in coverage_rows}),
            "linked_refresh_row_ids": sorted({str(row.get("id") or "") for row in refresh_rows if row.get("id")}),
            "release_gate_links": release_gate_links,
            "reason_codes": reason_codes,
            "next_action": self._next_action(risk_level, decision, reason_codes),
            "validation_commands": validation_commands,
            "newapi_called": False,
            "network_called": False,
            "dataset_download_required": False,
            "public_score_claimed": False,
            "raw_legal_text_included": False,
            "secret_value_included": False,
        }

    def _refresh_rows_by_need(self, refresh: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        by_need: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in refresh.get("refresh_rows", []):
            if not isinstance(row, dict):
                continue
            for need_id in row.get("user_need_ids", []):
                by_need[str(need_id)].append(row)
        return by_need

    def _user_need_rows(
        self,
        queue_rows: list[dict[str, Any]],
        coverage_by_need: dict[str, dict[str, Any]],
        refresh_by_need: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        queue_by_need: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in queue_rows:
            for need_id in row["user_need_ids"]:
                queue_by_need[need_id].append(row)

        rows: list[dict[str, Any]] = []
        for need_id in sorted(queue_by_need):
            coverage = coverage_by_need.get(need_id, {})
            linked_queue_rows = queue_by_need[need_id]
            refresh_rows = refresh_by_need.get(need_id, [])
            rows.append(
                {
                    "need_id": need_id,
                    "title": str(coverage.get("title") or need_id),
                    "priority_band": str(coverage.get("priority_band") or "unknown"),
                    "priority_score": int(coverage.get("priority_score") or 0),
                    "coverage_status": str(coverage.get("coverage_status") or "not_mapped"),
                    "public_benchmark_status": str(coverage.get("public_benchmark_status") or "not_mapped"),
                    "calibration_status": str(coverage.get("calibration_status") or "not_mapped"),
                    "queue_row_ids": [row["id"] for row in linked_queue_rows],
                    "task_ids": [row["task_id"] for row in linked_queue_rows],
                    "refresh_row_ids": sorted({str(row.get("id")) for row in refresh_rows if row.get("id")}),
                    "research_source_ids": sorted(
                        {
                            str(source_id)
                            for row in linked_queue_rows
                            for source_id in row["research_source_ids"]
                        }
                    ),
                    "highest_risk_level": self._highest_risk_level(linked_queue_rows),
                    "cheap_first_allowed_count": sum(1 for row in linked_queue_rows if row["cheap_first_allowed"]),
                    "premium_exception_count": sum(1 for row in linked_queue_rows if row["premium_exception_required"]),
                    "next_action": self._need_next_action(need_id, linked_queue_rows, coverage),
                }
            )
        return rows

    def _reason_codes(
        self,
        calibration_row: dict[str, Any],
        coverage_rows: list[dict[str, Any]],
        refresh_rows: list[dict[str, Any]],
        missing_user_need_ids: list[str],
    ) -> list[str]:
        reasons = set(str(item) for item in calibration_row.get("reason_codes", []))
        if str(calibration_row.get("status")) in {"warn", "fail"}:
            reasons.add("calibration-attention")
        if str(calibration_row.get("calibration_decision")) == "require_operator_premium_exception":
            reasons.add("operator-premium-exception")
        if missing_user_need_ids:
            reasons.add("missing-user-need-mapping")
        if not refresh_rows:
            reasons.add("missing-legal-benchmark-refresh")
        if any(row.get("coverage_status") == "gap" for row in coverage_rows):
            reasons.add("user-need-gap")
        if any(row.get("public_benchmark_status") == "license_review_required" for row in coverage_rows):
            reasons.add("benchmark-license-review")
        if any(row.get("calibration_status") in {"warn", "fail"} for row in coverage_rows):
            reasons.add("user-need-calibration-attention")
        return sorted(reasons)

    def _risk_level(
        self,
        calibration_row: dict[str, Any],
        decision: str,
        reason_codes: list[str],
    ) -> str:
        if str(calibration_row.get("status")) == "fail" or "missing-user-need-mapping" in reason_codes:
            return "block"
        if decision == "require_operator_premium_exception":
            return "operator_exception"
        if {"benchmark-license-review", "user-need-gap", "calibration-attention"} & set(reason_codes):
            return "watch"
        return "ready"

    def _priority(self, risk_level: str, coverage_rows: list[dict[str, Any]], decision: str) -> int:
        base = {"block": 100, "operator_exception": 88, "watch": 72, "ready": 45}.get(risk_level, 50)
        if decision == "keep_balanced_after_precheck":
            base += 6
        if any(row.get("priority_band") == "high" for row in coverage_rows):
            base += 5
        return min(base, 100)

    def _highest_risk_level(self, rows: list[dict[str, Any]]) -> str:
        rank = {"ready": 0, "watch": 1, "operator_exception": 2, "block": 3}
        return max((str(row["risk_level"]) for row in rows), key=lambda item: rank.get(item, -1))

    def _next_action(self, risk_level: str, decision: str, reason_codes: list[str]) -> str:
        if risk_level == "block":
            return "Block route changes until missing mappings or failed calibration rows are repaired."
        if decision == "require_operator_premium_exception":
            return "Keep premium use as an operator exception with fixture evidence; do not promote it to default."
        if decision == "keep_balanced_after_precheck":
            return "Keep cheap precheck first, then allow balanced review only with linked benchmark and user-need evidence."
        if "benchmark-license-review" in reason_codes:
            return "Keep public benchmark evidence metadata-only until license review passes."
        return "Keep cheap-first default and rerun local fixture validation before any model-default change."

    def _need_next_action(
        self,
        need_id: str,
        rows: list[dict[str, Any]],
        coverage: dict[str, Any],
    ) -> str:
        highest = self._highest_risk_level(rows)
        if highest == "block":
            return f"Repair route evidence before claiming {need_id} is covered by cheap-first routing."
        if highest == "operator_exception":
            return f"Keep {need_id} premium paths explicit and operator-reviewed."
        if coverage.get("public_benchmark_status") == "license_review_required":
            return f"Keep {need_id} public benchmark mappings metadata-only until license review passes."
        return f"Review {need_id} route rows before changing model defaults."

    def _recommended_actions(
        self,
        queue_rows: list[dict[str, Any]],
        user_need_rows: list[dict[str, Any]],
    ) -> list[str]:
        blockers = [row for row in queue_rows if row["risk_level"] == "block"]
        if blockers:
            return [f"Resolve blocking route evidence for {row['task_id']}." for row in blockers[:5]]
        actions = [
            "Keep Gemini/NewAPI default changes cheap-first unless a queue row has fixture-backed escalation evidence.",
            "Treat public legal benchmark links as metadata-only until license review and local validation archives exist.",
        ]
        premium_rows = [row for row in queue_rows if row["premium_exception_required"]]
        if premium_rows:
            actions.append(
                "Review premium exceptions before default promotion: "
                + ", ".join(row["task_id"] for row in premium_rows)
                + "."
            )
        gap_needs = [row["need_id"] for row in user_need_rows if row["coverage_status"] == "gap"]
        if gap_needs:
            actions.append("Add synthetic fixtures or backlog links for user-need gaps: " + ", ".join(gap_needs) + ".")
        return actions

    def _status(self, queue_rows: list[dict[str, Any]]) -> str:
        risk_levels = {row["risk_level"] for row in queue_rows}
        if "block" in risk_levels:
            return "blocked"
        if {"watch", "operator_exception"} & risk_levels:
            return "ready_with_watchlist"
        return "ready"

    def _calibration_validation_commands(self, task_id: str, decision: str) -> list[str]:
        commands = ["python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py -q"]
        if decision == "require_operator_premium_exception":
            commands.append("python -m pytest tests/test_model_cost_guardrails.py tests/test_extraction_quality.py -q")
        if "legal" in task_id or "document" in task_id:
            commands.append("python -m pytest tests/test_legal_review_benchmark.py tests/test_legal_document_benchmark_suite.py -q")
        return commands

    def _validation_commands(
        self,
        calibration: dict[str, Any],
        refresh: dict[str, Any],
        coverage: dict[str, Any],
    ) -> list[str]:
        commands = {
            "python -m pytest tests/test_model_route_legal_benchmark_risk_queue.py -q",
            "python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py tests/test_user_need_benchmark_coverage.py tests/test_legal_benchmark_research_refresh.py -q",
        }
        commands.update(str(command) for command in calibration.get("validation_commands", []) if str(command).startswith("python -m pytest "))
        commands.update(str(command) for command in refresh.get("validation_commands", []) if str(command).startswith("python -m pytest "))
        commands.update(str(command) for command in coverage.get("validation_commands", []) if str(command).startswith("python -m pytest "))
        return sorted(commands)
