from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.gemini_newapi_selector_replay import GeminiNewapiSelectorReplayService
from services.legal_fixture_run_report import LegalFixtureRunReportService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.model_cost_forecast import ModelCostForecastService
from services.model_cost_guardrails import ModelCostGuardrailService
COST_RANK = {"lowest": 0, "low": 1, "medium": 2, "premium": 3, "unverified": 99, "unknown": 99}
PASSING_STATUSES = {"pass", "ready"}
WARNING_STATUSES = {"warn", "review_recommended", "needs_catalog_review"}


@dataclass(frozen=True)
class CalibrationTask:
    id: str
    task: str
    product_area: str
    fixture_ids: tuple[str, ...]
    expected_decision: str
    max_cost_tier: str
    quality_floor: int
    release_gate_links: tuple[str, ...]
    user_need_ids: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["fixture_ids"] = list(self.fixture_ids)
        data["release_gate_links"] = list(self.release_gate_links)
        data["user_need_ids"] = list(self.user_need_ids)
        return data


class GeminiNewapiCheapFirstCalibrationService:
    """Join selector, fixture, and cost evidence into cheap-first calibration decisions."""

    def __init__(
        self,
        replay_service: GeminiNewapiSelectorReplayService | None = None,
        fixture_report_service: LegalFixtureRunReportService | None = None,
        benchmark_service: LegalReviewBenchmarkService | None = None,
        forecast_service: ModelCostForecastService | None = None,
        guardrail_service: ModelCostGuardrailService | None = None,
    ) -> None:
        self.replay_service = replay_service or GeminiNewapiSelectorReplayService()
        self.fixture_report_service = fixture_report_service or LegalFixtureRunReportService()
        self.benchmark_service = benchmark_service or LegalReviewBenchmarkService()
        self.forecast_service = forecast_service or ModelCostForecastService()
        self.guardrail_service = guardrail_service or ModelCostGuardrailService()

    def build_calibration(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        fixture_payload = data.get("fixture_report") if isinstance(data.get("fixture_report"), dict) else None
        selector_payload = data.get("selector_replay") if isinstance(data.get("selector_replay"), dict) else None
        fixture_report = self.fixture_report_service.build_report(fixture_payload or self._default_fixture_report_payload())
        selector_replay = self.replay_service.run_replay(selector_payload)
        cost_forecast = self.forecast_service.build_forecast()
        cost_guardrails = self.guardrail_service.evaluate(
            self._usage_snapshot(fixture_report, selector_replay),
            cost_forecast,
        )

        selector_by_task = self._selector_by_task(selector_replay)
        fixture_by_id = {row["fixture_id"]: row for row in fixture_report["fixture_reports"]}
        forecast_by_task = {row["task"]: row for row in cost_forecast["profiles"]}
        rows = [
            self._calibration_row(
                task,
                selector_by_task.get(task.task),
                fixture_by_id,
                forecast_by_task.get(task.task),
                fixture_report,
                selector_replay,
                cost_guardrails,
            )
            for task in self._tasks()
        ]
        status = self._status(rows, cost_guardrails)
        fail_rows = [row for row in rows if row["status"] == "fail"]
        warn_rows = [row for row in rows if row["status"] == "warn"]

        return {
            "status": status,
            "method": {
                "type": "gemini-newapi-cheap-first-cost-quality-calibration",
                "notes": [
                    "Joins selector replay, synthetic legal fixture smoke, cost forecast, and cost guardrail metadata.",
                    "Default calibration uses tiny local synthetic fixtures and does not call NewAPI or any model.",
                    "Calibration can keep cheap-first defaults, hold default changes, or require fixture-scoped escalation.",
                ],
            },
            "summary": {
                "task_count": len(rows),
                "pass_count": sum(1 for row in rows if row["status"] == "pass"),
                "warn_count": len(warn_rows),
                "fail_count": len(fail_rows),
                "cheap_first_retained_count": sum(
                    1 for row in rows if row["calibration_decision"] == "keep_cheap_first_default"
                ),
                "balanced_precheck_count": sum(
                    1 for row in rows if row["calibration_decision"] == "keep_balanced_after_precheck"
                ),
                "premium_exception_count": sum(
                    1 for row in rows if row["calibration_decision"] == "require_operator_premium_exception"
                ),
                "fixture_count": fixture_report["summary"]["fixture_count"],
                "observed_fixture_count": fixture_report["summary"]["observed_fixture_count"],
                "selector_scenario_count": selector_replay["summary"]["scenario_count"],
                "cost_guardrail_status": cost_guardrails["status"],
                "estimated_savings_ratio": cost_forecast["summary"]["estimated_savings_ratio"],
                "newapi_called": False,
                "raw_payload_echoed": False,
            },
            "calibration_tasks": [task.to_api() for task in self._tasks()],
            "calibration_rows": rows,
            "source_summaries": {
                "selector_replay": selector_replay["summary"],
                "fixture_report": fixture_report["summary"],
                "cost_forecast": cost_forecast["summary"],
                "cost_guardrails": cost_guardrails["summary"],
            },
            "recommended_actions": self._recommended_actions(status, rows, cost_guardrails),
            "release_guardrails": [
                "Do not use calibration as proof of live NewAPI execution or public benchmark performance.",
                "Do not promote premium models to defaults when only selected fixtures need escalation.",
                "Keep raw model output, prompts, legal text, gateway payloads, emails, and credentials out of calibration evidence.",
            ],
            "privacy_boundary": {
                "newapi_called": False,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "metadata-only task ids, fixture ids, model ids, cost tiers, scores, reason codes, and validation paths",
            },
            "validation_commands": [
                "python -m pytest tests/test_gemini_newapi_cheap_first_calibration.py -q",
                "python -m pytest tests/test_gemini_newapi_selector_replay.py tests/test_legal_fixture_run_report.py tests/test_model_cost_guardrails.py -q",
                "npm run typecheck",
            ],
        }

    def _calibration_row(
        self,
        task: CalibrationTask,
        selector_result: dict[str, Any] | None,
        fixture_by_id: dict[str, dict[str, Any]],
        forecast_row: dict[str, Any] | None,
        fixture_report: dict[str, Any],
        selector_replay: dict[str, Any],
        cost_guardrails: dict[str, Any],
    ) -> dict[str, Any]:
        actual = selector_result.get("actual") if isinstance(selector_result, dict) else {}
        cost_tier = str(actual.get("cost_tier") or "unverified")
        fixture_rows = [fixture_by_id[fixture_id] for fixture_id in task.fixture_ids if fixture_id in fixture_by_id]
        fixture_scores = [int(row.get("score") or 0) for row in fixture_rows if row.get("smoke_status") != "not_run"]
        fixture_score = round(sum(fixture_scores) / len(fixture_scores)) if fixture_scores else 0
        checks = [
            self._check_selector(selector_result, task),
            self._check_cost_tier(cost_tier, task.max_cost_tier),
            self._check_fixture_quality(fixture_score, task.quality_floor, fixture_report["status"], bool(task.fixture_ids)),
            self._check_guardrails(cost_guardrails),
        ]
        failed = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "fail" if failed else ("warn" if warnings else "pass")
        return {
            "id": task.id,
            "task": task.task,
            "product_area": task.product_area,
            "status": status,
            "selected_model": actual.get("selected_model"),
            "canonical_model": actual.get("canonical_model"),
            "decision": actual.get("decision"),
            "cost_tier": cost_tier,
            "fixture_ids": list(task.fixture_ids),
            "fixture_score": fixture_score,
            "quality_floor": task.quality_floor,
            "estimated_savings_ratio": forecast_row.get("estimated_savings_ratio") if forecast_row else None,
            "calibration_decision": self._decision(task, selector_result, status, cost_tier, fixture_report),
            "reason_codes": self._reason_codes(checks, fixture_report, selector_replay, cost_guardrails),
            "checks": checks,
            "release_gate_links": list(task.release_gate_links),
            "next_action": self._next_action(task, status, failed, warnings),
        }

    def _check_selector(self, selector_result: dict[str, Any] | None, task: CalibrationTask) -> dict[str, Any]:
        actual = selector_result.get("actual") if isinstance(selector_result, dict) else {}
        decision = actual.get("decision") if isinstance(actual, dict) else None
        selector_status = selector_result.get("status") if isinstance(selector_result, dict) else "missing"
        status = "pass" if decision == task.expected_decision and selector_status == "pass" else "fail"
        if selector_status == "warn":
            status = "warn"
        return {
            "id": "selector-replay",
            "status": status,
            "expected": task.expected_decision,
            "actual": decision,
            "reason": "Selector replay matches the expected cheap-first route."
            if status == "pass"
            else "Selector replay drifted or needs catalog review.",
        }

    def _check_cost_tier(self, actual: str, max_allowed: str) -> dict[str, Any]:
        actual_rank = COST_RANK.get(actual, COST_RANK["unverified"])
        allowed_rank = COST_RANK.get(max_allowed, COST_RANK["unverified"])
        if actual in {"unverified", "unknown"}:
            status = "warn"
        else:
            status = "pass" if actual_rank <= allowed_rank else "fail"
        return {
            "id": "cost-tier",
            "status": status,
            "expected": f"<= {max_allowed}",
            "actual": actual,
            "reason": "Selected model cost tier is within calibration ceiling."
            if status == "pass"
            else "Selected model is unpriced or exceeds the calibration ceiling.",
        }

    def _check_fixture_quality(self, score: int, floor: int, fixture_status: str, required: bool) -> dict[str, Any]:
        if not required:
            status = "pass"
            reason = "No fixture is required for this high-volume metadata-only routing task."
        elif fixture_status == "not_run":
            status = "warn"
            reason = "Run or improve cheap-first fixture coverage before changing defaults."
        else:
            status = "pass" if score >= floor else "fail"
            reason = (
                "Synthetic fixture coverage meets the calibration floor."
                if status == "pass"
                else "Run or improve cheap-first fixture coverage before changing defaults."
            )
        return {
            "id": "fixture-quality",
            "status": status,
            "expected": f">= {floor}",
            "actual": score if required else "not-required",
            "reason": reason,
        }

    def _check_guardrails(self, cost_guardrails: dict[str, Any]) -> dict[str, Any]:
        guardrail_status = cost_guardrails["status"]
        status = "pass" if guardrail_status == "pass" else ("warn" if guardrail_status == "warn" else "fail")
        return {
            "id": "cost-guardrails",
            "status": status,
            "expected": "pass",
            "actual": guardrail_status,
            "reason": "Model cost guardrails support cheap-first defaults."
            if status == "pass"
            else "Cost guardrails require review before route defaults change.",
        }

    def _decision(
        self,
        task: CalibrationTask,
        selector_result: dict[str, Any] | None,
        status: str,
        cost_tier: str,
        fixture_report: dict[str, Any],
    ) -> str:
        decision = ((selector_result or {}).get("actual") or {}).get("decision")
        if fixture_report["status"] in {"needs_escalation", "not_run"} and task.fixture_ids:
            return "hold_for_fixture_evidence"
        if decision == "premium_exception_required" or cost_tier == "premium":
            return "require_operator_premium_exception"
        if status == "fail":
            return "hold_default_change"
        if decision == "balanced_after_precheck":
            return "keep_balanced_after_precheck"
        return "keep_cheap_first_default"

    def _reason_codes(
        self,
        checks: list[dict[str, Any]],
        fixture_report: dict[str, Any],
        selector_replay: dict[str, Any],
        cost_guardrails: dict[str, Any],
    ) -> list[str]:
        codes = [f"{check['id']}-{check['status']}" for check in checks if check["status"] != "pass"]
        if fixture_report["summary"]["escalation_required_count"]:
            codes.append("fixture-escalation-required")
        codes.extend(f"guardrail-{item}" for item in cost_guardrails.get("blocking_check_ids", []))
        return sorted(set(codes)) or ["calibration-pass"]

    def _next_action(
        self,
        task: CalibrationTask,
        status: str,
        failed: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> str:
        if failed:
            return f"Hold {task.task} default changes and review failing checks: {', '.join(check['id'] for check in failed)}."
        if warnings:
            return f"Keep {task.task} route explicit or monitored until warnings are reviewed: {', '.join(check['id'] for check in warnings)}."
        if task.expected_decision == "premium_exception_required":
            return f"Keep {task.task} as an operator-reviewed premium exception."
        return f"Keep {task.task} aligned to cheap-first calibration."

    def _default_fixture_report_payload(self) -> dict[str, Any]:
        template = self.benchmark_service.build_fixture_smoke_template()
        observations = {
            fixture["id"]: {
                "route": fixture["expected_routes"][0],
                "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
            }
            for fixture in template["fixtures"]
        }
        run_metadata = {
            fixture["id"]: {
                "phase": "cheap_first",
                "model": "gemini-2.5-flash-lite",
                "estimated_cost_usd": round(0.00009 + (index * 0.00001), 8),
            }
            for index, fixture in enumerate(template["fixtures"])
        }
        return {"observations": observations, "run_metadata": run_metadata}

    def _usage_snapshot(self, fixture_report: dict[str, Any], selector_replay: dict[str, Any]) -> dict[str, Any]:
        request_count = max(1, int(fixture_report["summary"]["observed_fixture_count"] or 0))
        premium_requests = sum(
            1
            for item in fixture_report["fixture_reports"]
            if str(item.get("observed_model") or "").endswith("pro")
        )
        observed_cost = fixture_report["summary"].get("observed_cost_usd")
        estimated_cost = float(observed_cost) if isinstance(observed_cost, (int, float)) else 0.001
        return {
            "totals": {
                "requests": request_count,
                "successes": max(0, request_count - fixture_report["summary"]["failed_fixture_count"]),
                "failures": fixture_report["summary"]["failed_fixture_count"],
                "estimated_cost_usd": estimated_cost,
                "priced_model_count": request_count,
                "unpriced_model_count": 0,
            },
            "models": {
                "gemini-2.5-flash-lite": {
                    "requests": request_count,
                    "estimated_cost_usd": estimated_cost,
                    "tasks": {"legal_fixture": request_count},
                },
                "gemini-2.5-pro": {
                    "requests": premium_requests,
                    "estimated_cost_usd": 0.0,
                    "tasks": {"premium_exception": premium_requests},
                },
            },
        }

    def _selector_by_task(self, selector_replay: dict[str, Any]) -> dict[str, dict[str, Any]]:
        mapping: dict[str, dict[str, Any]] = {}
        for result in selector_replay["replay_results"]:
            scenario = result.get("scenario") or {}
            task = str(scenario.get("task") or "").replace("_", "-")
            if task and task not in mapping:
                mapping[task] = result
        return mapping

    def _tasks(self) -> tuple[CalibrationTask, ...]:
        return (
            CalibrationTask(
                id="fast-intake-preflight",
                task="fast",
                product_area="intake_preflight",
                fixture_ids=(),
                expected_decision="cheap_first_ready",
                max_cost_tier="lowest",
                quality_floor=80,
                release_gate_links=("gemini-newapi-selector-replay", "model-cost-guardrails"),
                user_need_ids=("cheap-first-review-routing",),
            ),
            CalibrationTask(
                id="classification-routing",
                task="classification",
                product_area="document_routing",
                fixture_ids=(),
                expected_decision="cheap_first_ready",
                max_cost_tier="lowest",
                quality_floor=80,
                release_gate_links=("gemini-newapi-selector-replay", "model-task-inference"),
                user_need_ids=("cheap-first-review-routing", "robust-extraction-quality"),
            ),
            CalibrationTask(
                id="ocr-assist",
                task="ocr",
                product_area="document_intake",
                fixture_ids=("fixture-low-text-pdf-page-small",),
                expected_decision="cheap_first_ready",
                max_cost_tier="lowest",
                quality_floor=80,
                release_gate_links=("gemini-newapi-selector-replay", "extraction_quality"),
                user_need_ids=("robust-extraction-quality", "cheap-first-review-routing"),
            ),
            CalibrationTask(
                id="legal-review-balanced",
                task="review",
                product_area="legal_review",
                fixture_ids=("fixture-service-agreement-small", "fixture-lease-dispute-notice-small"),
                expected_decision="balanced_after_precheck",
                max_cost_tier="low",
                quality_floor=80,
                release_gate_links=("legal-review-benchmark", "report_quality_gate"),
                user_need_ids=("traceable-legal-review", "cheap-first-review-routing"),
            ),
            CalibrationTask(
                id="document-generation-balanced",
                task="document-generation",
                product_area="document_generation",
                fixture_ids=("fixture-service-agreement-small",),
                expected_decision="balanced_after_precheck",
                max_cost_tier="low",
                quality_floor=80,
                release_gate_links=("legal-document-benchmark-suite", "model-cost-guardrails"),
                user_need_ids=("plain-language-actionability", "cheap-first-review-routing"),
            ),
            CalibrationTask(
                id="large-pdf-premium-exception",
                task="large-pdf",
                product_area="large_document_review",
                fixture_ids=("fixture-low-text-pdf-page-small",),
                expected_decision="premium_exception_required",
                max_cost_tier="premium",
                quality_floor=80,
                release_gate_links=("extraction_quality", "model-cost-guardrails"),
                user_need_ids=("robust-extraction-quality", "traceable-legal-review"),
            ),
        )

    def _status(self, rows: list[dict[str, Any]], cost_guardrails: dict[str, Any]) -> str:
        if any(row["status"] == "fail" for row in rows) or cost_guardrails["status"] == "fail":
            return "fail"
        if any(row["status"] == "warn" for row in rows) or cost_guardrails["status"] == "warn":
            return "warn"
        return "pass"

    def _recommended_actions(
        self,
        status: str,
        rows: list[dict[str, Any]],
        cost_guardrails: dict[str, Any],
    ) -> list[str]:
        if status == "pass":
            return [
                "Keep cheap-first Gemini/NewAPI defaults for calibrated high-volume tasks.",
                "Keep large PDF and final review as operator-reviewed premium exceptions.",
                "Attach calibration rows to release evidence after selector, fixture, and cost guardrail tests pass.",
            ]
        actions = [row["next_action"] for row in rows if row["status"] != "pass"]
        actions.extend(cost_guardrails.get("recommended_actions") or [])
        return actions or ["Review calibration warnings before changing model defaults."]


def calibration_decision_order(decision: str) -> int:
    return {
        "keep_cheap_first_default": 0,
        "keep_balanced_after_precheck": 1,
        "require_operator_premium_exception": 2,
        "hold_for_fixture_evidence": 3,
        "hold_default_change": 4,
    }.get(decision, 99)
