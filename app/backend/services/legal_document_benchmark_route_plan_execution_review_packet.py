from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_route_plan_execution_readiness import (
    LegalDocumentBenchmarkRoutePlanExecutionReadinessService,
)
from services.legal_document_benchmark_route_plan_execution_result_archive import (
    LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService,
)
from services.legal_document_benchmark_route_plan_execution_result_handoff import (
    LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService,
)


REVIEW_PACKET_ID = "legal-document-benchmark-route-plan-execution-review-packet"


class LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService:
    """Build a reviewer-facing packet for route-plan execution evidence."""

    def __init__(
        self,
        readiness_service: LegalDocumentBenchmarkRoutePlanExecutionReadinessService | None = None,
        archive_service: LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService | None = None,
        handoff_service: LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService | None = None,
    ) -> None:
        self.readiness_service = readiness_service or LegalDocumentBenchmarkRoutePlanExecutionReadinessService()
        self.archive_service = archive_service or LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService(
            self.readiness_service
        )
        self.handoff_service = handoff_service or LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService(
            self.readiness_service,
            self.archive_service,
        )

    def build_packet(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        readiness_payload = data.get("execution_readiness") if isinstance(data.get("execution_readiness"), dict) else data
        archive_payload = (
            data.get("execution_result_archive")
            if isinstance(data.get("execution_result_archive"), dict)
            else data
        )
        readiness = self.readiness_service.build_packet(readiness_payload)
        archive = self.archive_service.build_archive(archive_payload)
        handoff = self.handoff_service.build_handoff(data)
        review_items = self._review_items(readiness, archive, handoff)
        checks = self._checks(readiness, archive, handoff, review_items)
        blocking_check_ids = [check["id"] for check in checks if check["status"] == "fail"]
        warning_check_ids = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking_check_ids else ("review_required" if warning_check_ids else "ready")
        release_action = self._release_action(status, handoff)

        return {
            "id": REVIEW_PACKET_ID,
            "title": "Legal document benchmark route-plan execution review packet",
            "status": status,
            "method": {
                "type": "metadata-only-route-plan-execution-review-packet",
                "notes": [
                    "Summarizes readiness, sanitized execution-result archive, and release-evidence handoff.",
                    "Gives reviewers one packet of attach/review/hold decisions and allowed claim wording.",
                    "Does not execute benchmarks, call providers, write release records, approve releases, or shift traffic.",
                ],
            },
            "summary": {
                "readiness_status": readiness["status"],
                "archive_status": archive["status"],
                "handoff_status": handoff["status"],
                "observation_count": archive["summary"]["observation_count"],
                "attachable_row_count": handoff["summary"]["attachable_row_count"],
                "review_row_count": handoff["summary"]["review_row_count"],
                "blocked_row_count": handoff["summary"]["blocked_row_count"],
                "cheap_first_aligned_count": handoff["summary"]["cheap_first_aligned_count"],
                "recommended_fixture_limit": handoff["summary"]["recommended_fixture_limit"],
                "max_parallel_model_requests": handoff["summary"]["max_parallel_model_requests"],
                "review_item_count": len(review_items),
                "blocking_review_item_count": sum(1 for item in review_items if item["status"] == "blocked"),
                "warning_review_item_count": sum(1 for item in review_items if item["status"] == "review_required"),
                "ready_for_release_packet": status == "ready",
                "release_action": release_action,
                "raw_payload_echoed": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "benchmark_executed": False,
                "release_record_written": False,
                "maintainer_approval_recorded": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "review_items": review_items,
            "checks": checks,
            "blocking_check_ids": blocking_check_ids,
            "warning_check_ids": warning_check_ids,
            "claim_review_rows": self._claim_review_rows(status, handoff),
            "source_summaries": {
                "execution_readiness": {
                    "id": readiness["id"],
                    "status": readiness["status"],
                    "manual_execution_ready": readiness["summary"]["manual_execution_ready"],
                    "blocking_gate_count": readiness["summary"]["blocking_gate_count"],
                    "warning_gate_count": readiness["summary"]["warning_gate_count"],
                },
                "execution_result_archive": {
                    "id": archive["id"],
                    "status": archive["status"],
                    "observation_count": archive["summary"]["observation_count"],
                    "ready_observation_count": archive["summary"]["ready_observation_count"],
                    "blocked_observation_count": archive["summary"]["blocked_observation_count"],
                    "blocking_check_ids": list(archive.get("blocking_check_ids", [])),
                    "warning_check_ids": list(archive.get("warning_check_ids", [])),
                },
                "execution_result_handoff": {
                    "id": handoff["id"],
                    "status": handoff["status"],
                    "release_action": handoff["summary"]["release_action"],
                    "ready_for_release_evidence": handoff["summary"]["ready_for_release_evidence"],
                    "attachable_row_count": handoff["summary"]["attachable_row_count"],
                    "blocking_check_ids": list(handoff.get("blocking_check_ids", [])),
                    "warning_check_ids": list(handoff.get("warning_check_ids", [])),
                },
            },
            "review_packet_policy": {
                "evidence_kind": "metadata_only_route_plan_execution_review",
                "requires_ready_handoff": True,
                "requires_ready_archive": True,
                "requires_ready_readiness": True,
                "requires_fixture_limit": 3,
                "requires_max_parallel_model_requests": 1,
                "records_maintainer_approval": False,
                "writes_release_record": False,
                "executes_benchmark": False,
                "allowed_release_action": "attach_to_release_evidence",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_case_ids": True,
                "returns_route_metadata": True,
                "returns_public_benchmark_text": False,
                "returns_fixture_snippets": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_request_bodies": False,
                "returns_response_bodies": False,
                "returns_headers": False,
                "returns_gateway_responses": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "writes_release_record": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "claim_boundary": {
                "benchmark_executed_by_service": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_score_claimed": False,
                "production_quality_claimed": False,
                "maintainer_approval_claimed": False,
                "release_approval_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "allowed_claim": (
                    "A metadata-only reviewer packet summarizes sanitized legal-document route-plan execution evidence."
                ),
            },
            "recommended_actions": self._recommended_actions(status, handoff),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_review_packet.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_result_handoff.py tests/test_legal_document_benchmark_route_plan_execution_result_archive.py -q",
            ],
        }

    def _review_items(
        self,
        readiness: dict[str, Any],
        archive: dict[str, Any],
        handoff: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "execution-readiness",
                "title": "Execution readiness packet",
                "status": self._review_status(readiness["status"]),
                "source_status": readiness["status"],
                "release_action": "allow_manual_observation_review"
                if readiness["status"] == "ready"
                else "review_readiness_before_results",
                "evidence_count": readiness["summary"]["gate_count"],
                "blocking_ids": list(readiness.get("blocking_gate_ids", []))[:12],
                "warning_ids": list(readiness.get("warning_gate_ids", []))[:12],
            },
            {
                "id": "execution-result-archive",
                "title": "Execution result archive",
                "status": self._review_status(archive["status"]),
                "source_status": archive["status"],
                "release_action": "allow_handoff_review"
                if archive["status"] == "ready"
                else "collect_or_fix_sanitized_observations",
                "evidence_count": archive["summary"]["observation_count"],
                "blocking_ids": list(archive.get("blocking_check_ids", []))[:12],
                "warning_ids": list(archive.get("warning_check_ids", []))[:12],
            },
            {
                "id": "execution-result-handoff",
                "title": "Execution result handoff",
                "status": self._review_status(handoff["status"]),
                "source_status": handoff["status"],
                "release_action": str(handoff["summary"]["release_action"]),
                "evidence_count": handoff["summary"]["attachable_row_count"],
                "blocking_ids": list(handoff.get("blocking_check_ids", []))[:12],
                "warning_ids": list(handoff.get("warning_check_ids", []))[:12],
            },
        ]

    def _checks(
        self,
        readiness: dict[str, Any],
        archive: dict[str, Any],
        handoff: dict[str, Any],
        review_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            _check(
                "readiness-review-packet-linked",
                "pass" if readiness["status"] == "ready" else ("fail" if readiness["status"] == "blocked" else "warn"),
                "The reviewer packet links a ready execution-readiness packet.",
                list(readiness.get("blocking_gate_ids", []))[:12],
            ),
            _check(
                "result-archive-review-packet-linked",
                "pass" if archive["status"] == "ready" else ("fail" if archive["status"] == "blocked" else "warn"),
                "The reviewer packet links a ready sanitized execution-result archive.",
                list(archive.get("blocking_check_ids", []))[:12] + list(archive.get("warning_check_ids", []))[:12],
            ),
            _check(
                "handoff-release-action-ready",
                "pass" if handoff["status"] == "ready" else ("fail" if handoff["status"] == "blocked" else "warn"),
                "Release evidence packet can advance only after handoff is ready.",
                list(handoff.get("blocking_check_ids", []))[:12] + list(handoff.get("warning_check_ids", []))[:12],
            ),
            _check(
                "low-resource-envelope-visible",
                "pass"
                if handoff["summary"]["recommended_fixture_limit"] == 3
                and handoff["summary"]["max_parallel_model_requests"] == 1
                else "fail",
                "Reviewer packet preserves fixture_limit=3 and max_parallel_model_requests=1.",
                [],
            ),
            _check(
                "review-item-blockers-surfaced",
                "pass"
                if all(item["blocking_ids"] or item["status"] != "blocked" for item in review_items)
                else "fail",
                "Blocked source rows expose the blocker ids reviewers need before release evidence use.",
                [item["id"] for item in review_items if item["status"] == "blocked" and not item["blocking_ids"]],
            ),
            _check(
                "no-release-claim-overreach",
                "pass",
                "The packet does not claim benchmark execution, public scores, release approval, or traffic/default changes.",
                [],
            ),
            _check(
                "no-provider-side-effects",
                "pass",
                "The packet does not call providers, gateways, app AI endpoints, public datasets, or the network.",
                [],
            ),
            _check(
                "validation-commands-present",
                "pass",
                "Reviewer packet includes local validation commands for the packet and upstream archive/handoff chain.",
                [],
            ),
        ]

    def _claim_review_rows(self, status: str, handoff: dict[str, Any]) -> list[dict[str, Any]]:
        metadata_allowed = status == "ready" and handoff["summary"]["ready_for_release_evidence"] is True
        return [
            {
                "id": "sanitized-route-plan-result-evidence",
                "allowed": metadata_allowed,
                "claim": "Sanitized manual legal-document route-plan result metadata is ready for release evidence.",
                "reason": "Allowed only after readiness, archive, handoff, cheap-first alignment, and low-resource checks pass.",
            },
            {
                "id": "public-benchmark-score",
                "allowed": False,
                "claim": "Public benchmark score or external leaderboard result.",
                "reason": "No public benchmark run, external dataset evaluation, or leaderboard submission is performed.",
            },
            {
                "id": "live-provider-execution",
                "allowed": False,
                "claim": "This service executed live NewAPI/Gemini benchmark calls.",
                "reason": "The review packet is metadata-only and never calls providers, gateways, or models.",
            },
            {
                "id": "release-or-maintainer-approval",
                "allowed": False,
                "claim": "Maintainer or release approval has been recorded.",
                "reason": "The packet prepares review evidence but writes no approval or release record.",
            },
        ]

    def _release_action(self, status: str, handoff: dict[str, Any]) -> str:
        if status == "ready":
            return "attach_review_packet_to_release_evidence"
        if handoff["summary"]["release_action"] == "collect_manual_observations_before_release_evidence":
            return "collect_manual_observations_before_review_packet"
        if status == "review_required":
            return "review_packet_before_release_evidence"
        return "hold_review_packet_until_blockers_clear"

    def _recommended_actions(self, status: str, handoff: dict[str, Any]) -> list[str]:
        if status == "ready":
            return [
                "Attach this review packet with the sanitized archive and handoff as metadata-only release evidence.",
                "Keep public benchmark scores, provider execution claims, approvals, and raw payloads out of release notes.",
            ]
        if handoff["summary"]["release_action"] == "collect_manual_observations_before_release_evidence":
            return [
                "Collect up to three serial manual observations and submit only sanitized metadata.",
                "Refresh archive, handoff, and review packet after observations are available.",
            ]
        if status == "review_required":
            return [
                "Resolve warning checks or add reviewer notes before attaching the packet to release evidence.",
                "Keep claims limited to repository-backed metadata until handoff becomes ready.",
            ]
        return [
            "Do not attach this packet to release evidence while blockers are present.",
            "Clear readiness, archive, handoff, cheap-first alignment, or metadata-boundary blockers first.",
        ]

    def _review_status(self, status: str) -> str:
        if status == "ready":
            return "ready"
        if status == "blocked":
            return "blocked"
        return "review_required"


def _check(check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "reason": reason,
        "evidence_count": len(evidence),
        "evidence": evidence[:12],
    }
