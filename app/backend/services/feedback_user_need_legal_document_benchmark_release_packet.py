from __future__ import annotations

from typing import Any

from services.feedback_lifecycle_policy import FeedbackLifecyclePolicyService
from services.feedback_user_need_legal_document_benchmark_backlog import (
    FeedbackUserNeedLegalDocumentBenchmarkBacklogService,
)
from services.user_need_implementation_priority_queue import UserNeedImplementationPriorityQueueService


HIGH_RISK_SEVERITIES = {"critical", "high"}


class FeedbackUserNeedLegalDocumentBenchmarkReleasePacketService:
    """Gate feedback benchmark backlog rows before customer-visible release claims."""

    def __init__(
        self,
        backlog_service: FeedbackUserNeedLegalDocumentBenchmarkBacklogService | None = None,
        lifecycle_service: FeedbackLifecyclePolicyService | None = None,
        implementation_queue_service: UserNeedImplementationPriorityQueueService | None = None,
    ) -> None:
        self.backlog_service = backlog_service or FeedbackUserNeedLegalDocumentBenchmarkBacklogService()
        self.lifecycle_service = lifecycle_service or FeedbackLifecyclePolicyService()
        self.implementation_queue_service = (
            implementation_queue_service or UserNeedImplementationPriorityQueueService()
        )

    def build_packet(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        backlog = self.backlog_service.build_backlog(self._backlog_payload(payload))
        implementation_queue = self.implementation_queue_service.build_queue(
            self._safe_mapping(payload.get("implementation_queue"))
        )
        implementation_by_need_id = {
            str(item["need_id"]): item
            for item in implementation_queue.get("queue_items", [])
            if isinstance(item, dict) and item.get("need_id")
        }
        observations = self._release_observations(payload.get("release_observations"))

        release_rows = [
            self._release_row(
                backlog_row=row,
                implementation_item=implementation_by_need_id.get(str(row.get("primary_need_id")), {}),
                observation=self._observation_for_row(row, observations),
            )
            for row in backlog.get("backlog_rows", [])
            if isinstance(row, dict)
        ]
        release_rows.sort(
            key=lambda row: (
                row["release_action_rank"],
                -int(row["priority_score"]),
                row["cluster_id"],
            )
        )

        blocked_rows = [row for row in release_rows if row["release_action_status"] == "blocked"]
        review_rows = [row for row in release_rows if row["release_action_status"] == "release_review_required"]
        ready_rows = [row for row in release_rows if row["release_action_status"] == "customer_resolution_ready"]
        high_risk_blocked_rows = [row for row in blocked_rows if row["high_risk"]]
        status = "blocked" if high_risk_blocked_rows else ("review_required" if blocked_rows or review_rows else "ready")

        return {
            "status": status,
            "method": {
                "type": "feedback-user-need-legal-document-benchmark-release-packet",
                "notes": [
                    "Joins feedback benchmark backlog rows to feedback lifecycle checks and user-need implementation queue rows.",
                    "Allows customer-visible resolution only when benchmark evidence, implementation status, validation, and public-note checks pass.",
                    "Returns IDs, counts, statuses, reason codes, and reviewer actions only; raw feedback, customer notes, legal text, prompts, model outputs, payload bodies, and credentials are not returned.",
                ],
            },
            "summary": {
                "release_row_count": len(release_rows),
                "customer_resolution_ready_count": len(ready_rows),
                "release_review_required_count": len(review_rows),
                "blocked_release_count": len(blocked_rows),
                "high_risk_blocked_count": len(high_risk_blocked_rows),
                "source_backlog_status": backlog.get("status"),
                "source_implementation_queue_status": implementation_queue.get("status"),
                "raw_feedback_returned": False,
                "customer_resolution_claimed": False,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "release_rows": release_rows,
            "customer_resolution_ready_cluster_ids": [row["cluster_id"] for row in ready_rows],
            "release_review_required_cluster_ids": [row["cluster_id"] for row in review_rows],
            "blocked_cluster_ids": [row["cluster_id"] for row in blocked_rows],
            "high_risk_blocked_cluster_ids": [row["cluster_id"] for row in high_risk_blocked_rows],
            "source_summaries": {
                "feedback_benchmark_backlog": backlog.get("summary", {}),
                "user_need_implementation_queue": implementation_queue.get("summary", {}),
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows, ready_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_raw_feedback": False,
                "returns_raw_feedback_text": False,
                "returns_customer_notes": False,
                "returns_public_resolution_text": False,
                "returns_pii": False,
                "returns_document_snippets": False,
                "returns_fixture_snippets": False,
                "returns_public_benchmark_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_payload_bodies": False,
                "returns_credentials": False,
                "model_calls": False,
                "network_called": False,
            },
            "claim_boundary": {
                "feedback_resolution_claimed": False,
                "customer_notification_claimed": False,
                "production_quality_claimed": False,
                "public_benchmark_score_claimed": False,
                "client_document_coverage_claimed": False,
                "allowed_claim": (
                    "The repository can review whether privacy-safe feedback benchmark backlog rows have "
                    "enough metadata evidence to enter release validation or customer-visible resolution."
                ),
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_feedback_user_need_legal_document_benchmark_release_packet.py -q",
                "cd app/backend && python -m pytest tests/test_feedback_user_need_legal_document_benchmark_backlog.py tests/test_feedback_lifecycle_policy.py tests/test_user_need_implementation_priority_queue.py -q",
            ],
        }

    def _release_row(
        self,
        *,
        backlog_row: dict[str, Any],
        implementation_item: dict[str, Any],
        observation: dict[str, Any],
    ) -> dict[str, Any]:
        lifecycle = self.lifecycle_service.evaluate_ticket(
            self._lifecycle_source(backlog_row=backlog_row, observation=observation)
        )
        high_risk = str(backlog_row.get("severity") or "low") in HIGH_RISK_SEVERITIES or bool(
            lifecycle.get("high_risk")
        )
        benchmark_status = str(backlog_row.get("benchmark_action_status") or "review_required")
        implementation_status = str(implementation_item.get("action_status") or "review_required")
        lifecycle_blockers = list(lifecycle.get("blocking_check_ids") or [])
        release_action_status = self._release_action_status(
            benchmark_status=benchmark_status,
            legal_document_evidence_status=str(backlog_row.get("legal_document_evidence_status") or "not_run"),
            implementation_status=self._implementation_status(implementation_status, observation),
            lifecycle=lifecycle,
            high_risk=high_risk,
        )
        reason_codes = self._reason_codes(
            backlog_row=backlog_row,
            implementation_item=implementation_item,
            implementation_status=self._implementation_status(implementation_status, observation),
            lifecycle_blockers=lifecycle_blockers,
            release_action_status=release_action_status,
            high_risk=high_risk,
        )

        return {
            "cluster_id": str(backlog_row.get("cluster_id") or "feedback-cluster"),
            "normalized_topic": str(backlog_row.get("normalized_topic") or "general_feedback"),
            "primary_need_id": str(backlog_row.get("primary_need_id") or ""),
            "primary_need_title": str(backlog_row.get("primary_need_title") or backlog_row.get("primary_need_id") or ""),
            "severity": str(backlog_row.get("severity") or "low"),
            "high_risk": high_risk,
            "feedback_count": int(backlog_row.get("feedback_count") or 0),
            "priority_score": int(backlog_row.get("priority_score") or 0),
            "benchmark_action_status": benchmark_status,
            "legal_document_evidence_status": str(backlog_row.get("legal_document_evidence_status") or "not_run"),
            "implementation_action_status": self._implementation_status(implementation_status, observation),
            "lifecycle_current_state": lifecycle.get("current_state"),
            "lifecycle_next_allowed_states": list(lifecycle.get("next_allowed_states") or []),
            "lifecycle_blocking_check_ids": lifecycle_blockers,
            "release_action_status": release_action_status,
            "release_action_rank": self._release_action_rank(release_action_status),
            "customer_resolution_allowed": release_action_status == "customer_resolution_ready",
            "customer_resolution_claimed": False,
            "release_gate_links": self._release_gate_links(backlog_row, observation),
            "linked_document_case_ids": list(backlog_row.get("linked_document_case_ids") or []),
            "suggested_fixture_ids": list(backlog_row.get("suggested_fixture_ids") or []),
            "reason_codes": reason_codes,
            "next_actions": self._next_actions(
                release_action_status=release_action_status,
                backlog_row=backlog_row,
                implementation_item=implementation_item,
                lifecycle=lifecycle,
            ),
        }

    def _release_action_status(
        self,
        *,
        benchmark_status: str,
        legal_document_evidence_status: str,
        implementation_status: str,
        lifecycle: dict[str, Any],
        high_risk: bool,
    ) -> str:
        if benchmark_status == "blocked" or legal_document_evidence_status == "blocked":
            return "blocked"
        if implementation_status == "blocked":
            return "blocked"
        if high_risk and "high_risk_release_gate_linked" in lifecycle.get("blocking_check_ids", []):
            return "blocked"
        if benchmark_status in {"create_fixture", "review_required"}:
            return "release_review_required"
        if legal_document_evidence_status in {"not_run", "review_required"}:
            return "release_review_required"
        if implementation_status == "review_required":
            return "release_review_required"
        if "customer_visible_resolution" in lifecycle.get("next_allowed_states", []):
            return "customer_resolution_ready"
        return "release_review_required"

    def _lifecycle_source(self, *, backlog_row: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
        release_gate_links = _strings(
            observation.get("release_gate_links")
            or observation.get("release_gates")
            or backlog_row.get("release_gate_links")
        )
        return {
            "id": str(observation.get("id") or observation.get("ticket_id") or backlog_row.get("cluster_id")),
            "state": str(observation.get("state") or observation.get("current_state") or "release_validation"),
            "category": str(backlog_row.get("normalized_topic") or "general_feedback"),
            "summary": str(backlog_row.get("normalized_topic") or "feedback cluster").replace("_", " "),
            "priority": "P1" if str(backlog_row.get("severity") or "low") in HIGH_RISK_SEVERITIES else "P2",
            "risk_level": "high" if str(backlog_row.get("severity") or "low") in HIGH_RISK_SEVERITIES else "medium",
            "roadmap_gap_id": str(backlog_row.get("primary_need_id") or ""),
            "release_gate_links": release_gate_links,
            "work_owner": str(observation.get("work_owner") or observation.get("owner") or "product_maintainer"),
            "release_validation_status": str(
                observation.get("release_validation_status") or observation.get("validation_status") or "not_run"
            ),
            "customer_visible_resolution": str(
                observation.get("customer_visible_resolution")
                or observation.get("customer_resolution_note")
                or observation.get("public_resolution")
                or ""
            ),
            "customer_notification_ready": observation.get("customer_notification_ready")
            or observation.get("customer_notified")
            or False,
            "closure_summary": str(observation.get("closure_summary") or ""),
        }

    def _release_gate_links(self, backlog_row: dict[str, Any], observation: dict[str, Any]) -> list[str]:
        return _unique(
            _strings(backlog_row.get("release_gate_links"))
            + _strings(observation.get("release_gate_links"))
            + _strings(observation.get("release_gates"))
            + ["feedback-user-need-legal-document-benchmark-release-packet"]
        )

    def _implementation_status(self, default_status: str, observation: dict[str, Any]) -> str:
        observed = str(
            observation.get("implementation_review_status")
            or observation.get("implementation_status")
            or observation.get("work_status")
            or ""
        ).lower()
        if observed in {"pass", "passed", "ready", "verified", "accepted"}:
            return "ready"
        if observed in {"blocked", "fail", "failed"}:
            return "blocked"
        if observed in {"review", "review_required", "needs_review"}:
            return "review_required"
        return default_status

    def _reason_codes(
        self,
        *,
        backlog_row: dict[str, Any],
        implementation_item: dict[str, Any],
        implementation_status: str,
        lifecycle_blockers: list[str],
        release_action_status: str,
        high_risk: bool,
    ) -> list[str]:
        codes = [
            f"release-action-{release_action_status}",
            f"benchmark-action-{backlog_row.get('benchmark_action_status') or 'review_required'}",
            f"legal-document-evidence-{backlog_row.get('legal_document_evidence_status') or 'not_run'}",
            f"implementation-{implementation_status or 'review_required'}",
        ]
        if high_risk:
            codes.append("high-risk-feedback-release-gate")
        if backlog_row.get("suggested_fixture_ids"):
            codes.append("suggested-fixture-work-present")
        codes.extend(f"lifecycle-blocker-{blocker}" for blocker in lifecycle_blockers)
        codes.extend(_strings(backlog_row.get("reason_codes"))[:4])
        codes.extend(_strings(implementation_item.get("blocker_codes"))[:3])
        codes.extend(_strings(implementation_item.get("review_reason_codes"))[:3])
        return _unique(codes)

    def _next_actions(
        self,
        *,
        release_action_status: str,
        backlog_row: dict[str, Any],
        implementation_item: dict[str, Any],
        lifecycle: dict[str, Any],
    ) -> list[str]:
        actions: list[str] = []
        if release_action_status == "blocked":
            actions.append("Do not prepare customer-visible feedback resolution until blocking benchmark or lifecycle gates clear.")
        elif release_action_status == "release_review_required":
            actions.append("Keep this feedback cluster in maintainer release review before customer-visible resolution.")
        else:
            actions.append("Customer-visible resolution metadata is ready for maintainer approval; do not claim customer notification here.")
        actions.extend(_strings(backlog_row.get("next_actions"))[:2])
        actions.extend(_strings(implementation_item.get("next_actions"))[:2])
        actions.extend(_strings(lifecycle.get("required_actions"))[:2])
        return _unique(actions)[:6]

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        ready_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocked_rows:
            return [
                "Clear blocked feedback release rows before claiming customer-visible resolution: "
                + ", ".join(row["cluster_id"] for row in blocked_rows[:5])
                + ".",
                "Prioritize high-risk feedback rows with legal-document evidence or lifecycle blockers first.",
                "Keep public/customer notes out of the packet; attach only pass/fail release observation metadata.",
            ]
        if review_rows:
            return [
                "Run local legal-document benchmark evidence and feedback lifecycle checks before customer-facing updates.",
                "Use release observations with pass/waived validation and privacy-safe note metadata when review is complete.",
            ]
        if ready_rows:
            return ["Ready rows can enter maintainer approval for customer-visible resolution metadata."]
        return ["Submit privacy-safe feedback clusters and release observations to build release rows."]

    def _release_observations(self, value: Any) -> dict[str, dict[str, Any]]:
        observations: list[dict[str, Any]]
        if isinstance(value, dict):
            observations = [item for item in value.values() if isinstance(item, dict)]
        elif isinstance(value, list):
            observations = [item for item in value if isinstance(item, dict)]
        else:
            observations = []

        result: dict[str, dict[str, Any]] = {}
        for item in observations:
            keys = _strings(
                [
                    item.get("cluster_id"),
                    item.get("normalized_topic"),
                    item.get("primary_need_id"),
                    item.get("ticket_id"),
                    item.get("id"),
                ]
            )
            for key in keys:
                result[key] = item
        return result

    def _observation_for_row(self, row: dict[str, Any], observations: dict[str, dict[str, Any]]) -> dict[str, Any]:
        for key in (
            str(row.get("cluster_id") or ""),
            str(row.get("normalized_topic") or ""),
            str(row.get("primary_need_id") or ""),
        ):
            if key in observations:
                return observations[key]
        return {}

    def _backlog_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = ("items", "feedback", "legal_document_evidence")
        return {key: payload[key] for key in allowed if key in payload}

    def _safe_mapping(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _release_action_rank(self, status: str) -> int:
        return {"blocked": 0, "release_review_required": 1, "customer_resolution_ready": 2}.get(status, 9)


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item]
    return [str(value)] if value else []


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
