from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_route_plan_execution_readiness import (
    LegalDocumentBenchmarkRoutePlanExecutionReadinessService,
)
from services.legal_document_benchmark_route_plan_execution_result_archive import (
    LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService,
)


HANDOFF_ID = "legal-document-benchmark-route-plan-execution-result-handoff"


class LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService:
    """Bind sanitized route-plan execution results to release-evidence decisions."""

    def __init__(
        self,
        readiness_service: LegalDocumentBenchmarkRoutePlanExecutionReadinessService | None = None,
        archive_service: LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService | None = None,
    ) -> None:
        self.readiness_service = readiness_service or LegalDocumentBenchmarkRoutePlanExecutionReadinessService()
        self.archive_service = archive_service or LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService(
            self.readiness_service
        )

    def build_handoff(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        readiness_payload = data.get("execution_readiness") if isinstance(data.get("execution_readiness"), dict) else data
        archive_payload = (
            data.get("execution_result_archive")
            if isinstance(data.get("execution_result_archive"), dict)
            else data
        )
        readiness = self.readiness_service.build_packet(readiness_payload)
        archive = self.archive_service.build_archive(archive_payload)
        handoff_rows = [self._handoff_row(row) for row in archive.get("archive_rows", [])]
        checks = self._checks(readiness, archive, handoff_rows)
        blocking_check_ids = [check["id"] for check in checks if check["status"] == "fail"]
        warning_check_ids = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking_check_ids else ("review_required" if warning_check_ids else "ready")
        release_action = self._release_action(status, archive)

        return {
            "id": HANDOFF_ID,
            "title": "Legal document benchmark route-plan execution result handoff",
            "status": status,
            "method": {
                "type": "metadata-only-route-plan-execution-result-release-handoff",
                "notes": [
                    "Turns sanitized manual route-plan observation archives into release-evidence handoff decisions.",
                    "Requires a ready execution-readiness packet and ready archive rows before evidence can be attached.",
                    "Does not execute benchmarks, call providers, write archive files, record approvals, or shift traffic.",
                ],
            },
            "summary": {
                "readiness_status": readiness["status"],
                "archive_status": archive["status"],
                "manual_execution_ready": readiness["summary"]["manual_execution_ready"],
                "observation_count": archive["summary"]["observation_count"],
                "handoff_row_count": len(handoff_rows),
                "attachable_row_count": sum(1 for row in handoff_rows if row["can_attach_to_release"]),
                "review_row_count": sum(1 for row in handoff_rows if row["handoff_status"] == "review_required"),
                "blocked_row_count": sum(1 for row in handoff_rows if row["handoff_status"] == "blocked"),
                "cheap_first_aligned_count": archive["summary"]["cheap_first_aligned_count"],
                "ready_observation_count": archive["summary"]["ready_observation_count"],
                "recommended_fixture_limit": archive["summary"]["recommended_fixture_limit"],
                "max_parallel_model_requests": archive["summary"]["max_parallel_model_requests"],
                "forbidden_payload_field_count": archive["summary"]["forbidden_payload_field_count"],
                "ready_for_release_evidence": status == "ready",
                "release_action": release_action,
                "raw_payload_echoed": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "archive_file_written": False,
                "maintainer_approval_recorded": False,
                "benchmark_execution_claimed": False,
                "traffic_shifted": False,
                "configuration_written": False,
            },
            "handoff_rows": handoff_rows,
            "checks": checks,
            "blocking_check_ids": blocking_check_ids,
            "warning_check_ids": warning_check_ids,
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
                    "forbidden_payload_field_count": archive["summary"]["forbidden_payload_field_count"],
                    "blocking_check_ids": list(archive.get("blocking_check_ids", [])),
                    "warning_check_ids": list(archive.get("warning_check_ids", [])),
                },
            },
            "release_evidence_packet": {
                "ready_for_release_evidence": status == "ready",
                "release_action": release_action,
                "evidence_kind": "sanitized_manual_route_plan_result_metadata",
                "requires_ready_readiness_packet": True,
                "requires_ready_result_archive": True,
                "requires_fixture_limit": True,
                "requires_max_parallel_model_requests": 1,
                "records_maintainer_approval": False,
                "writes_release_record": False,
                "executes_benchmark": False,
                "allowed_evidence_summary": (
                    "Attach only sanitized case id, phase, observed model, status, token, cost, latency, "
                    "fallback, and coarse error metadata after all handoff checks pass."
                ),
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
                "writes_archive_file": False,
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
                    "Sanitized legal-document route-plan result metadata has a release-evidence handoff decision."
                ),
            },
            "recommended_actions": self._recommended_actions(status, archive),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_result_handoff.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_result_archive.py tests/test_legal_document_benchmark_route_plan_execution_readiness.py -q",
            ],
        }

    def _handoff_row(self, archive_row: dict[str, Any]) -> dict[str, Any]:
        row_status = str(archive_row.get("result_status") or "blocked")
        can_attach = row_status == "ready"
        return {
            "id": f"handoff-{archive_row.get('id', 'row')}",
            "case_id": str(archive_row.get("case_id") or ""),
            "phase": str(archive_row.get("phase") or "primary"),
            "handoff_status": row_status,
            "can_attach_to_release": can_attach,
            "handoff_action": self._row_action(row_status),
            "archive_release_action": str(archive_row.get("release_action") or ""),
            "route_plan_match": archive_row.get("route_plan_match") is True,
            "cheap_first_aligned": archive_row.get("cheap_first_aligned") is True,
            "observed_status": str(archive_row.get("observed_status") or ""),
            "observed_model": str(archive_row.get("observed_model") or ""),
            "expected_model": str(archive_row.get("expected_model") or ""),
            "observed_cost_usd": archive_row.get("observed_cost_usd"),
            "latency_ms": archive_row.get("latency_ms"),
            "reason_codes": list(archive_row.get("reason_codes", []))[:12],
        }

    def _checks(
        self,
        readiness: dict[str, Any],
        archive: dict[str, Any],
        handoff_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        observation_count = int(archive["summary"]["observation_count"])
        ready_observation_count = int(archive["summary"]["ready_observation_count"])
        cheap_first_aligned_count = int(archive["summary"]["cheap_first_aligned_count"])
        recommended_fixture_limit = int(archive["summary"]["recommended_fixture_limit"])
        max_parallel = int(archive["summary"]["max_parallel_model_requests"])
        blocked_rows = [row["id"] for row in handoff_rows if row["handoff_status"] == "blocked"]
        review_rows = [row["id"] for row in handoff_rows if row["handoff_status"] == "review_required"]
        cheap_first_gaps = [row["id"] for row in handoff_rows if not row["cheap_first_aligned"]]
        forbidden_count = int(archive["summary"]["forbidden_payload_field_count"])
        return [
            _check(
                "execution-readiness-ready",
                "fail" if readiness["status"] == "blocked" else ("warn" if readiness["status"] != "ready" else "pass"),
                "Release evidence handoff requires the route-plan execution-readiness packet to be ready.",
                list(readiness.get("blocking_gate_ids", []))[:12],
            ),
            _check(
                "execution-result-archive-ready",
                "fail"
                if archive["status"] == "blocked"
                else ("warn" if archive["status"] != "ready" else "pass"),
                "Release evidence handoff requires a ready sanitized execution-result archive.",
                list(archive.get("blocking_check_ids", []))[:12] + list(archive.get("warning_check_ids", []))[:12],
            ),
            _check(
                "manual-observations-present",
                "warn" if observation_count == 0 else "pass",
                "At least one sanitized manual observation row is needed before attaching release evidence.",
                [],
            ),
            _check(
                "all-archive-rows-attachable",
                "fail" if blocked_rows else ("warn" if review_rows else "pass"),
                "Every archived result row must be attachable or explicitly reviewed before release evidence use.",
                blocked_rows + review_rows,
            ),
            _check(
                "cheap-first-handoff-aligned",
                "warn"
                if observation_count == 0
                else ("pass" if cheap_first_aligned_count == observation_count else "fail"),
                "Observed models must remain aligned with the planned cheap-first route before evidence handoff.",
                cheap_first_gaps,
            ),
            _check(
                "low-resource-envelope-preserved",
                "fail" if observation_count > recommended_fixture_limit or max_parallel != 1 else "pass",
                "Release evidence handoff stays inside fixture_limit=3 and max_parallel_model_requests=1.",
                [str(observation_count), str(max_parallel)]
                if observation_count > recommended_fixture_limit or max_parallel != 1
                else [],
            ),
            _check(
                "metadata-only-boundary-preserved",
                "fail" if forbidden_count else "pass",
                "Handoff derives only metadata from the archive and does not return raw benchmark or provider payloads.",
                [str(forbidden_count)] if forbidden_count else [],
            ),
            _check(
                "release-evidence-counts-match",
                "pass" if ready_observation_count == sum(1 for row in handoff_rows if row["can_attach_to_release"]) else "fail",
                "Attachable handoff rows must match ready archive observation counts.",
                [],
            ),
            _check(
                "no-release-claim-overreach",
                "pass",
                "The handoff does not record approval, claim benchmark execution, change defaults, or shift traffic.",
                [],
            ),
        ]

    def _release_action(self, status: str, archive: dict[str, Any]) -> str:
        if status == "ready":
            return "attach_to_release_evidence"
        if archive["status"] == "not_run":
            return "collect_manual_observations_before_release_evidence"
        if status == "review_required":
            return "review_result_archive_before_release_evidence"
        return "hold_release_evidence_until_blockers_clear"

    def _row_action(self, status: str) -> str:
        if status == "ready":
            return "attach_row_as_metadata_only_evidence"
        if status == "review_required":
            return "review_row_before_attachment"
        return "hold_row_until_archive_blockers_clear"

    def _recommended_actions(self, status: str, archive: dict[str, Any]) -> list[str]:
        if status == "ready":
            return [
                "Attach the sanitized route-plan execution result archive as metadata-only release evidence.",
                "Keep raw prompts, legal text, provider payloads, and approval records outside this handoff service.",
            ]
        if archive["status"] == "not_run":
            return [
                "Run up to three manual serial legal-document route observations, then archive sanitized metadata.",
                "Refresh the handoff after the archive reports ready rows aligned to the cheap-first route plan.",
            ]
        if status == "review_required":
            return [
                "Resolve warning rows or add maintainer notes before attaching the archive to release evidence.",
                "Keep the release evidence packet in review status until every handoff row is attachable.",
            ]
        return [
            "Do not attach blocked result archives to release evidence.",
            "Clear readiness, route matching, cheap-first model alignment, low-resource, or metadata-boundary blockers first.",
        ]


def _check(check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "reason": reason,
        "evidence_count": len(evidence),
        "evidence": evidence[:12],
    }
