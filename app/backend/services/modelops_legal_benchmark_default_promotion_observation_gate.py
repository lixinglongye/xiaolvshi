from __future__ import annotations

import re
from typing import Any

from services.modelops_legal_benchmark_default_promotion_execution_handoff import (
    ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService,
)


RAW_INPUT_FIELD_NAMES = {
    "api_key",
    "authorization",
    "candidate_text",
    "client_email",
    "content",
    "document_text",
    "execution_payload",
    "fixture_text",
    "generated_text",
    "headers",
    "incident_report",
    "messages",
    "observation_payload",
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
    "secret",
}
SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._\-]{16,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b|password|secret",
    re.IGNORECASE,
)
FAIL_STATUSES = {"blocked", "fail", "failed", "error", "rollback_required"}
READY_STATUSES = {"pass", "ready", "ok", "success", "observed", "clear"}
INCIDENT_STATUSES = {"incident", "incident_open", "failed", "rollback_required", "regression_detected"}


class ModelOpsLegalBenchmarkDefaultPromotionObservationGateService:
    """Build a metadata-only post-execution observation gate for legal default-promotion review."""

    def __init__(
        self,
        execution_handoff_service: ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService | None = None,
    ) -> None:
        self.execution_handoff_service = (
            execution_handoff_service or ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService()
        )

    def build_gate(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        execution_handoff = self._source_dict(
            data,
            "legal_benchmark_default_promotion_execution_handoff",
            "default_promotion_execution_handoff",
            "execution_handoff",
        )
        if not execution_handoff:
            execution_handoff = self.execution_handoff_service.build_handoff(data or None)

        raw_input_field_count = self._raw_input_field_count(data)
        handoff_rows = self._list_of_dicts(execution_handoff.get("handoff_rows"))
        observation_rows = [
            self._observation_row(index, row, execution_handoff) for index, row in enumerate(handoff_rows, start=1)
        ]
        rollback_window_rows = [self._rollback_window_row(row) for row in observation_rows]
        source_status_rows = self._source_status_rows(execution_handoff)
        checks = self._checks(execution_handoff, observation_rows, rollback_window_rows, raw_input_field_count)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        observed_rows = [row for row in observation_rows if row["observation_gate_status"] == "observation_ready"]
        review_rows = [row for row in observation_rows if row["observation_gate_status"] == "review_required"]
        blocked_rows = [row for row in observation_rows if row["observation_gate_status"] == "blocked"]
        rollback_required_rows = [
            row for row in observation_rows if row["observation_gate_status"] == "rollback_required"
        ]
        not_run_rows = [row for row in observation_rows if row["observation_gate_status"] == "not_run"]
        status = (
            "blocked"
            if blocking or blocked_rows or rollback_required_rows
            else "ready"
            if observation_rows and len(observed_rows) == len(observation_rows) and not warnings
            else "review_required"
        )

        return {
            "id": "modelops-legal-benchmark-default-promotion-observation-gate",
            "title": "ModelOps legal benchmark default-promotion observation gate",
            "status": status,
            "observation_policy": {
                "post_change_observation_required": True,
                "route_telemetry_required": True,
                "legal_benchmark_smoke_required": True,
                "rollback_window_required": True,
                "incident_triage_required": True,
                "configuration_change_allowed": False,
                "env_file_write_allowed": False,
                "approval_record_write_allowed": False,
                "signoff_record_write_allowed": False,
                "gateway_call_allowed": False,
                "newapi_call_allowed": False,
                "traffic_shift_allowed": False,
                "rollback_execution_allowed": False,
                "requires_execution_handoff_not_blocked": True,
                "requires_metadata_only_boundary": True,
            },
            "decision": {
                "status": status,
                "observation_gate_ready": status == "ready",
                "default_change_allowed_by_observation_gate": False,
                "configuration_change_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "rollback_execution_allowed": False,
                "release_action": "block_or_rollback_external_default_promotion"
                if status == "blocked"
                else "accept_external_observation_evidence"
                if status == "ready"
                else "collect_post_change_observation_evidence",
            },
            "method": {
                "type": "metadata-only-legal-benchmark-default-promotion-observation-gate",
                "notes": [
                    "Consumes the legal benchmark default-promotion execution handoff after external execution prerequisites are packaged.",
                    "Packages post-change observation, rollback-window, route telemetry, legal benchmark smoke, and incident-triage metadata only.",
                    "Does not write config, env files, approvals, signoff records, rollback records, or traffic controls.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, public datasets, or the network.",
                ],
            },
            "summary": {
                "source_count": len(source_status_rows),
                "observation_row_count": len(observation_rows),
                "observation_ready_count": len(observed_rows),
                "review_required_count": len(review_rows),
                "blocked_count": len(blocked_rows),
                "rollback_required_count": len(rollback_required_rows),
                "not_run_count": len(not_run_rows),
                "rollback_window_clear_count": sum(
                    1 for row in rollback_window_rows if row["rollback_window_status"] == "clear"
                ),
                "execution_handoff_status": self._status_text(execution_handoff),
                "handoff_row_count": self._summary_int(execution_handoff, "handoff_row_count") or len(handoff_rows),
                "ready_for_external_execution_count": self._summary_int(
                    execution_handoff,
                    "ready_for_external_execution_count",
                ),
                "raw_input_field_count": raw_input_field_count,
                "default_change_allowed_by_observation_gate": False,
                "configuration_written": False,
                "env_file_written": False,
                "approval_record_written": False,
                "signoff_record_written": False,
                "rollback_executed": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "traffic_shifted": False,
                "raw_fixture_text_returned": False,
                "raw_document_text_returned": False,
                "raw_model_output_returned": False,
                "raw_payload_echoed": False,
            },
            "source_status_rows": source_status_rows,
            "observation_rows": observation_rows,
            "rollback_window_rows": rollback_window_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "required_observation_roles": [
                "model_ops_maintainer",
                "legal_quality_owner",
                "release_owner",
                "rollback_owner",
            ],
            "source_links": {
                "legal_benchmark_default_promotion_execution_handoff": "/api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff",
                "legal_benchmark_default_promotion_observation_gate": "/api/v1/aihub/models/legal-benchmark-default-promotion-observation-gate",
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, observation_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_model_ids": True,
                "returns_observation_roles": True,
                "returns_rollback_window_status": True,
                "returns_incident_status": True,
                "returns_raw_fixture_text": False,
                "returns_raw_legal_text": False,
                "returns_document_snippets": False,
                "returns_candidate_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "returns_emails": False,
                "newapi_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "approval_record_written": False,
                "traffic_shifted": False,
                "rollback_executed": False,
                "output_scope": "handoff row ids, fixture ids, model ids, observation status, rollback-window status, incident status, counts, check ids, and review actions only",
            },
            "claim_boundary": {
                "post_change_quality_claimed": False,
                "automatic_default_change_claimed": False,
                "configuration_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "traffic_shift_claimed": False,
                "rollback_execution_claimed": False,
                "public_benchmark_scores_claimed": False,
                "production_legal_quality_claimed": False,
                "legal_advice_claimed": False,
                "allowed_claim": "Metadata-only legal benchmark default-promotion post-change observation requirements are packaged for external maintainer review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_benchmark_default_promotion_observation_gate.py tests/test_modelops_legal_benchmark_default_promotion_execution_handoff.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _observation_row(self, index: int, row: dict[str, Any], execution_handoff: dict[str, Any]) -> dict[str, Any]:
        execution_status = self._safe_text(row.get("execution_status"), "not_run")
        post_change_observation_status = self._safe_text(row.get("post_change_observation_status"), "not_observed")
        route_telemetry_status = self._safe_text(row.get("route_telemetry_status"), "not_attached")
        legal_benchmark_smoke_status = self._safe_text(row.get("legal_benchmark_smoke_status"), "not_attached")
        rollback_window_status = self._safe_text(row.get("rollback_window_status"), "not_opened")
        incident_status = self._safe_text(row.get("incident_status"), "not_attached")
        gate_status = self._observation_gate_status(
            execution_status=execution_status,
            post_change_observation_status=post_change_observation_status,
            route_telemetry_status=route_telemetry_status,
            legal_benchmark_smoke_status=legal_benchmark_smoke_status,
            rollback_window_status=rollback_window_status,
            incident_status=incident_status,
            execution_handoff=execution_handoff,
        )
        reason_codes = self._dedupe(
            [
                *self._string_list(row.get("reason_codes")),
                *self._derived_reason_codes(
                    gate_status=gate_status,
                    post_change_observation_status=post_change_observation_status,
                    route_telemetry_status=route_telemetry_status,
                    legal_benchmark_smoke_status=legal_benchmark_smoke_status,
                    rollback_window_status=rollback_window_status,
                    incident_status=incident_status,
                ),
            ]
        )
        return {
            "id": f"legal-benchmark-default-promotion-observation-{index}",
            "source_handoff_row_id": self._safe_text(row.get("id"), f"handoff-row-{index}"),
            "source_signoff_item_id": self._safe_text(row.get("source_signoff_item_id"), f"signoff-item-{index}"),
            "requirement_id": self._safe_text(row.get("requirement_id"), f"requirement-{index}"),
            "fixture_id": self._safe_text(row.get("fixture_id"), "unknown"),
            "task": self._safe_text(row.get("task"), "unknown"),
            "proposed_default_model": self._safe_text(row.get("proposed_default_model"), "unknown"),
            "model_cost_tier": self._safe_text(row.get("model_cost_tier"), "unknown"),
            "execution_status": execution_status,
            "post_change_observation_status": post_change_observation_status,
            "route_telemetry_status": route_telemetry_status,
            "legal_benchmark_smoke_status": legal_benchmark_smoke_status,
            "rollback_window_status": rollback_window_status,
            "incident_status": incident_status,
            "observation_gate_status": gate_status,
            "observation_checks": self._observation_checks(gate_status),
            "blocking_reason_codes": [] if gate_status == "observation_ready" else reason_codes,
            "reason_codes": reason_codes,
            "configuration_change_allowed": False,
            "env_file_write_allowed": False,
            "approval_record_write_allowed": False,
            "signoff_record_write_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
            "rollback_execution_allowed": False,
            "default_change_allowed_by_observation_gate": False,
            "observation_action": self._observation_action(gate_status, row),
        }

    def _rollback_window_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": f"{row['id']}-rollback-window",
            "source_observation_row_id": row["id"],
            "fixture_id": row["fixture_id"],
            "task": row["task"],
            "proposed_default_model": row["proposed_default_model"],
            "rollback_window_status": row["rollback_window_status"],
            "incident_status": row["incident_status"],
            "rollback_owner_role": "rollback_owner",
            "rollback_window_checks": self._rollback_window_checks(row["observation_gate_status"]),
            "rollback_execution_allowed": False,
            "rollback_executed": False,
            "traffic_shift_allowed": False,
            "configuration_change_allowed": False,
        }

    def _source_status_rows(self, execution_handoff: dict[str, Any]) -> list[dict[str, Any]]:
        summary = self._summary(execution_handoff)
        return [
            {
                "id": "legal-benchmark-default-promotion-execution-handoff",
                "label": "Legal benchmark default-promotion execution handoff",
                "source_key": "legal_benchmark_default_promotion_execution_handoff",
                "source_status": self._status_text(execution_handoff),
                "observation_status": "blocked" if self._is_blocked(execution_handoff) else "review_required",
                "row_count": self._summary_int(execution_handoff, "handoff_row_count"),
                "blocking_count": len(execution_handoff.get("blocking_check_ids") or []) + self._summary_int(
                    execution_handoff,
                    "blocked_count",
                ),
                "warning_count": len(execution_handoff.get("warning_check_ids") or []) + self._summary_int(
                    execution_handoff,
                    "awaiting_external_signoff_count",
                ),
                "configuration_written": bool(summary.get("configuration_written")),
                "approval_record_written": bool(summary.get("approval_record_written")),
                "signoff_record_written": bool(summary.get("signoff_record_written")),
                "rollback_executed": bool(summary.get("rollback_executed")),
                "gateway_called": bool(summary.get("gateway_called")),
                "network_called": bool(summary.get("network_called")),
                "raw_payload_echoed": bool(summary.get("raw_payload_echoed")),
                "raw_model_output_returned": bool(summary.get("raw_model_output_returned")),
            }
        ]

    def _checks(
        self,
        execution_handoff: dict[str, Any],
        observation_rows: list[dict[str, Any]],
        rollback_window_rows: list[dict[str, Any]],
        raw_input_field_count: int,
    ) -> list[dict[str, Any]]:
        observation_ready_rows = [
            row for row in observation_rows if row["observation_gate_status"] == "observation_ready"
        ]
        rollback_clear_rows = [row for row in rollback_window_rows if row["rollback_window_status"] == "clear"]
        rollback_required_rows = [
            row for row in observation_rows if row["observation_gate_status"] == "rollback_required"
        ]
        all_ready = bool(observation_rows) and len(observation_ready_rows) == len(observation_rows)
        return [
            {
                "id": "default-promotion-execution-handoff-attached-not-blocked",
                "source_key": "legal_benchmark_default_promotion_execution_handoff",
                "status": "fail" if not execution_handoff or self._is_blocked(execution_handoff) else "pass",
                "source_status": self._status_text(execution_handoff),
                "decision_effect": "blocks_observation_review"
                if not execution_handoff or self._is_blocked(execution_handoff)
                else "allows_observation_review",
                "reason": "Legal benchmark default-promotion execution handoff is missing or blocked."
                if not execution_handoff or self._is_blocked(execution_handoff)
                else "Execution handoff is attached and not blocked.",
                "source_blocking_ids": self._string_list(execution_handoff.get("blocking_check_ids")),
                "source_warning_ids": self._string_list(execution_handoff.get("warning_check_ids")),
            },
            {
                "id": "observation-rows-generated",
                "source_key": "legal_benchmark_default_promotion_observation_gate",
                "status": "pass" if observation_rows else "warn",
                "source_status": "mapped" if observation_rows else "not_run",
                "decision_effect": "requires_observation_review" if observation_rows else "requires_execution_handoff_rows",
                "reason": "Execution handoff rows were converted into observation rows."
                if observation_rows
                else "No execution handoff rows are available for observation review.",
                "source_blocking_ids": [],
                "source_warning_ids": [] if observation_rows else ["observation-rows-not-generated"],
            },
            {
                "id": "post-change-observation-attached",
                "source_key": "legal_benchmark_default_promotion_observation_gate",
                "status": "pass" if all_ready else "warn",
                "source_status": "ready" if all_ready else "not_attached",
                "decision_effect": "allows_external_observation_acceptance" if all_ready else "requires_observation_evidence",
                "reason": "Every observation row has route telemetry, legal benchmark smoke, rollback window, and incident metadata."
                if all_ready
                else "Route telemetry, legal benchmark smoke, rollback window, or incident metadata is missing.",
                "source_blocking_ids": [],
                "source_warning_ids": [] if all_ready else ["post-change-observation-evidence-incomplete"],
            },
            {
                "id": "rollback-window-clear",
                "source_key": "legal_benchmark_default_promotion_observation_gate",
                "status": "fail" if rollback_required_rows else "pass" if rollback_window_rows and len(rollback_clear_rows) == len(rollback_window_rows) else "warn",
                "source_status": "rollback_required" if rollback_required_rows else "clear" if rollback_window_rows and len(rollback_clear_rows) == len(rollback_window_rows) else "not_clear",
                "decision_effect": "requires_external_rollback_review"
                if rollback_required_rows
                else "supports_observation_acceptance"
                if rollback_window_rows and len(rollback_clear_rows) == len(rollback_window_rows)
                else "requires_rollback_window_evidence",
                "reason": "Observation metadata indicates incident or rollback-required state."
                if rollback_required_rows
                else "Rollback window is clear for every observation row."
                if rollback_window_rows and len(rollback_clear_rows) == len(rollback_window_rows)
                else "Rollback window metadata must be clear before observation acceptance.",
                "source_blocking_ids": [row["id"] for row in rollback_required_rows],
                "source_warning_ids": []
                if rollback_window_rows and len(rollback_clear_rows) == len(rollback_window_rows)
                else ["rollback-window-not-clear"],
            },
            {
                "id": "no-observation-side-effects",
                "source_key": "legal_benchmark_default_promotion_observation_gate",
                "status": "pass",
                "source_status": "metadata_only",
                "decision_effect": "keeps_observation_external",
                "reason": "The gate does not call providers, write records, change config, execute rollback, or shift traffic.",
                "source_blocking_ids": [],
                "source_warning_ids": [],
            },
            {
                "id": "metadata-only-boundary",
                "source_key": "legal_benchmark_default_promotion_observation_gate",
                "status": "warn" if raw_input_field_count else "pass",
                "source_status": "metadata_only",
                "decision_effect": "requires_payload_sanitization" if raw_input_field_count else "allows_observation_review",
                "reason": f"Forbidden raw/sensitive input field count is {raw_input_field_count}; raw values are not echoed.",
                "source_blocking_ids": [],
                "source_warning_ids": ["raw-input-field-detected"] if raw_input_field_count else [],
            },
        ]

    def _observation_gate_status(
        self,
        *,
        execution_status: str,
        post_change_observation_status: str,
        route_telemetry_status: str,
        legal_benchmark_smoke_status: str,
        rollback_window_status: str,
        incident_status: str,
        execution_handoff: dict[str, Any],
    ) -> str:
        if self._is_blocked(execution_handoff) or execution_status == "blocked":
            return "blocked"
        if execution_status not in {"ready_for_external_execution", "externally_executed"}:
            return "not_run"
        if incident_status in INCIDENT_STATUSES or rollback_window_status == "rollback_required":
            return "rollback_required"
        if (
            post_change_observation_status in READY_STATUSES
            and route_telemetry_status in READY_STATUSES
            and legal_benchmark_smoke_status in READY_STATUSES
            and rollback_window_status in {"clear", "ready", "closed"}
            and incident_status in {"none", "clear", "no_incident", "ready"}
        ):
            return "observation_ready"
        return "review_required"

    def _observation_checks(self, gate_status: str) -> list[str]:
        if gate_status == "observation_ready":
            return [
                "confirm-route-telemetry-watch-clear",
                "confirm-legal-benchmark-smoke-pass",
                "confirm-rollback-window-clear",
                "archive-observation-summary-outside-this-service",
            ]
        if gate_status == "rollback_required":
            return [
                "escalate-external-rollback-review",
                "keep-current-legal-default-under-review",
                "attach-incident-triage-summary",
            ]
        if gate_status == "blocked":
            return [
                "resolve-execution-handoff-blockers",
                "do-not-accept-post-change-observation",
            ]
        if gate_status == "not_run":
            return [
                "attach-ready-execution-handoff-row",
                "attach-external-execution-reference",
            ]
        return [
            "attach-route-telemetry-observation",
            "attach-legal-benchmark-smoke-result",
            "attach-rollback-window-status",
            "attach-incident-status",
        ]

    def _rollback_window_checks(self, gate_status: str) -> list[str]:
        if gate_status == "observation_ready":
            return [
                "rollback-window-clear",
                "rollback-owner-available",
                "previous-default-restorable",
            ]
        if gate_status == "rollback_required":
            return [
                "rollback-review-required",
                "incident-triage-required",
                "default-change-hold-required",
            ]
        return [
            "rollback-window-evidence-required",
            "rollback-owner-confirmation-required",
            "previous-default-reference-required",
        ]

    def _derived_reason_codes(
        self,
        *,
        gate_status: str,
        post_change_observation_status: str,
        route_telemetry_status: str,
        legal_benchmark_smoke_status: str,
        rollback_window_status: str,
        incident_status: str,
    ) -> list[str]:
        codes: list[str] = []
        if gate_status == "blocked":
            codes.append("execution-handoff-blocked")
        if gate_status == "not_run":
            codes.append("execution-handoff-not-ready")
        if gate_status == "review_required":
            codes.append("post-change-observation-review-required")
        if gate_status == "rollback_required":
            codes.append("rollback-review-required")
        if post_change_observation_status not in READY_STATUSES:
            codes.append("post-change-observation-missing")
        if route_telemetry_status not in READY_STATUSES:
            codes.append("route-telemetry-observation-missing")
        if legal_benchmark_smoke_status not in READY_STATUSES:
            codes.append("legal-benchmark-smoke-missing")
        if rollback_window_status not in {"clear", "ready", "closed"}:
            codes.append("rollback-window-not-clear")
        if incident_status not in {"none", "clear", "no_incident", "ready"}:
            codes.append("incident-status-review-required")
        return codes

    def _observation_action(self, gate_status: str, row: dict[str, Any]) -> str:
        task = self._safe_text(row.get("task"), "unknown")
        model_id = self._safe_text(row.get("proposed_default_model"), "the model")
        if gate_status == "observation_ready":
            return f"Accept external observation evidence for {task} default change to {model_id}; keep audit record outside this service."
        if gate_status == "rollback_required":
            return f"Escalate external rollback review for {task} default change to {model_id}; do not claim stable default quality."
        if gate_status == "blocked":
            return f"Do not observe {task} default change to {model_id}; resolve execution handoff blockers first."
        if gate_status == "not_run":
            return f"Attach ready execution handoff evidence before observing {task} default change."
        return f"Collect route telemetry, legal benchmark smoke, rollback-window, and incident metadata for {task}."

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        observation_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [f"Resolve observation gate blocker: {check['id']}." for check in blocking[:5]]
        actions = [
            "Keep post-change quality claims disabled until external observation evidence is attached.",
            "Archive route telemetry, smoke result, rollback-window, and incident-status references outside this service.",
        ]
        if warnings:
            actions.append("Review observation warnings: " + ", ".join(check["id"] for check in warnings[:5]) + ".")
        if not observation_rows:
            actions.append("Attach execution handoff rows before using this observation gate.")
        return actions[:6]

    def _source_dict(self, data: dict[str, Any], *keys: str) -> dict[str, Any]:
        for key in keys:
            value = data.get(key)
            if isinstance(value, dict):
                return value
        return {}

    def _summary(self, value: dict[str, Any]) -> dict[str, Any]:
        summary = value.get("summary")
        return summary if isinstance(summary, dict) else {}

    def _summary_int(self, value: dict[str, Any], key: str) -> int:
        raw = self._summary(value).get(key)
        if isinstance(raw, bool):
            return 0
        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            return 0

    def _status_text(self, value: dict[str, Any]) -> str:
        return self._safe_text(value.get("status"), "not_supplied").lower().replace(" ", "_")

    def _is_blocked(self, source: dict[str, Any]) -> bool:
        if not source:
            return False
        status = self._status_text(source)
        return (
            status in FAIL_STATUSES
            or bool(source.get("blocking_check_ids"))
            or bool(source.get("blocking_item_ids"))
            or self._summary_int(source, "blocked_count") > 0
            or self._summary_int(source, "rollback_required_count") > 0
        )

    def _list_of_dicts(self, value: Any) -> list[dict[str, Any]]:
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [text for text in (self._safe_text(item, "") for item in value) if text]

    def _safe_text(self, value: Any, fallback: str) -> str:
        text = str(value or "").strip()
        if not text:
            return fallback
        if SENSITIVE_PATTERN.search(text):
            return "redacted-sensitive-value"
        return text[:180]

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    def _raw_input_field_count(self, value: Any) -> int:
        if isinstance(value, dict):
            count = 0
            for key, child in value.items():
                key_text = str(key).strip().lower()
                if key_text in RAW_INPUT_FIELD_NAMES:
                    count += 1
                    continue
                count += self._raw_input_field_count(child)
            return count
        if isinstance(value, list):
            return sum(self._raw_input_field_count(item) for item in value[:50])
        if isinstance(value, str) and SENSITIVE_PATTERN.search(value):
            return 1
        return 0
