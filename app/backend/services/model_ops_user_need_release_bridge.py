from __future__ import annotations

from typing import Any

from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService
from services.user_need_gemini_route_coverage import UserNeedGeminiRouteCoverageService
from services.user_need_implementation_priority_queue import UserNeedImplementationPriorityQueueService


class ModelOpsUserNeedReleaseBridgeService:
    """Bridge user-need evidence into cheap-first release decisions."""

    def __init__(
        self,
        *,
        benchmark_service: UserNeedBenchmarkCoverageService | None = None,
        route_service: UserNeedGeminiRouteCoverageService | None = None,
        queue_service: UserNeedImplementationPriorityQueueService | None = None,
    ) -> None:
        self.benchmark_service = benchmark_service or UserNeedBenchmarkCoverageService()
        self.route_service = route_service or UserNeedGeminiRouteCoverageService()
        self.queue_service = queue_service or UserNeedImplementationPriorityQueueService()

    def build_bridge(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        benchmark_coverage = (
            data.get("user_need_benchmark_coverage")
            if isinstance(data.get("user_need_benchmark_coverage"), dict)
            else self.benchmark_service.build_coverage()
        )
        shared_signals = {
            **data,
            "user_need_benchmark_coverage": benchmark_coverage,
        }
        route_coverage = (
            data.get("user_need_gemini_route_coverage")
            if isinstance(data.get("user_need_gemini_route_coverage"), dict)
            else self.route_service.build_coverage(shared_signals)
        )
        implementation_queue = (
            data.get("user_need_implementation_priority_queue")
            if isinstance(data.get("user_need_implementation_priority_queue"), dict)
            else self.queue_service.build_queue(shared_signals)
        )

        implementation_by_need = _row_by_need(implementation_queue.get("queue_items"))
        route_by_need = _row_by_need(route_coverage.get("coverage_rows"))
        rows = [
            self._bridge_row(route_row, implementation_by_need.get(str(route_row.get("need_id")), {}))
            for route_row in _safe_list(route_coverage.get("coverage_rows"))
            if isinstance(route_row, dict)
        ]
        rows = sorted(rows, key=lambda row: (-row["release_priority_score"], row["need_id"]))
        blocked_rows = [row for row in rows if row["release_bridge_status"] == "blocked"]
        review_rows = [row for row in rows if row["release_bridge_status"] == "review_required"]
        ready_rows = [row for row in rows if row["release_bridge_status"] == "ready"]
        high_priority_rows = [row for row in rows if row["priority_band"] == "high"]
        implementation_blocked_rows = [
            row for row in rows if row["implementation_action_status"] == "blocked"
        ]
        public_benchmark_review_rows = [
            row for row in rows if "public_benchmark_license_review_required" in row["review_reason_codes"]
        ]
        premium_exception_rows = [
            row for row in rows if "premium_exception_review_required" in row["review_reason_codes"]
        ]
        status = "blocked" if blocked_rows else ("review_required" if review_rows else "ready")

        return {
            "id": "modelops-user-need-release-bridge",
            "title": "ModelOps user-need release bridge",
            "status": status,
            "method": {
                "type": "modelops-user-need-release-bridge",
                "notes": [
                    "Joins user-need implementation queue items with Gemini cheap-first route coverage rows before default-change review.",
                    "High-priority user needs block default changes only when implementation evidence is blocked or route coverage is blocked or unmapped.",
                    "Medium or low priority blockers, public benchmark license review, premium exceptions, and partial coverage remain maintainer-review signals.",
                    "This bridge does not consume cheap_first_release_decision, so the release decision can safely consume this bridge without a cycle.",
                ],
            },
            "summary": {
                "need_count": len(rows),
                "high_priority_need_count": len(high_priority_rows),
                "ready_need_count": len(ready_rows),
                "review_required_need_count": len(review_rows),
                "blocked_need_count": len(blocked_rows),
                "implementation_blocked_count": len(implementation_blocked_rows),
                "high_priority_implementation_blocked_count": sum(
                    1 for row in implementation_blocked_rows if row["priority_band"] == "high"
                ),
                "route_unmapped_need_count": sum(
                    1
                    for row in rows
                    if row["route_coverage_status"] == "unmapped"
                    or "no_gemini_route_task_mapped" in row["route_blocker_codes"]
                ),
                "high_priority_route_blocked_count": sum(
                    1
                    for row in high_priority_rows
                    if row["route_coverage_status"] in {"blocked", "unmapped"}
                    or "high_priority_route_unmapped" in row["route_blocker_codes"]
                ),
                "high_priority_route_protected_count": _safe_int(
                    _safe_dict(route_coverage.get("summary")).get("high_priority_route_protected_count")
                ),
                "public_benchmark_review_need_count": len(public_benchmark_review_rows),
                "premium_exception_review_need_count": len(premium_exception_rows),
                "default_change_blocked_need_count": len(blocked_rows),
                "default_change_review_need_count": len(review_rows),
                "source_user_need_benchmark_status": str(benchmark_coverage.get("status") or "missing"),
                "source_user_need_route_status": str(route_coverage.get("status") or "missing"),
                "source_implementation_queue_status": str(implementation_queue.get("status") or "missing"),
                "default_change_allowed": not blocked_rows,
                "maintainer_review_required": bool(review_rows),
                "configuration_written": False,
                "traffic_shifted": False,
                "network_called": False,
                "raw_text_returned": False,
            },
            "bridge_rows": rows,
            "need_rows": rows,
            "blocking_check_ids": [row["id"] for row in blocked_rows],
            "warning_check_ids": [row["id"] for row in review_rows],
            "blocked_need_ids": [row["need_id"] for row in blocked_rows],
            "review_need_ids": [row["need_id"] for row in review_rows],
            "ready_need_ids": [row["need_id"] for row in ready_rows],
            "source_summaries": {
                "user_need_benchmark_coverage": _safe_dict(benchmark_coverage.get("summary")),
                "user_need_gemini_route_coverage": _safe_dict(route_coverage.get("summary")),
                "user_need_implementation_priority_queue": _safe_dict(implementation_queue.get("summary")),
            },
            "bridge_policy": {
                "high_priority_user_need_policy": "High-priority user needs with blocked implementation evidence or blocked/unmapped Gemini route coverage block default changes.",
                "review_policy": "Public benchmark license, premium exception, route-hint calibration, partial coverage, and medium or low priority blockers require maintainer review.",
                "ready_policy": "Ready rows support current cheap-first defaults but do not change production configuration.",
                "blocks_on_high_priority_implementation_blocker": True,
                "blocks_on_high_priority_route_unmapped": True,
                "blocks_on_public_benchmark_license_review": False,
                "blocks_on_premium_exception_review": False,
                "blocks_on_medium_priority_implementation_blocker": False,
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows),
            "source_boundaries": {
                "benchmark_coverage_endpoint": "/api/v1/maintenance/user-needs/benchmark-coverage",
                "gemini_route_coverage_endpoint": "/api/v1/maintenance/user-needs/gemini-route-coverage",
                "implementation_queue_endpoint": "/api/v1/maintenance/user-needs/implementation-priority-queue",
                "model_ops_endpoint": "/api/v1/aihub/models/user-need-release-bridge",
                "uses_public_benchmark_metadata": True,
                "imports_public_benchmark_samples": False,
                "uses_raw_user_feedback": False,
                "uses_raw_legal_text": False,
                "uses_model_outputs": False,
                "uses_credentials": False,
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
                "traffic_shifted": False,
            },
            "claim_boundary": {
                "claims_24h_completion": False,
                "claims_100_update_completion": False,
                "claims_public_benchmark_scores": False,
                "claims_live_gateway_execution": False,
                "claims_production_quality": False,
                "claims_default_route_changed": False,
                "allowed_claim": "The repository maps user needs to metadata-only cheap-first release review gates.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_user_need_release_bridge.py tests/test_user_need_implementation_priority_queue.py tests/test_user_need_gemini_route_coverage.py -q",
                "python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _bridge_row(self, route_row: dict[str, Any], implementation_item: dict[str, Any]) -> dict[str, Any]:
        priority_band = str(route_row.get("priority_band") or implementation_item.get("priority_band") or "unknown")
        implementation_status = str(implementation_item.get("action_status") or "unmapped")
        route_status = str(route_row.get("route_coverage_status") or "unmapped")
        implementation_blockers = _safe_strings(implementation_item.get("blocker_codes"))
        route_blockers = _safe_strings(route_row.get("blocked_reason_codes"))
        review_reasons = _dedupe(
            _safe_strings(implementation_item.get("review_reason_codes"))
            + _safe_strings(route_row.get("review_reason_codes"))
        )
        bridge_status = self._bridge_status(
            priority_band,
            implementation_status,
            route_status,
            implementation_blockers,
            route_blockers,
            review_reasons,
        )
        release_effect = (
            "blocks_default_changes"
            if bridge_status == "blocked"
            else "requires_maintainer_review"
            if bridge_status == "review_required"
            else "supports_current_defaults"
        )
        return {
            "id": f"modelops-user-need-release-{route_row.get('need_id')}",
            "need_id": str(route_row.get("need_id") or implementation_item.get("need_id") or "unknown"),
            "title": str(route_row.get("title") or implementation_item.get("title") or "Untitled user need"),
            "category": str(route_row.get("category") or implementation_item.get("category") or "unknown"),
            "priority_band": priority_band,
            "priority_score": _safe_int(route_row.get("priority_score") or implementation_item.get("user_need_priority_score")),
            "release_priority_score": self._release_priority_score(
                priority_band,
                bridge_status,
                review_reasons,
                implementation_blockers,
                route_blockers,
            ),
            "benchmark_coverage_status": str(route_row.get("benchmark_coverage_status") or "unknown"),
            "implementation_action_status": implementation_status,
            "implementation_status": implementation_status,
            "route_coverage_status": route_status,
            "release_bridge_status": bridge_status,
            "release_status": bridge_status,
            "release_decision_effect": release_effect,
            "default_allowed_without_review": bool(route_row.get("default_allowed_without_review"))
            and bridge_status == "ready",
            "high_frequency_route_ready": bool(route_row.get("high_frequency_route_ready")),
            "linked_route_tasks": _safe_strings(route_row.get("linked_route_tasks")),
            "linked_default_models": _safe_strings(route_row.get("linked_default_models")),
            "linked_release_gates": _dedupe(
                _safe_strings(route_row.get("release_gate_links"))
                + _safe_strings(implementation_item.get("release_gate_links"))
            ),
            "linked_release_gate_links": _dedupe(
                _safe_strings(route_row.get("release_gate_links"))
                + _safe_strings(implementation_item.get("release_gate_links"))
            ),
            "implementation_blocker_codes": implementation_blockers,
            "route_blocker_codes": route_blockers,
            "blocked_reason_codes": _dedupe(implementation_blockers + route_blockers),
            "review_reason_codes": review_reasons,
            "next_action": self._next_action(bridge_status, implementation_item, route_row),
        }

    def _bridge_status(
        self,
        priority_band: str,
        implementation_status: str,
        route_status: str,
        implementation_blockers: list[str],
        route_blockers: list[str],
        review_reasons: list[str],
    ) -> str:
        high_priority = priority_band == "high"
        route_blocked = route_status in {"blocked", "unmapped"} or bool(route_blockers)
        if high_priority and (implementation_status == "blocked" or route_blocked):
            return "blocked"
        if implementation_status == "blocked" or route_blocked:
            return "review_required"
        if implementation_status == "review_required" or route_status == "review_required" or review_reasons:
            return "review_required"
        return "ready"

    def _release_priority_score(
        self,
        priority_band: str,
        bridge_status: str,
        review_reasons: list[str],
        implementation_blockers: list[str],
        route_blockers: list[str],
    ) -> int:
        score = 75 if priority_band == "high" else 50 if priority_band == "medium" else 25
        if bridge_status == "blocked":
            score += 25
        elif bridge_status == "review_required":
            score += 12
        score += min(15, 5 * len(implementation_blockers + route_blockers))
        score += min(10, 2 * len(review_reasons))
        return max(0, min(100, score))

    def _next_action(
        self,
        bridge_status: str,
        implementation_item: dict[str, Any],
        route_row: dict[str, Any],
    ) -> str:
        if bridge_status == "blocked":
            return "Clear high-priority implementation or route blockers before any cheap-first default change."
        implementation_actions = _safe_strings(implementation_item.get("next_actions"))
        route_actions = _safe_strings(route_row.get("next_actions"))
        actions = _dedupe(implementation_actions + route_actions)
        if actions:
            return actions[0]
        if bridge_status == "review_required":
            return "Complete maintainer review for benchmark license, premium exception, route hint, or partial coverage evidence."
        return "Keep attached to release evidence and rerun bridge checks before changing defaults."

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocked_rows:
            return [
                "Do not promote cheap-first defaults until blocked high-priority user needs pass: "
                + ", ".join(row["need_id"] for row in blocked_rows[:5])
                + ".",
                "Fix implementation blockers or attach Gemini route coverage before default-change review.",
            ]
        if review_rows:
            return [
                "Keep current cheap-first defaults and complete maintainer review for user-need release evidence.",
                "Resolve public benchmark license, premium exception, route hint, and partial coverage review items before release claims.",
            ]
        return ["All user-need release bridge rows support current cheap-first defaults."]


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _row_by_need(rows: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in _safe_list(rows):
        if not isinstance(row, dict):
            continue
        need_id = str(row.get("need_id") or "").strip()
        if need_id:
            result[need_id] = row
    return result


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
