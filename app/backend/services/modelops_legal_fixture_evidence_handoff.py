from __future__ import annotations

import re
from typing import Any

from services.continuous_session_run_monitor import ContinuousSessionRunMonitorService
from services.legal_fixture_local_run_review import LegalFixtureLocalRunReviewService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)
from services.modelops_legal_fixture_default_promotion_packet import (
    ModelOpsLegalFixtureDefaultPromotionPacketService,
)


FORBIDDEN_INPUT_KEYS = {
    "api_key",
    "authorization",
    "candidate_text",
    "content",
    "gateway_response",
    "generated_text",
    "headers",
    "input_excerpt",
    "legal_text",
    "messages",
    "observations",
    "output_text",
    "prompt",
    "raw_gateway_response",
    "raw_legal_text",
    "raw_model_output",
    "raw_output",
    "raw_payload",
    "raw_response",
    "request_body",
    "response_body",
    "responses",
    "run_report_payload",
    "structured_outputs",
}
SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{16,}|Bearer\s+[A-Za-z0-9._\-]{16,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b|password|secret",
    re.IGNORECASE,
)


class ModelOpsLegalFixtureEvidenceHandoffService:
    """Build archive-safe handoff evidence for low-resource legal fixture runs."""

    def __init__(
        self,
        local_run_review_service: LegalFixtureLocalRunReviewService | None = None,
        benchmark_gate_service: ModelOpsLegalFixtureCheapFirstBenchmarkGateService | None = None,
        promotion_packet_service: ModelOpsLegalFixtureDefaultPromotionPacketService | None = None,
        run_monitor_service: ContinuousSessionRunMonitorService | None = None,
    ) -> None:
        self.local_run_review_service = local_run_review_service or LegalFixtureLocalRunReviewService()
        self.benchmark_gate_service = benchmark_gate_service or ModelOpsLegalFixtureCheapFirstBenchmarkGateService()
        self.promotion_packet_service = promotion_packet_service or ModelOpsLegalFixtureDefaultPromotionPacketService()
        self.run_monitor_service = run_monitor_service or ContinuousSessionRunMonitorService()

    def build_handoff(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        raw_input_field_count = self._raw_input_field_count(data)
        local_run_review = self._local_run_review(data)
        benchmark_gate = self._benchmark_gate(data)
        promotion_packet = self._promotion_packet(data, benchmark_gate)
        handoff_evidence = self._handoff_evidence(local_run_review, benchmark_gate, promotion_packet, raw_input_field_count)
        run_monitor = self._run_monitor(data, handoff_evidence)
        rows = self._handoff_rows(local_run_review, benchmark_gate, promotion_packet, run_monitor)
        checks = self._checks(rows, raw_input_field_count, handoff_evidence, run_monitor)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]

        return {
            "id": "modelops-legal-fixture-evidence-handoff",
            "title": "ModelOps legal fixture evidence handoff",
            "status": self._status(rows, blocking, warnings),
            "method": {
                "type": "metadata-only-legal-fixture-evidence-handoff",
                "notes": [
                    "Joins local-run-review, cheap-first benchmark gate, default-promotion packet, and continuous-session monitor summaries.",
                    "Returns archive-safe status, counts, endpoints, and release blockers only.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or the network.",
                ],
            },
            "summary": {
                "handoff_source_count": len(rows),
                "ready_source_count": sum(1 for row in rows if row["handoff_status"] == "ready"),
                "review_source_count": sum(1 for row in rows if row["handoff_status"] == "review_required"),
                "blocked_source_count": sum(1 for row in rows if row["handoff_status"] == "blocked"),
                "not_run_source_count": sum(1 for row in rows if row["handoff_status"] == "not_run"),
                "local_run_review_status": rows[0]["source_status"],
                "cheap_first_gate_status": rows[1]["source_status"],
                "default_promotion_packet_status": rows[2]["source_status"],
                "run_monitor_status": rows[3]["source_status"],
                "observed_fixture_count": handoff_evidence["summary"]["observed_fixture_count"],
                "archived_fixture_count": handoff_evidence["summary"]["archived_fixture_count"],
                "release_ready": handoff_evidence["summary"]["release_ready"],
                "raw_input_field_count": raw_input_field_count,
                "raw_payload_echoed": False,
                "raw_gateway_response_returned": False,
                "raw_model_output_returned": False,
                "raw_legal_text_returned": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "gateway_called": False,
                "network_called": False,
                "completion_claimed": False,
            },
            "handoff_rows": rows,
            "handoff_evidence_summary": handoff_evidence,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "recommended_actions": self._recommended_actions(rows, raw_input_field_count),
            "source_endpoints": self._source_endpoints(),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_status_counts_only": True,
                "returns_raw_local_run_review": False,
                "returns_run_report_payload": False,
                "returns_observations": False,
                "returns_response_summaries": False,
                "returns_gateway_response": False,
                "returns_gateway_headers": False,
                "returns_request_body": False,
                "returns_messages": False,
                "returns_prompts": False,
                "returns_fixture_excerpt": False,
                "returns_legal_text": False,
                "returns_generated_text": False,
                "returns_model_output": False,
                "returns_credentials": False,
                "returns_emails": False,
                "newapi_called": False,
                "network_called": False,
            },
            "claim_boundary": {
                "live_gateway_quality_claimed": False,
                "public_benchmark_scores_claimed": False,
                "production_legal_accuracy_claimed": False,
                "automatic_default_change_claimed": False,
                "twenty_four_hour_completion_claimed": False,
                "hundred_update_completion_claimed": False,
                "github_push_claimed": False,
                "allowed_claim": "Archive-safe metadata handoff exists for reviewer evaluation of low-resource legal fixture evidence.",
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_fixture_evidence_handoff.py tests/test_legal_fixture_local_run_review.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py -q",
                "python -m pytest tests/test_continuous_session_run_monitor.py tests/test_model_ops_readiness.py -q",
            ],
        }

    def _local_run_review(self, data: dict[str, Any]) -> dict[str, Any]:
        provided = self._dict_value(data, "local_run_review") or self._dict_value(data, "fixture_review")
        if provided:
            return provided
        if "responses" in data:
            return self.local_run_review_service.review(data)
        return {"status": "not_supplied", "summary": {}, "blocking_check_ids": [], "warning_check_ids": []}

    def _benchmark_gate(self, data: dict[str, Any]) -> dict[str, Any]:
        provided = (
            self._dict_value(data, "cheap_first_benchmark_gate")
            or self._dict_value(data, "benchmark_gate")
            or self._dict_value(data, "source_gate")
        )
        if provided:
            return provided
        return self.benchmark_gate_service.build_gate(data)

    def _promotion_packet(self, data: dict[str, Any], benchmark_gate: dict[str, Any]) -> dict[str, Any]:
        provided = (
            self._dict_value(data, "default_promotion_packet")
            or self._dict_value(data, "promotion_packet")
        )
        if provided:
            return provided
        return self.promotion_packet_service.build_packet({"source_gate": benchmark_gate})

    def _run_monitor(self, data: dict[str, Any], handoff_evidence: dict[str, Any]) -> dict[str, Any]:
        provided = self._dict_value(data, "continuous_session_run_monitor") or self._dict_value(data, "run_monitor")
        if provided:
            return provided
        monitor_payload: dict[str, Any] = {"low_resource_fixture_review": handoff_evidence}
        for key in ("events", "validation_events", "session_start_timestamp", "current_timestamp"):
            if key in data:
                monitor_payload[key] = data[key]
        return self.run_monitor_service.build_monitor(monitor_payload)

    def _handoff_evidence(
        self,
        local_run_review: dict[str, Any],
        benchmark_gate: dict[str, Any],
        promotion_packet: dict[str, Any],
        raw_input_field_count: int,
    ) -> dict[str, Any]:
        review_summary = self._summary(local_run_review)
        gate_summary = self._summary(benchmark_gate)
        promotion_summary = self._summary(promotion_packet)
        observed_count = self._int_value(review_summary, "observed_fixture_count") or self._int_value(
            gate_summary,
            "evaluated_fixture_count",
        )
        blocking_count = (
            len(local_run_review.get("blocking_check_ids") or [])
            + self._int_value(gate_summary, "blocked_count")
            + self._int_value(promotion_summary, "blocking_item_count")
            + (1 if raw_input_field_count else 0)
        )
        warning_count = (
            len(local_run_review.get("warning_check_ids") or [])
            + self._int_value(gate_summary, "review_required_count")
            + self._int_value(promotion_summary, "review_item_count")
        )
        release_ready = (
            self._safe_status(local_run_review) == "ready"
            and self._safe_status(benchmark_gate) in {"ready", "pass"}
            and self._bool_value(promotion_summary, "default_change_allowed_by_packet")
            and blocking_count == 0
        )
        return {
            "status": "ready" if release_ready else ("blocked" if blocking_count else "review_recommended"),
            "summary": {
                "review_status": self._safe_status(local_run_review),
                "gate_status": self._safe_status(benchmark_gate),
                "promotion_status": self._safe_status(promotion_packet),
                "observed_fixture_count": observed_count,
                "archived_fixture_count": self._int_value(promotion_summary, "archived_fixture_count"),
                "blocking_check_count": blocking_count,
                "warning_check_count": warning_count,
                "release_ready": release_ready,
                "raw_input_field_count": raw_input_field_count,
                "raw_payload_echoed": False,
            },
            "source_endpoints": self._source_endpoints(),
        }

    def _handoff_rows(
        self,
        local_run_review: dict[str, Any],
        benchmark_gate: dict[str, Any],
        promotion_packet: dict[str, Any],
        run_monitor: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            self._row(
                "local-run-review",
                "Local run review",
                local_run_review,
                "/api/v1/maintenance/legal-review-benchmark/local-run-review",
            ),
            self._row(
                "cheap-first-benchmark-gate",
                "Cheap-first benchmark gate",
                benchmark_gate,
                "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
            ),
            self._row(
                "default-promotion-packet",
                "Default promotion packet",
                promotion_packet,
                "/api/v1/maintenance/legal-review-benchmark/default-promotion-packet",
            ),
            self._row(
                "continuous-session-run-monitor",
                "Continuous session run monitor",
                run_monitor,
                "/api/v1/maintenance/continuous-session-run-monitor",
            ),
        ]

    def _row(self, source_id: str, label: str, source: dict[str, Any], endpoint: str) -> dict[str, Any]:
        summary = self._summary(source)
        status = self._safe_status(source)
        return {
            "id": source_id,
            "label": label,
            "endpoint": endpoint,
            "source_status": status,
            "handoff_status": self._handoff_status(status),
            "blocking_count": len(source.get("blocking_check_ids") or []) + self._int_value(summary, "blocker_count"),
            "warning_count": len(source.get("warning_check_ids") or []) + self._int_value(summary, "warning_check_count"),
            "observed_fixture_count": self._int_value(summary, "observed_fixture_count"),
            "not_run_fixture_count": self._int_value(summary, "not_run_fixture_count"),
            "release_ready": self._bool_value(summary, "release_ready")
            or self._bool_value(summary, "default_change_allowed_by_packet"),
            "raw_payload_returned": False,
            "raw_gateway_response_returned": False,
            "raw_model_output_returned": False,
        }

    def _handoff_status(self, status: str) -> str:
        if status in {"ready", "pass", "ready_for_review"}:
            return "ready"
        if status in {"blocked", "fail", "needs_escalation"}:
            return "blocked"
        if status in {"not_run", "not_started", "not_supplied", "not_ready"}:
            return "not_run"
        return "review_required"

    def _checks(
        self,
        rows: list[dict[str, Any]],
        raw_input_field_count: int,
        handoff_evidence: dict[str, Any],
        run_monitor: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "archive-safe-handoff-boundary",
                "status": "pass" if raw_input_field_count == 0 else "warn",
                "reason": f"Forbidden raw/sensitive input field count is {raw_input_field_count}; raw values are not echoed.",
            },
            {
                "id": "handoff-source-chain-present",
                "status": "pass" if len(rows) == 4 else "fail",
                "reason": "Local review, benchmark gate, promotion packet, and run monitor source rows are present.",
            },
            {
                "id": "low-resource-fixture-evidence-linked",
                "status": "pass"
                if handoff_evidence["summary"]["observed_fixture_count"] > 0
                else "warn",
                "reason": "Observed fixture evidence is available for the active-session monitor."
                if handoff_evidence["summary"]["observed_fixture_count"] > 0
                else "No observed fixture evidence has been supplied yet.",
            },
            {
                "id": "continuous-run-monitor-non-completion-claim",
                "status": "pass"
                if run_monitor.get("summary", {}).get("completion_ready") is not True
                else "warn",
                "reason": "The handoff does not claim 24-hour or 100-update completion.",
            },
            {
                "id": "configuration-and-traffic-boundary",
                "status": "pass",
                "reason": "The handoff never writes configuration, changes defaults, shifts traffic, or calls gateways.",
            },
        ]

    def _recommended_actions(self, rows: list[dict[str, Any]], raw_input_field_count: int) -> list[str]:
        actions: list[str] = []
        if raw_input_field_count:
            actions.append("Re-submit only archive-safe summaries; keep raw gateway responses, prompts, and output text out of handoff payloads.")
        if any(row["handoff_status"] == "not_run" for row in rows):
            actions.append("Run local-run-review, then post the summary through cheap-first benchmark gate and default-promotion packet.")
        if any(row["handoff_status"] == "blocked" for row in rows):
            actions.append("Resolve blocked low-resource fixture evidence before using it in active-session continuity review.")
        actions.append("Attach this handoff summary to continuous-session run-monitor as low_resource_fixture_review evidence.")
        actions.append("Do not treat this handoff as proof of GitHub push, 24-hour continuity, or 100+ completed updates.")
        return actions[:6]

    def _status(self, rows: list[dict[str, Any]], blocking: list[str], warnings: list[str]) -> str:
        if blocking:
            return "blocked"
        if all(row["handoff_status"] == "ready" for row in rows):
            return "ready"
        if all(row["handoff_status"] == "not_run" for row in rows):
            return "not_run"
        if warnings:
            return "review_required"
        return "review_required"

    def _raw_input_field_count(self, value: Any) -> int:
        if isinstance(value, dict):
            count = 0
            for key, child in value.items():
                key_text = str(key).strip().lower()
                if key_text in FORBIDDEN_INPUT_KEYS:
                    count += 1
                    continue
                count += self._raw_input_field_count(child)
            return count
        if isinstance(value, list):
            return sum(self._raw_input_field_count(item) for item in value[:50])
        if isinstance(value, str) and SENSITIVE_PATTERN.search(value):
            return 1
        return 0

    def _source_endpoints(self) -> dict[str, str]:
        return {
            "local_run_review": "/api/v1/maintenance/legal-review-benchmark/local-run-review",
            "cheap_first_benchmark_gate": "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
            "default_promotion_packet": "/api/v1/maintenance/legal-review-benchmark/default-promotion-packet",
            "continuous_session_run_monitor": "/api/v1/maintenance/continuous-session-run-monitor",
            "model_ops_handoff": "/api/v1/aihub/models/legal-fixture-evidence-handoff",
        }

    def _dict_value(self, data: dict[str, Any], key: str) -> dict[str, Any]:
        value = data.get(key)
        return value if isinstance(value, dict) else {}

    def _summary(self, value: dict[str, Any]) -> dict[str, Any]:
        summary = value.get("summary")
        return summary if isinstance(summary, dict) else {}

    def _safe_status(self, value: dict[str, Any]) -> str:
        raw = str(value.get("status") or "not_supplied").strip().lower().replace(" ", "_")
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw)[:80] or "not_supplied"

    def _int_value(self, data: dict[str, Any], key: str) -> int:
        value = data.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    def _bool_value(self, data: dict[str, Any], key: str) -> bool:
        return data.get(key) is True
