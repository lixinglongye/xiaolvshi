from __future__ import annotations

import re
from typing import Any

from services.model_ops_user_need_release_bridge import ModelOpsUserNeedReleaseBridgeService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService
from services.user_need_gemini_route_coverage import UserNeedGeminiRouteCoverageService
from services.user_need_implementation_priority_queue import UserNeedImplementationPriorityQueueService


SENSITIVE_TEXT_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key)",
    re.IGNORECASE,
)


class ModelOpsUserNeedCheapFirstHandoffService:
    """Build reviewer handoff evidence for user-needs and cheap-first routing."""

    def __init__(
        self,
        *,
        benchmark_service: UserNeedBenchmarkCoverageService | None = None,
        route_service: UserNeedGeminiRouteCoverageService | None = None,
        queue_service: UserNeedImplementationPriorityQueueService | None = None,
        bridge_service: ModelOpsUserNeedReleaseBridgeService | None = None,
    ) -> None:
        self.benchmark_service = benchmark_service or UserNeedBenchmarkCoverageService()
        self.route_service = route_service or UserNeedGeminiRouteCoverageService()
        self.queue_service = queue_service or UserNeedImplementationPriorityQueueService()
        self.bridge_service = bridge_service or ModelOpsUserNeedReleaseBridgeService()

    def build_handoff(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
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
        implementation_queue = (
            data.get("user_need_implementation_priority_queue")
            if isinstance(data.get("user_need_implementation_priority_queue"), dict)
            else self.queue_service.build_queue(shared_signals)
        )
        route_coverage = (
            data.get("user_need_gemini_route_coverage")
            if isinstance(data.get("user_need_gemini_route_coverage"), dict)
            else self.route_service.build_coverage(shared_signals)
        )
        release_bridge = (
            data.get("user_need_release_bridge")
            if isinstance(data.get("user_need_release_bridge"), dict)
            else self.bridge_service.build_bridge(
                {
                    **shared_signals,
                    "user_need_implementation_priority_queue": implementation_queue,
                    "user_need_gemini_route_coverage": route_coverage,
                }
            )
        )

        rows = [
            self._handoff_row(row)
            for row in _safe_list(release_bridge.get("bridge_rows") or release_bridge.get("need_rows"))
            if isinstance(row, dict)
        ]
        rows = sorted(rows, key=lambda row: (-row["review_priority_score"], row["need_id"]))
        blocked_rows = [row for row in rows if row["handoff_status"] == "blocked"]
        review_rows = [row for row in rows if row["handoff_status"] == "review_required"]
        ready_rows = [row for row in rows if row["handoff_status"] == "ready"]
        high_priority_rows = [row for row in rows if row["priority_band"] == "high"]
        protected_rows = [row for row in rows if row["cheap_first_route_protected"]]
        protected_high_priority_rows = [
            row for row in high_priority_rows if row["cheap_first_route_protected"] and not row["blocked_reason_codes"]
        ]
        status = "blocked" if blocked_rows else ("review_required" if review_rows else "ready")

        return {
            "id": "modelops-user-need-cheap-first-handoff",
            "title": "ModelOps user-need cheap-first handoff",
            "status": status,
            "method": {
                "type": "modelops-user-need-cheap-first-handoff",
                "notes": [
                    "Aggregates user-need implementation queue, Gemini route coverage, and user-need release bridge rows for maintainer handoff.",
                    "Ranks review rows by release priority and separates default-change blockers from maintainer-review-only items.",
                    "Uses metadata-only local evidence; it never calls model providers, gateways, or public benchmark datasets.",
                ],
            },
            "summary": {
                "need_count": len(rows),
                "high_priority_need_count": len(high_priority_rows),
                "ready_need_count": len(ready_rows),
                "review_required_need_count": len(review_rows),
                "blocked_need_count": len(blocked_rows),
                "cheap_first_route_protected_need_count": len(protected_rows),
                "high_priority_route_protected_count": len(protected_high_priority_rows),
                "default_change_allowed": not blocked_rows
                and bool(_safe_dict(release_bridge.get("summary")).get("default_change_allowed", True)),
                "default_change_blocked": bool(blocked_rows),
                "maintainer_review_required": bool(review_rows)
                or bool(_safe_dict(release_bridge.get("summary")).get("maintainer_review_required")),
                "implementation_queue_status": str(implementation_queue.get("status") or "missing"),
                "gemini_route_coverage_status": str(route_coverage.get("status") or "missing"),
                "release_bridge_status": str(release_bridge.get("status") or "missing"),
                "source_benchmark_coverage_status": str(benchmark_coverage.get("status") or "missing"),
                "evidence_section_count": 4,
                "validation_command_count": 3,
                "model_calls": "not_required",
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "raw_text_returned": False,
            },
            "handoff_rows": rows,
            "blocking_check_ids": [row["id"] for row in blocked_rows],
            "warning_check_ids": [row["id"] for row in review_rows],
            "blocked_need_ids": [row["need_id"] for row in blocked_rows],
            "review_need_ids": [row["need_id"] for row in review_rows],
            "ready_need_ids": [row["need_id"] for row in ready_rows],
            "handoff_sections": [
                self._section(
                    "user-need-benchmark-coverage",
                    "User-need benchmark coverage",
                    "/api/v1/maintenance/user-needs/benchmark-coverage",
                    benchmark_coverage,
                    ("need_count", "high_priority_need_count", "coverage_gap_count"),
                ),
                self._section(
                    "user-need-implementation-priority-queue",
                    "User-need implementation priority queue",
                    "/api/v1/maintenance/user-needs/implementation-priority-queue",
                    implementation_queue,
                    ("queue_item_count", "blocked_action_count", "review_required_action_count"),
                ),
                self._section(
                    "user-need-gemini-route-coverage",
                    "User-need Gemini route coverage",
                    "/api/v1/maintenance/user-needs/gemini-route-coverage",
                    route_coverage,
                    ("need_count", "high_priority_route_protected_count", "premium_exception_need_count"),
                ),
                self._section(
                    "modelops-user-need-release-bridge",
                    "ModelOps user-need release bridge",
                    "/api/v1/aihub/models/user-need-release-bridge",
                    release_bridge,
                    ("need_count", "default_change_blocked_need_count", "default_change_review_need_count"),
                ),
            ],
            "source_summaries": {
                "user_need_benchmark_coverage": _safe_dict(benchmark_coverage.get("summary")),
                "user_need_implementation_priority_queue": _safe_dict(implementation_queue.get("summary")),
                "user_need_gemini_route_coverage": _safe_dict(route_coverage.get("summary")),
                "user_need_release_bridge": _safe_dict(release_bridge.get("summary")),
            },
            "reviewer_handoff": {
                "primary_endpoint": "/api/v1/aihub/models/user-need-cheap-first-handoff",
                "maintenance_endpoint": "/api/v1/maintenance/user-needs/cheap-first-evidence-handoff",
                "default_change_rule": "Blocked handoff rows prevent cheap-first default promotion; review rows require maintainer signoff.",
                "cheap_first_policy": "High-frequency needs should stay on cheap-first Gemini routes unless the release bridge marks a reviewed exception.",
                "next_review_ids": [row["id"] for row in blocked_rows[:5] + review_rows[:5]],
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows),
            "source_boundaries": {
                "benchmark_coverage_endpoint": "/api/v1/maintenance/user-needs/benchmark-coverage",
                "implementation_queue_endpoint": "/api/v1/maintenance/user-needs/implementation-priority-queue",
                "gemini_route_coverage_endpoint": "/api/v1/maintenance/user-needs/gemini-route-coverage",
                "release_bridge_endpoint": "/api/v1/aihub/models/user-need-release-bridge",
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
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_raw_model_output": False,
                "returns_user_feedback_text": False,
                "returns_payloads": False,
                "returns_headers": False,
                "returns_credentials": False,
                "returns_emails": False,
                "returns_user_identifiers": False,
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
                "allowed_claim": "The repository provides metadata-only user-need handoff evidence for cheap-first route review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_user_need_cheap_first_handoff.py tests/test_model_ops_user_need_release_bridge.py -q",
                "python -m pytest tests/test_user_need_implementation_priority_queue.py tests/test_user_need_gemini_route_coverage.py tests/test_user_need_benchmark_coverage.py -q",
                "python -m pytest tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py -q",
            ],
        }

    def _handoff_row(self, row: dict[str, Any]) -> dict[str, Any]:
        status = str(row.get("release_bridge_status") or row.get("release_status") or "review_required")
        implementation_blockers = _safe_strings(row.get("implementation_blocker_codes"))
        route_blockers = _safe_strings(row.get("route_blocker_codes"))
        review_reasons = _safe_strings(row.get("review_reason_codes"))
        linked_models = _safe_strings(row.get("linked_default_models"))
        linked_release_gates = _dedupe(
            _safe_strings(row.get("linked_release_gates") or row.get("linked_release_gate_links"))
            + ["modelops-user-need-release-bridge", "modelops-user-need-cheap-first-handoff"]
        )
        cheap_first_protected = bool(row.get("high_frequency_route_ready")) and any(
            "flash-lite" in model.lower() or "cheap" in model.lower() for model in linked_models
        )
        blocked_codes = _dedupe(implementation_blockers + route_blockers)
        release_effect = str(row.get("release_decision_effect") or "requires_maintainer_review")
        need_id = _safe_public_text(row.get("need_id"), fallback="unknown")
        return {
            "id": f"modelops-user-need-cheap-first-handoff-{need_id}",
            "need_id": need_id,
            "title": _safe_public_text(row.get("title"), fallback="Untitled user need"),
            "category": _safe_public_text(row.get("category"), fallback="unknown"),
            "priority_band": _safe_public_text(row.get("priority_band"), fallback="unknown"),
            "priority_score": _safe_int(row.get("priority_score")),
            "review_priority_score": _safe_int(row.get("release_priority_score")),
            "handoff_status": status,
            "release_decision_effect": release_effect,
            "default_allowed_without_review": bool(row.get("default_allowed_without_review")) and status == "ready",
            "cheap_first_route_protected": cheap_first_protected,
            "high_frequency_route_ready": bool(row.get("high_frequency_route_ready")),
            "implementation_action_status": _safe_public_text(row.get("implementation_action_status"), fallback="unknown"),
            "route_coverage_status": _safe_public_text(row.get("route_coverage_status"), fallback="unknown"),
            "linked_route_tasks": _safe_strings(row.get("linked_route_tasks")),
            "linked_default_models": linked_models,
            "linked_release_gates": linked_release_gates,
            "implementation_blocker_codes": implementation_blockers,
            "route_blocker_codes": route_blockers,
            "blocked_reason_codes": blocked_codes,
            "review_reason_codes": review_reasons,
            "reviewer_action": self._reviewer_action(status, release_effect, blocked_codes, review_reasons, row),
            "evidence_endpoints": [
                "/api/v1/maintenance/user-needs/implementation-priority-queue",
                "/api/v1/maintenance/user-needs/gemini-route-coverage",
                "/api/v1/aihub/models/user-need-release-bridge",
            ],
        }

    def _section(
        self,
        section_id: str,
        title: str,
        endpoint: str,
        payload: dict[str, Any],
        summary_keys: tuple[str, ...],
    ) -> dict[str, Any]:
        summary = _safe_dict(payload.get("summary"))
        return {
            "id": section_id,
            "title": title,
            "status": _safe_public_text(payload.get("status"), fallback="missing"),
            "endpoint": endpoint,
            "summary": {key: summary.get(key, 0) for key in summary_keys},
            "blocking_ids": _safe_strings(payload.get("blocking_check_ids") or payload.get("blocked_need_ids")),
            "warning_ids": _safe_strings(payload.get("warning_check_ids") or payload.get("review_need_ids")),
        }

    def _reviewer_action(
        self,
        status: str,
        release_effect: str,
        blocked_codes: list[str],
        review_reasons: list[str],
        row: dict[str, Any],
    ) -> str:
        if status == "blocked" or release_effect == "blocks_default_changes":
            return "Clear blocking implementation or route evidence before cheap-first default promotion."
        if "public_benchmark_license_review_required" in review_reasons:
            return "Finish metadata-only public benchmark license review before using this need in release claims."
        if "premium_exception_review_required" in review_reasons:
            return "Confirm the premium exception stays reviewed and does not become a high-frequency default."
        if blocked_codes:
            return "Treat blockers as maintainer-review items unless this need is promoted to high priority."
        next_action = str(row.get("next_action") or "").strip()
        if next_action:
            return next_action
        if status == "review_required":
            return "Complete maintainer review for the user-need evidence packet."
        return "Keep this need attached to cheap-first route and release evidence."

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocked_rows:
            return [
                "Do not promote cheap-first defaults until handoff blockers are cleared: "
                + ", ".join(row["need_id"] for row in blocked_rows[:5])
                + ".",
                "Attach implementation, benchmark, and Gemini route evidence before default-change review.",
            ]
        if review_rows:
            return [
                "Keep current cheap-first defaults and complete maintainer review for user-need handoff rows.",
                "Prioritize public benchmark license, premium exception, route-hint, and partial-coverage review items.",
            ]
        return ["All user-need handoff rows are ready for current cheap-first default review."]


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        str(item)
        for item in value
        if str(item).strip() and not SENSITIVE_TEXT_PATTERN.search(str(item))
    ]


def _safe_public_text(value: Any, *, fallback: str) -> str:
    text = str(value or fallback).strip()
    if not text or SENSITIVE_TEXT_PATTERN.search(text):
        return fallback
    return text


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


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
