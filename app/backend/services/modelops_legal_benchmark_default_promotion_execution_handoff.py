from __future__ import annotations

import re
from typing import Any

from services.modelops_legal_benchmark_default_promotion_signoff_packet import (
    ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService,
)


RAW_INPUT_FIELD_NAMES = {
    "api_key",
    "approval_record",
    "authorization",
    "candidate_text",
    "client_email",
    "config_diff",
    "content",
    "document_text",
    "execution_payload",
    "fixture_text",
    "generated_text",
    "headers",
    "identity",
    "messages",
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
FAIL_STATUSES = {"blocked", "fail", "failed", "error"}
SIGNED_STATUSES = {"approved", "attached", "recorded", "signed"}
READY_STATUSES = {"pass", "ready", "ready_for_external_execution", "ok", "success"}


class ModelOpsLegalBenchmarkDefaultPromotionExecutionHandoffService:
    """Build a metadata-only execution handoff for externally signed legal benchmark default changes."""

    def __init__(
        self,
        signoff_service: ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService | None = None,
    ) -> None:
        self.signoff_service = signoff_service or ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService()

    def build_handoff(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        signoff_packet = self._source_dict(
            data,
            "legal_benchmark_default_promotion_signoff_packet",
            "default_promotion_signoff_packet",
            "signoff_packet",
        )
        if not signoff_packet:
            signoff_packet = self.signoff_service.build_packet(data or None)

        raw_input_field_count = self._raw_input_field_count(data)
        signoff_items = self._list_of_dicts(signoff_packet.get("signoff_items"))
        handoff_rows = [self._handoff_row(index, row, signoff_packet) for index, row in enumerate(signoff_items, start=1)]
        source_status_rows = self._source_status_rows(signoff_packet)
        rollback_gate_items = [self._rollback_gate_item(row) for row in handoff_rows]
        checks = self._checks(signoff_packet, handoff_rows, raw_input_field_count)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        ready_rows = [row for row in handoff_rows if row["execution_status"] == "ready_for_external_execution"]
        awaiting_rows = [row for row in handoff_rows if row["execution_status"] == "awaiting_external_signoff"]
        blocked_rows = [row for row in handoff_rows if row["execution_status"] == "blocked"]
        not_run_rows = [row for row in handoff_rows if row["execution_status"] == "not_run"]
        rollback_ready_rows = [row for row in handoff_rows if row["rollback_plan_status"] == "ready"]
        status = (
            "blocked"
            if blocking or blocked_rows
            else "ready_for_external_execution"
            if handoff_rows and len(ready_rows) == len(handoff_rows) and not warnings
            else "review_required"
        )

        return {
            "id": "modelops-legal-benchmark-default-promotion-execution-handoff",
            "title": "ModelOps legal benchmark default-promotion execution handoff",
            "status": status,
            "execution_policy": {
                "execution_handoff_required": True,
                "external_signoff_required": True,
                "rollback_plan_required": True,
                "config_diff_review_required": True,
                "post_change_observation_required": True,
                "rollback_execution_allowed": False,
                "configuration_change_allowed": False,
                "env_file_write_allowed": False,
                "approval_record_write_allowed": False,
                "signoff_record_write_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "requires_signoff_packet_not_blocked": True,
                "requires_metadata_only_boundary": True,
            },
            "decision": {
                "status": status,
                "execution_handoff_ready": status == "ready_for_external_execution",
                "default_change_allowed_by_execution_handoff": False,
                "configuration_change_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "rollback_execution_allowed": False,
                "release_action": "block_default_promotion"
                if status == "blocked"
                else "handoff_to_external_maintainer_execution"
                if status == "ready_for_external_execution"
                else "collect_signoff_and_rollback_evidence",
            },
            "method": {
                "type": "metadata-only-legal-benchmark-default-promotion-execution-handoff",
                "notes": [
                    "Consumes the legal benchmark default-promotion signoff packet after checklist rows are mapped to external signoff requirements.",
                    "Packages execution prerequisites, rollback checks, and post-change observation requirements only.",
                    "Does not write config, env files, approval records, or signoff records, and does not shift traffic.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, public datasets, or the network.",
                ],
            },
            "summary": {
                "source_count": len(source_status_rows),
                "handoff_row_count": len(handoff_rows),
                "ready_for_external_execution_count": len(ready_rows),
                "awaiting_external_signoff_count": len(awaiting_rows),
                "blocked_count": len(blocked_rows),
                "not_run_count": len(not_run_rows),
                "rollback_ready_count": len(rollback_ready_rows),
                "signoff_packet_status": self._status_text(signoff_packet),
                "signoff_item_count": self._summary_int(signoff_packet, "signoff_item_count") or len(signoff_items),
                "signoff_ready_count": self._summary_int(signoff_packet, "ready_for_signoff_count"),
                "signoff_blocked_count": self._summary_int(signoff_packet, "blocked_count"),
                "raw_input_field_count": raw_input_field_count,
                "default_change_allowed_by_execution_handoff": False,
                "rollback_execution_allowed": False,
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
            "handoff_rows": handoff_rows,
            "rollback_gate_items": rollback_gate_items,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "required_execution_roles": [
                "model_ops_maintainer",
                "legal_quality_owner",
                "release_owner",
                "rollback_owner",
            ],
            "source_links": {
                "legal_benchmark_default_promotion_signoff_packet": "/api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet",
                "legal_benchmark_default_promotion_execution_handoff": "/api/v1/aihub/models/legal-benchmark-default-promotion-execution-handoff",
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, handoff_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_model_ids": True,
                "returns_execution_roles": True,
                "returns_rollback_check_ids": True,
                "approver_identity_included": False,
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
                "output_scope": "signoff item ids, fixture ids, model ids, execution roles, rollback check ids, source statuses, counts, and review actions only",
            },
            "claim_boundary": {
                "maintainer_approval_claimed": False,
                "signoff_record_claimed": False,
                "automatic_default_change_claimed": False,
                "configuration_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "traffic_shift_claimed": False,
                "rollback_execution_claimed": False,
                "public_benchmark_scores_claimed": False,
                "production_legal_quality_claimed": False,
                "legal_advice_claimed": False,
                "allowed_claim": "Metadata-only legal benchmark default-promotion execution handoff requirements are packaged for external maintainer execution review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_benchmark_default_promotion_execution_handoff.py tests/test_modelops_legal_benchmark_default_promotion_signoff_packet.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _rollback_gate_item(self, row: dict[str, Any]) -> dict[str, Any]:
        status = "ready" if row["rollback_plan_status"] == "ready" else "review_required"
        if row["execution_status"] == "blocked":
            status = "blocked"
        return {
            "id": f"{row['id']}-rollback-gate",
            "source_handoff_row_id": row["id"],
            "fixture_id": row["fixture_id"],
            "task": row["task"],
            "proposed_default_model": row["proposed_default_model"],
            "rollback_gate_status": status,
            "rollback_plan_status": row["rollback_plan_status"],
            "rollback_owner_role": row["rollback_owner_role"],
            "rollback_checks": row["rollback_checks"],
            "rollback_execution_allowed": False,
            "rollback_executed": False,
            "traffic_shift_allowed": False,
            "configuration_change_allowed": False,
        }

    def _handoff_row(self, index: int, item: dict[str, Any], signoff_packet: dict[str, Any]) -> dict[str, Any]:
        signoff_status = self._safe_text(item.get("signoff_status"), "not_run")
        external_signoff_status = self._safe_text(item.get("external_signoff_status"), "not_attached")
        rollback_plan_status = self._safe_text(item.get("rollback_plan_status"), "not_attached")
        config_diff_status = self._safe_text(item.get("config_diff_status"), "not_attached")
        observation_plan_status = self._safe_text(item.get("observation_plan_status"), "not_attached")
        execution_status = self._execution_status(
            signoff_status=signoff_status,
            external_signoff_status=external_signoff_status,
            rollback_plan_status=rollback_plan_status,
            config_diff_status=config_diff_status,
            observation_plan_status=observation_plan_status,
            signoff_packet=signoff_packet,
        )
        reason_codes = self._dedupe(
            [
                *self._string_list(item.get("reason_codes")),
                *self._derived_reason_codes(
                    execution_status=execution_status,
                    external_signoff_status=external_signoff_status,
                    rollback_plan_status=rollback_plan_status,
                    config_diff_status=config_diff_status,
                    observation_plan_status=observation_plan_status,
                ),
            ]
        )
        return {
            "id": f"legal-benchmark-default-promotion-execution-handoff-{index}",
            "source_signoff_item_id": self._safe_text(item.get("id"), f"signoff-item-{index}"),
            "source_checklist_row_id": self._safe_text(item.get("source_checklist_row_id"), f"checklist-row-{index}"),
            "requirement_id": self._safe_text(item.get("requirement_id"), f"requirement-{index}"),
            "fixture_id": self._safe_text(item.get("fixture_id"), "unknown"),
            "task": self._safe_text(item.get("task"), "unknown"),
            "proposed_default_model": self._safe_text(item.get("proposed_default_model"), "unknown"),
            "model_cost_tier": self._safe_text(item.get("model_cost_tier"), "unknown"),
            "signoff_status": signoff_status,
            "external_signoff_status": external_signoff_status,
            "rollback_plan_status": rollback_plan_status,
            "config_diff_status": config_diff_status,
            "observation_plan_status": observation_plan_status,
            "execution_status": execution_status,
            "required_execution_steps": self._required_execution_steps(execution_status),
            "rollback_checks": self._rollback_checks(execution_status),
            "blocking_reason_codes": [] if execution_status == "ready_for_external_execution" else reason_codes,
            "reason_codes": reason_codes,
            "rollback_owner_role": "rollback_owner",
            "configuration_change_allowed": False,
            "env_file_write_allowed": False,
            "approval_record_write_allowed": False,
            "signoff_record_write_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
            "default_change_allowed_by_execution_handoff": False,
            "execution_action": self._execution_action(execution_status, item),
        }

    def _source_status_rows(self, signoff_packet: dict[str, Any]) -> list[dict[str, Any]]:
        summary = self._summary(signoff_packet)
        return [
            {
                "id": "legal-benchmark-default-promotion-signoff-packet",
                "label": "Legal benchmark default-promotion signoff packet",
                "source_key": "legal_benchmark_default_promotion_signoff_packet",
                "source_status": self._status_text(signoff_packet),
                "execution_status": "blocked" if self._is_blocked(signoff_packet) else "review_required",
                "row_count": self._summary_int(signoff_packet, "signoff_item_count"),
                "blocking_count": len(signoff_packet.get("blocking_check_ids") or []) + self._summary_int(
                    signoff_packet,
                    "blocked_count",
                ),
                "warning_count": len(signoff_packet.get("warning_check_ids") or []) + self._summary_int(
                    signoff_packet,
                    "review_required_count",
                ),
                "configuration_written": bool(summary.get("configuration_written")),
                "approval_record_written": bool(summary.get("approval_record_written")),
                "signoff_record_written": bool(summary.get("signoff_record_written")),
                "gateway_called": bool(summary.get("gateway_called")),
                "network_called": bool(summary.get("network_called")),
                "raw_payload_echoed": bool(summary.get("raw_payload_echoed")),
                "raw_model_output_returned": bool(summary.get("raw_model_output_returned")),
            }
        ]

    def _checks(
        self,
        signoff_packet: dict[str, Any],
        handoff_rows: list[dict[str, Any]],
        raw_input_field_count: int,
    ) -> list[dict[str, Any]]:
        ready_rows = [row for row in handoff_rows if row["execution_status"] == "ready_for_external_execution"]
        rollback_ready_rows = [row for row in handoff_rows if row["rollback_plan_status"] == "ready"]
        all_ready = bool(handoff_rows) and len(ready_rows) == len(handoff_rows)
        return [
            {
                "id": "default-promotion-signoff-packet-attached-not-blocked",
                "source_key": "legal_benchmark_default_promotion_signoff_packet",
                "status": "fail" if not signoff_packet or self._is_blocked(signoff_packet) else "pass",
                "source_status": self._status_text(signoff_packet),
                "decision_effect": "blocks_default_promotion"
                if not signoff_packet or self._is_blocked(signoff_packet)
                else "allows_execution_handoff_review",
                "reason": "Legal benchmark default-promotion signoff packet is missing or blocked."
                if not signoff_packet or self._is_blocked(signoff_packet)
                else "Signoff packet is attached and not blocked.",
                "source_blocking_ids": self._string_list(signoff_packet.get("blocking_check_ids")),
                "source_warning_ids": self._string_list(signoff_packet.get("warning_check_ids")),
            },
            {
                "id": "execution-handoff-rows-generated",
                "source_key": "legal_benchmark_default_promotion_execution_handoff",
                "status": "pass" if handoff_rows else "warn",
                "source_status": "mapped" if handoff_rows else "not_run",
                "decision_effect": "requires_external_execution_review" if handoff_rows else "requires_signoff_items",
                "reason": "Signoff items were converted into execution handoff rows."
                if handoff_rows
                else "No signoff items are available for execution handoff.",
                "source_blocking_ids": [],
                "source_warning_ids": [] if handoff_rows else ["execution-handoff-rows-not-generated"],
            },
            {
                "id": "external-signoff-record-attached",
                "source_key": "legal_benchmark_default_promotion_execution_handoff",
                "status": "pass" if all_ready else "warn",
                "source_status": "ready" if all_ready else "not_attached",
                "decision_effect": "allows_external_execution_handoff" if all_ready else "requires_external_signoff_record",
                "reason": "Every handoff row has external signoff, rollback, config diff, and observation metadata."
                if all_ready
                else "External signoff, rollback, config diff, or observation metadata is still missing.",
                "source_blocking_ids": [],
                "source_warning_ids": [] if all_ready else ["external-execution-evidence-incomplete"],
            },
            {
                "id": "rollback-plan-ready",
                "source_key": "legal_benchmark_default_promotion_execution_handoff",
                "status": "pass" if handoff_rows and len(rollback_ready_rows) == len(handoff_rows) else "warn",
                "source_status": "ready" if handoff_rows and len(rollback_ready_rows) == len(handoff_rows) else "not_attached",
                "decision_effect": "supports_external_rollback_review"
                if handoff_rows and len(rollback_ready_rows) == len(handoff_rows)
                else "requires_rollback_plan",
                "reason": "Rollback plan metadata is attached for every handoff row."
                if handoff_rows and len(rollback_ready_rows) == len(handoff_rows)
                else "Attach rollback plan metadata before external default-promotion execution.",
                "source_blocking_ids": [],
                "source_warning_ids": []
                if handoff_rows and len(rollback_ready_rows) == len(handoff_rows)
                else ["rollback-plan-not-ready"],
            },
            {
                "id": "no-execution-side-effects",
                "source_key": "legal_benchmark_default_promotion_execution_handoff",
                "status": "pass",
                "source_status": "metadata_only",
                "decision_effect": "keeps_execution_external",
                "reason": "The handoff does not write configuration, records, env files, call gateways, or shift traffic.",
                "source_blocking_ids": [],
                "source_warning_ids": [],
            },
            {
                "id": "metadata-only-boundary",
                "source_key": "legal_benchmark_default_promotion_execution_handoff",
                "status": "warn" if raw_input_field_count else "pass",
                "source_status": "metadata_only",
                "decision_effect": "requires_payload_sanitization" if raw_input_field_count else "allows_external_execution_review",
                "reason": f"Forbidden raw/sensitive input field count is {raw_input_field_count}; raw values are not echoed.",
                "source_blocking_ids": [],
                "source_warning_ids": ["raw-input-field-detected"] if raw_input_field_count else [],
            },
        ]

    def _execution_status(
        self,
        *,
        signoff_status: str,
        external_signoff_status: str,
        rollback_plan_status: str,
        config_diff_status: str,
        observation_plan_status: str,
        signoff_packet: dict[str, Any],
    ) -> str:
        if self._is_blocked(signoff_packet) or signoff_status == "blocked":
            return "blocked"
        if signoff_status in {"not_run", "not_ready", "not_supplied"}:
            return "not_run"
        if (
            external_signoff_status in SIGNED_STATUSES
            and rollback_plan_status in READY_STATUSES
            and config_diff_status in {"reviewed", "ready", "approved"}
            and observation_plan_status in READY_STATUSES
        ):
            return "ready_for_external_execution"
        return "awaiting_external_signoff"

    def _required_execution_steps(self, execution_status: str) -> list[str]:
        if execution_status == "ready_for_external_execution":
            return [
                "confirm-external-signoff-record-reference",
                "apply-config-change-outside-this-service",
                "observe-legal-benchmark-route-after-change",
                "keep-rollback-window-open",
            ]
        if execution_status == "blocked":
            return [
                "resolve-signoff-packet-blockers",
                "keep-current-legal-default",
                "rerun-execution-handoff-after-signoff-clears",
            ]
        if execution_status == "not_run":
            return [
                "attach-signoff-packet-item",
                "collect-external-signoff-record",
                "attach-rollback-plan-metadata",
            ]
        return [
            "collect-external-signoff-record",
            "attach-config-diff-review",
            "attach-rollback-plan-metadata",
            "attach-post-change-observation-plan",
        ]

    def _rollback_checks(self, execution_status: str) -> list[str]:
        if execution_status == "ready_for_external_execution":
            return [
                "previous-default-model-recorded",
                "rollback-owner-assigned",
                "route-telemetry-watch-ready",
                "legal-benchmark-smoke-rerun-ready",
            ]
        if execution_status == "blocked":
            return ["rollback-blocked-until-signoff-packet-clears"]
        return [
            "previous-default-model-required",
            "rollback-owner-required",
            "route-telemetry-watch-required",
            "legal-benchmark-smoke-rerun-required",
        ]

    def _derived_reason_codes(
        self,
        *,
        execution_status: str,
        external_signoff_status: str,
        rollback_plan_status: str,
        config_diff_status: str,
        observation_plan_status: str,
    ) -> list[str]:
        codes: list[str] = []
        if execution_status == "blocked":
            codes.append("signoff-packet-blocked")
        if execution_status == "not_run":
            codes.append("signoff-item-not-ready")
        if execution_status == "awaiting_external_signoff":
            codes.append("external-execution-evidence-required")
        if external_signoff_status not in SIGNED_STATUSES:
            codes.append("external-signoff-record-missing")
        if rollback_plan_status not in READY_STATUSES:
            codes.append("rollback-plan-missing")
        if config_diff_status not in {"reviewed", "ready", "approved"}:
            codes.append("config-diff-review-missing")
        if observation_plan_status not in READY_STATUSES:
            codes.append("post-change-observation-plan-missing")
        return codes

    def _execution_action(self, execution_status: str, item: dict[str, Any]) -> str:
        task = self._safe_text(item.get("task"), "unknown")
        model_id = self._safe_text(item.get("proposed_default_model"), "the model")
        if execution_status == "ready_for_external_execution":
            return f"Handoff {task} default change to {model_id} for external maintainer execution with rollback watch."
        if execution_status == "blocked":
            return f"Do not execute {task} default change to {model_id}; resolve signoff blockers first."
        if execution_status == "not_run":
            return f"Attach signoff packet evidence before preparing {task} execution handoff."
        return f"Collect external signoff, rollback, config diff, and observation metadata before {task} execution handoff."

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        handoff_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [f"Resolve execution handoff blocker: {check['id']}." for check in blocking[:5]]
        actions = [
            "Keep legal-task defaults unchanged until external signoff and rollback evidence are attached.",
            "Use this handoff as release evidence only; execute configuration work outside this service.",
        ]
        if warnings:
            actions.append("Review execution handoff warnings: " + ", ".join(check["id"] for check in warnings[:5]) + ".")
        if not handoff_rows:
            actions.append("Attach signoff packet rows before preparing execution handoff.")
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
            or self._summary_int(source, "blocking_signal_count") > 0
            or self._summary_int(source, "blocked_change_count") > 0
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
