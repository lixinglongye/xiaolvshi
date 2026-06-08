from __future__ import annotations

from typing import Any

from services.gemini_newapi_cheap_first_calibration import GeminiNewapiCheapFirstCalibrationService
from services.model_ops_gemini_cheap_first_route_preflight import ModelOpsGeminiCheapFirstRoutePreflightService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService


TASK_NORMALIZATION = {
    "large-pdf": "pdf",
    "final-review": "review",
}

NEED_ROUTE_HINTS: dict[str, tuple[str, ...]] = {
    "traceable-legal-review": ("review", "pdf"),
    "cheap-first-review-routing": ("fast", "routing", "classification", "ocr", "review", "document-generation"),
    "privacy-safe-upload": ("fast", "routing", "classification"),
    "robust-extraction-quality": ("classification", "ocr", "pdf"),
    "prompt-injection-resilience": ("fast", "routing", "classification"),
    "plain-language-actionability": ("review", "document-generation"),
    "feedback-to-roadmap-loop": ("fast", "classification"),
}


class UserNeedGeminiRouteCoverageService:
    """Join user needs to Gemini cheap-first route evidence without provider calls."""

    def __init__(
        self,
        *,
        coverage_service: UserNeedBenchmarkCoverageService | None = None,
        calibration_service: GeminiNewapiCheapFirstCalibrationService | None = None,
        route_preflight_service: ModelOpsGeminiCheapFirstRoutePreflightService | None = None,
    ) -> None:
        self.coverage_service = coverage_service or UserNeedBenchmarkCoverageService()
        self.calibration_service = calibration_service or GeminiNewapiCheapFirstCalibrationService()
        self.route_preflight_service = route_preflight_service or ModelOpsGeminiCheapFirstRoutePreflightService()

    def build_coverage(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        coverage = (
            data.get("user_need_benchmark_coverage")
            if isinstance(data.get("user_need_benchmark_coverage"), dict)
            else self.coverage_service.build_coverage()
        )
        calibration = (
            data.get("cheap_first_calibration")
            if isinstance(data.get("cheap_first_calibration"), dict)
            else self.calibration_service.build_calibration()
        )
        route_preflight = (
            data.get("gemini_cheap_first_route_preflight")
            if isinstance(data.get("gemini_cheap_first_route_preflight"), dict)
            else self.route_preflight_service.build_preflight()
        )
        route_by_task = {str(row["task"]): row for row in route_preflight["route_task_rows"]}
        calibration_by_id = {str(row["id"]): row for row in calibration.get("calibration_rows", [])}
        task_by_calibration_id = {
            str(task["id"]): str(task.get("task") or "")
            for task in calibration.get("calibration_tasks", [])
        }

        rows = [
            self._coverage_row(row, route_by_task, calibration_by_id, task_by_calibration_id)
            for row in coverage["coverage_rows"]
        ]
        high_priority_rows = [row for row in rows if row["priority_band"] == "high"]
        ready_rows = [row for row in rows if row["route_coverage_status"] == "ready"]
        review_rows = [row for row in rows if row["route_coverage_status"] == "review_required"]
        blocked_rows = [row for row in rows if row["route_coverage_status"] == "blocked"]
        unmapped_rows = [row for row in rows if row["route_coverage_status"] == "unmapped"]
        protected_high_priority_rows = [
            row for row in high_priority_rows if row["high_frequency_route_ready"] and not row["blocked_reason_codes"]
        ]
        status = "blocked" if blocked_rows else ("review_required" if review_rows or unmapped_rows else "ready")

        return {
            "id": "user-need-gemini-route-coverage",
            "title": "User need Gemini route coverage",
            "status": status,
            "method": {
                "type": "user-need-to-gemini-route-coverage",
                "notes": [
                    "Maps user-need IDs to cheap-first calibration tasks and Gemini route preflight rows.",
                    "Uses local benchmark coverage metadata, route preflight metadata, and calibration summaries only.",
                    "Shows where Flash-Lite protects high-frequency product needs and where premium or public-benchmark review is still required.",
                ],
            },
            "summary": {
                "need_count": len(rows),
                "high_priority_need_count": len(high_priority_rows),
                "ready_need_count": len(ready_rows),
                "review_required_need_count": len(review_rows),
                "blocked_need_count": len(blocked_rows),
                "unmapped_need_count": len(unmapped_rows),
                "high_priority_route_protected_count": len(protected_high_priority_rows),
                "cheap_first_route_need_count": sum(1 for row in rows if row["cheap_first_route_count"] > 0),
                "balanced_route_need_count": sum(1 for row in rows if row["balanced_route_count"] > 0),
                "premium_exception_need_count": sum(1 for row in rows if row["premium_exception_route_count"] > 0),
                "source_user_need_coverage_status": coverage["status"],
                "source_route_preflight_status": route_preflight["status"],
                "source_calibration_status": calibration["status"],
                "official_source_count": route_preflight["summary"]["official_source_count"],
                "route_task_count": route_preflight["summary"]["route_task_count"],
                "model_calls": "not_required",
                "network_access": "disabled",
                "configuration_written": False,
                "raw_text_returned": False,
            },
            "coverage_rows": rows,
            "blocked_need_ids": [row["need_id"] for row in blocked_rows],
            "review_need_ids": [row["need_id"] for row in review_rows],
            "unmapped_need_ids": [row["need_id"] for row in unmapped_rows],
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows, unmapped_rows),
            "source_summaries": {
                "user_need_benchmark_coverage": coverage["summary"],
                "gemini_route_preflight": route_preflight["summary"],
                "cheap_first_calibration": calibration["summary"],
            },
            "source_boundaries": {
                "coverage_endpoint": "/api/v1/maintenance/user-needs/benchmark-coverage",
                "route_preflight_endpoint": "/api/v1/aihub/models/gemini-cheap-first-route-preflight",
                "official_source_urls": [row["url"] for row in route_preflight["official_source_rows"]],
                "uses_public_benchmark_metadata": True,
                "imports_public_benchmark_samples": False,
                "uses_route_preflight_metadata": True,
                "changes_default_routes": False,
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_raw_benchmark_samples": False,
                "returns_public_benchmark_text": False,
                "returns_fixture_snippets": False,
                "returns_calibration_payloads": False,
                "returns_route_payloads": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_raw_model_output": False,
                "returns_user_feedback_text": False,
                "returns_credentials": False,
                "returns_emails": False,
                "model_calls": False,
                "gateway_calls": False,
                "network_access": False,
                "configuration_written": False,
            },
            "claim_boundary": {
                "claims_24h_completion": False,
                "claims_public_benchmark_scores": False,
                "claims_live_gateway_execution": False,
                "claims_production_quality": False,
                "claims_default_route_changed": False,
                "allowed_claim": "The repository maps user needs to metadata-only Gemini cheap-first route review evidence.",
            },
            "validation_commands": [
                "python -m pytest tests/test_user_need_gemini_route_coverage.py tests/test_user_need_benchmark_coverage.py -q",
                "python -m pytest tests/test_model_ops_gemini_cheap_first_route_preflight.py tests/test_gemini_newapi_cheap_first_calibration.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _coverage_row(
        self,
        row: dict[str, Any],
        route_by_task: dict[str, dict[str, Any]],
        calibration_by_id: dict[str, dict[str, Any]],
        task_by_calibration_id: dict[str, str],
    ) -> dict[str, Any]:
        calibration_task_ids = [str(item) for item in row.get("linked_calibration_task_ids", [])]
        linked_tasks = sorted(
            {
                _normalize_task(task_by_calibration_id.get(task_id, ""))
                for task_id in calibration_task_ids
                if task_by_calibration_id.get(task_id)
            }
        )
        task_source = "cheap_first_calibration"
        if not linked_tasks:
            linked_tasks = sorted(NEED_ROUTE_HINTS.get(str(row["need_id"]), ()))
            task_source = "user_need_route_hint" if linked_tasks else "unmapped"
        linked_routes = [route_by_task[task] for task in linked_tasks if task in route_by_task]
        route_models = sorted({str(route.get("canonical_model") or route.get("default_model")) for route in linked_routes})
        route_modes = sorted({str(route.get("route_mode") or "unknown") for route in linked_routes})
        cost_tiers = sorted({str(route.get("cost_tier") or "unknown") for route in linked_routes})
        decisions = {
            task_id: str(calibration_by_id.get(task_id, {}).get("calibration_decision") or "unknown")
            for task_id in calibration_task_ids
        }
        blocked_reasons = self._blocked_reasons(row, linked_tasks, linked_routes)
        review_reasons = self._review_reasons(row, linked_tasks, linked_routes, decisions, task_source)
        status = self._status(blocked_reasons, review_reasons, linked_tasks)
        high_frequency_ready = any(
            bool(route.get("high_frequency_task")) and bool(route.get("cheap_first_aligned"))
            for route in linked_routes
        )
        return {
            "id": f"user-need-gemini-route-{row['need_id']}",
            "need_id": row["need_id"],
            "title": row["title"],
            "category": row["category"],
            "priority_band": row["priority_band"],
            "priority_score": row["priority_score"],
            "benchmark_coverage_status": row["coverage_status"],
            "public_benchmark_status": row["public_benchmark_status"],
            "calibration_status": row["calibration_status"],
            "route_coverage_status": status,
            "linked_calibration_task_ids": calibration_task_ids,
            "linked_route_tasks": linked_tasks,
            "route_task_source": task_source,
            "linked_default_models": route_models,
            "route_modes": route_modes,
            "cost_tiers": cost_tiers,
            "cheap_first_route_count": sum(1 for route in linked_routes if route.get("route_mode") == "cheap_first"),
            "balanced_route_count": sum(
                1 for route in linked_routes if route.get("route_mode") == "cheap_precheck_then_balanced"
            ),
            "premium_exception_route_count": sum(
                1 for route in linked_routes if bool(route.get("premium_exception_required"))
            ),
            "high_frequency_route_ready": high_frequency_ready,
            "default_allowed_without_review": bool(linked_routes)
            and all(bool(route.get("default_allowed_without_review")) for route in linked_routes)
            and not review_reasons
            and not blocked_reasons,
            "calibration_decisions": decisions,
            "blocked_reason_codes": blocked_reasons,
            "review_reason_codes": review_reasons,
            "next_actions": self._next_actions(row, blocked_reasons, review_reasons, linked_tasks),
            "release_gate_links": sorted(set(row.get("linked_release_gates", [])) | {"user-need-gemini-route-coverage"}),
        }

    def _blocked_reasons(
        self,
        row: dict[str, Any],
        linked_tasks: list[str],
        linked_routes: list[dict[str, Any]],
    ) -> list[str]:
        reasons: list[str] = []
        if not linked_tasks:
            reasons.append("no_gemini_route_task_mapped")
        if row.get("priority_band") == "high" and not linked_routes:
            reasons.append("high_priority_route_unmapped")
        if row.get("calibration_status") == "fail":
            reasons.append("cheap_first_calibration_failing")
        if any("unknown_model" in route.get("reason_codes", []) for route in linked_routes):
            reasons.append("unknown_default_model")
        return reasons

    def _review_reasons(
        self,
        row: dict[str, Any],
        linked_tasks: list[str],
        linked_routes: list[dict[str, Any]],
        decisions: dict[str, str],
        task_source: str,
    ) -> list[str]:
        reasons: list[str] = []
        if task_source == "user_need_route_hint":
            reasons.append("route_hint_needs_calibration_evidence")
        if row.get("coverage_status") != "covered":
            reasons.append("benchmark_coverage_not_complete")
        if row.get("public_benchmark_status") == "license_review_required":
            reasons.append("public_benchmark_license_review_required")
        if row.get("calibration_status") == "warn":
            reasons.append("cheap_first_calibration_warning")
        if any(route.get("premium_exception_required") for route in linked_routes):
            reasons.append("premium_exception_review_required")
        if any(not bool(route.get("cheap_first_aligned")) and route.get("high_frequency_task") for route in linked_routes):
            reasons.append("high_frequency_not_cheap_first_aligned")
        if any(decision == "unknown" for decision in decisions.values()):
            reasons.append("calibration_decision_missing")
        if linked_tasks and not linked_routes:
            reasons.append("route_preflight_row_missing")
        return reasons

    def _status(self, blocked: list[str], review: list[str], linked_tasks: list[str]) -> str:
        if blocked:
            return "blocked"
        if not linked_tasks:
            return "unmapped"
        if review:
            return "review_required"
        return "ready"

    def _next_actions(
        self,
        row: dict[str, Any],
        blocked: list[str],
        review: list[str],
        linked_tasks: list[str],
    ) -> list[str]:
        actions: list[str] = []
        if "no_gemini_route_task_mapped" in blocked:
            actions.append(f"Map user need {row['need_id']} to a cheap-first calibration task before route claims.")
        if "benchmark_coverage_not_complete" in review:
            actions.append("Link local benchmark fixtures before treating this need as route-protected.")
        if "public_benchmark_license_review_required" in review:
            actions.append("Keep public benchmark evidence metadata-only until license and attribution review pass.")
        if "premium_exception_review_required" in review:
            actions.append("Keep premium exception routes behind operator review and release evidence.")
        if linked_tasks:
            actions.append("Rerun Gemini route preflight before changing defaults for: " + ", ".join(linked_tasks[:5]) + ".")
        actions.extend(row.get("next_actions", [])[:2])
        return _dedupe(actions)[:4] or ["Keep this need linked to route preflight and release-gate evidence."]

    def _recommended_actions(
        self,
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        unmapped: list[dict[str, Any]],
    ) -> list[str]:
        if blocked:
            return [
                "Do not claim all user needs are protected by Gemini cheap-first routing until blocked mappings are resolved: "
                + ", ".join(row["need_id"] for row in blocked[:6])
                + ".",
                "Add local benchmark links or calibration task mappings before promoting route changes.",
            ]
        if unmapped:
            return [
                "Map unmapped user needs to calibration task ids before broad cheap-first route claims.",
                "Keep unmapped needs out of default-change approval packets.",
            ]
        if review:
            return [
                "Review public benchmark license states, premium exceptions, and partial benchmark coverage before release claims.",
                "Use route preflight and cheap-first calibration together before changing Gemini defaults.",
            ]
        return [
            "All mapped user needs have route evidence; keep official source refresh and UI regression checks attached.",
            "Continue using Flash-Lite for high-frequency needs and reviewed exceptions for premium routes.",
        ]


def _normalize_task(task: str) -> str:
    return TASK_NORMALIZATION.get(task, task)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
