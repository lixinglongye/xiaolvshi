from __future__ import annotations

import re
from typing import Any

from services.modelops_legal_benchmark_default_promotion_checklist import (
    ModelOpsLegalBenchmarkDefaultPromotionChecklistService,
)


RAW_INPUT_FIELD_NAMES = {
    "api_key",
    "authorization",
    "candidate_text",
    "content",
    "document_text",
    "fixture_text",
    "generated_text",
    "headers",
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
    r"sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._\-]{16,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b|password|secret",
    re.IGNORECASE,
)
FAIL_STATUSES = {"blocked", "fail", "failed", "error"}
READY_STATUSES = {"pass", "ready", "ok", "success"}
REVIEW_STATUSES = {
    "not_ready",
    "not_run",
    "not_supplied",
    "review_required",
    "review_recommended",
    "ready_for_maintainer_review",
    "warn",
    "warning",
}


class ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService:
    """Build a metadata-only signoff packet for legal benchmark default-promotion review."""

    def __init__(
        self,
        checklist_service: ModelOpsLegalBenchmarkDefaultPromotionChecklistService | None = None,
    ) -> None:
        self.checklist_service = checklist_service or ModelOpsLegalBenchmarkDefaultPromotionChecklistService()

    def build_packet(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        checklist = self._source_dict(
            data,
            "legal_benchmark_default_promotion_checklist",
            "default_promotion_checklist",
            "checklist",
        )
        if not checklist:
            checklist = self.checklist_service.build_checklist(data or None)

        raw_input_field_count = self._raw_input_field_count(data)
        checklist_rows = self._list_of_dicts(checklist.get("checklist_rows"))
        signoff_items = [self._signoff_item(index, row, checklist) for index, row in enumerate(checklist_rows, start=1)]
        source_status_rows = self._source_status_rows(checklist)
        checks = self._checks(checklist, signoff_items, raw_input_field_count)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        ready_items = [item for item in signoff_items if item["signoff_status"] == "ready_for_signoff"]
        review_items = [item for item in signoff_items if item["signoff_status"] == "review_required"]
        blocked_items = [item for item in signoff_items if item["signoff_status"] == "blocked"]
        not_run_items = [item for item in signoff_items if item["signoff_status"] == "not_run"]
        status = "blocked" if blocking or blocked_items else "review_required"

        return {
            "id": "modelops-legal-benchmark-default-promotion-signoff-packet",
            "title": "ModelOps legal benchmark default-promotion signoff packet",
            "status": status,
            "signoff_policy": {
                "signoff_required": True,
                "signoff_record_written": False,
                "approver_identity_collected": False,
                "configuration_change_allowed": False,
                "env_file_write_allowed": False,
                "approval_record_write_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "requires_checklist_not_blocked": True,
                "requires_model_ops_maintainer": True,
                "requires_legal_quality_owner": True,
                "requires_release_owner": True,
                "requires_metadata_only_boundary": True,
            },
            "decision": {
                "status": status,
                "default_change_allowed_by_signoff_packet": False,
                "configuration_change_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "maintainer_review_required": True,
                "signoff_release_action": "block_default_promotion"
                if status == "blocked"
                else "collect_external_signoff",
            },
            "method": {
                "type": "metadata-only-legal-benchmark-default-promotion-signoff-packet",
                "notes": [
                    "Consumes the legal benchmark default-promotion checklist after bridge, release decision, and default-change queue evidence are attached.",
                    "Returns signoff requirements and pre-signoff checks only; it does not claim approval or collect approver identity.",
                    "Keeps signoff review downstream of checklist evidence and outside automatic default-change execution.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, public datasets, or the network.",
                ],
            },
            "summary": {
                "source_count": len(source_status_rows),
                "signoff_item_count": len(signoff_items),
                "ready_for_signoff_count": len(ready_items),
                "review_required_count": len(review_items),
                "blocked_count": len(blocked_items),
                "not_run_count": len(not_run_items),
                "required_signoff_count": sum(len(item["required_signoffs"]) for item in signoff_items),
                "recorded_signoff_count": 0,
                "checklist_status": self._status_text(checklist),
                "checklist_row_count": self._summary_int(checklist, "checklist_row_count") or len(checklist_rows),
                "checklist_blocked_count": self._summary_int(checklist, "blocked_count"),
                "checklist_review_required_count": self._summary_int(checklist, "review_required_count"),
                "raw_input_field_count": raw_input_field_count,
                "default_change_allowed_by_signoff_packet": False,
                "configuration_written": False,
                "env_file_written": False,
                "approval_record_written": False,
                "signoff_record_written": False,
                "approver_identity_collected": False,
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
            "signoff_items": signoff_items,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "required_signoffs": [
                "model_ops_maintainer",
                "legal_quality_owner",
                "release_owner",
            ],
            "source_links": {
                "legal_benchmark_default_promotion_checklist": "/api/v1/aihub/models/legal-benchmark-default-promotion-checklist",
                "legal_benchmark_default_promotion_signoff_packet": "/api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet",
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, signoff_items),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_model_ids": True,
                "returns_signoff_roles": True,
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
                "output_scope": "checklist row ids, fixture ids, model ids, signoff roles, pre-signoff checks, check ids, counts, and review actions only",
            },
            "claim_boundary": {
                "maintainer_approval_claimed": False,
                "signoff_record_claimed": False,
                "automatic_default_change_claimed": False,
                "configuration_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_scores_claimed": False,
                "production_legal_quality_claimed": False,
                "legal_advice_claimed": False,
                "allowed_claim": "Metadata-only legal benchmark default-promotion signoff requirements are packaged for external maintainer review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_benchmark_default_promotion_signoff_packet.py tests/test_modelops_legal_benchmark_default_promotion_checklist.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _signoff_item(self, index: int, row: dict[str, Any], checklist: dict[str, Any]) -> dict[str, Any]:
        checklist_status = self._safe_text(row.get("checklist_status"), "not_run")
        signoff_status = self._signoff_status(row, checklist)
        required_signoffs = self._required_signoffs(signoff_status, row)
        reason_codes = self._dedupe(
            [
                *self._string_list(row.get("reason_codes")),
                *self._derived_reason_codes(signoff_status=signoff_status, checklist_status=checklist_status),
            ]
        )
        return {
            "id": f"legal-benchmark-default-promotion-signoff-{index}",
            "source_checklist_row_id": self._safe_text(row.get("id"), f"checklist-row-{index}"),
            "requirement_id": self._safe_text(row.get("requirement_id"), f"requirement-{index}"),
            "fixture_id": self._safe_text(row.get("fixture_id"), "unknown"),
            "task": self._safe_text(row.get("task"), "unknown"),
            "proposed_default_model": self._safe_text(row.get("proposed_default_model"), "unknown"),
            "model_cost_tier": self._safe_text(row.get("model_cost_tier"), "unknown"),
            "checklist_status": checklist_status,
            "signoff_status": signoff_status,
            "required_signoffs": required_signoffs,
            "pre_signoff_checks": self._pre_signoff_checks(signoff_status),
            "blocking_reason_codes": [] if signoff_status == "ready_for_signoff" else reason_codes,
            "reason_codes": reason_codes,
            "signoff_record_written": False,
            "approver_identity_collected": False,
            "configuration_change_allowed": False,
            "env_file_write_allowed": False,
            "approval_record_write_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
            "default_change_allowed_by_signoff_packet": False,
            "release_action": self._item_action(signoff_status, row),
        }

    def _source_status_rows(self, checklist: dict[str, Any]) -> list[dict[str, Any]]:
        summary = self._summary(checklist)
        return [
            {
                "id": "legal-benchmark-default-promotion-checklist",
                "label": "Legal benchmark default-promotion checklist",
                "source_key": "legal_benchmark_default_promotion_checklist",
                "source_status": self._status_text(checklist),
                "signoff_status": "blocked" if self._is_blocked(checklist) else "review_required",
                "row_count": self._summary_int(checklist, "checklist_row_count"),
                "blocking_count": len(checklist.get("blocking_check_ids") or []) + self._summary_int(checklist, "blocked_count"),
                "warning_count": len(checklist.get("warning_check_ids") or []) + self._summary_int(
                    checklist, "review_required_count"
                ),
                "configuration_written": bool(summary.get("configuration_written")),
                "approval_record_written": bool(summary.get("approval_record_written")),
                "gateway_called": bool(summary.get("gateway_called")),
                "network_called": bool(summary.get("network_called")),
                "raw_payload_echoed": bool(summary.get("raw_payload_echoed")),
                "raw_model_output_returned": bool(summary.get("raw_model_output_returned")),
            }
        ]

    def _checks(
        self,
        checklist: dict[str, Any],
        signoff_items: list[dict[str, Any]],
        raw_input_field_count: int,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "default-promotion-checklist-attached-not-blocked",
                "source_key": "legal_benchmark_default_promotion_checklist",
                "status": "fail" if not checklist or self._is_blocked(checklist) else "warn",
                "source_status": self._status_text(checklist),
                "decision_effect": "blocks_default_promotion"
                if not checklist or self._is_blocked(checklist)
                else "requires_external_signoff",
                "reason": "Legal benchmark default-promotion checklist is missing or blocked."
                if not checklist or self._is_blocked(checklist)
                else "Checklist is attached and requires external maintainer signoff.",
                "source_blocking_ids": self._string_list(checklist.get("blocking_check_ids")),
                "source_warning_ids": self._string_list(checklist.get("warning_check_ids")),
            },
            {
                "id": "signoff-items-generated",
                "source_key": "legal_benchmark_default_promotion_signoff_packet",
                "status": "pass" if signoff_items else "warn",
                "source_status": "mapped" if signoff_items else "not_run",
                "decision_effect": "requires_external_signoff" if signoff_items else "requires_checklist_rows",
                "reason": "Checklist rows were converted into signoff items."
                if signoff_items
                else "No checklist rows are available for signoff packaging.",
                "source_blocking_ids": [],
                "source_warning_ids": [] if signoff_items else ["signoff-items-not-generated"],
            },
            {
                "id": "no-signoff-record-written",
                "source_key": "legal_benchmark_default_promotion_signoff_packet",
                "status": "pass",
                "source_status": "metadata_only",
                "decision_effect": "keeps_signoff_external",
                "reason": "The packet does not write approval or signoff records and does not collect approver identity.",
                "source_blocking_ids": [],
                "source_warning_ids": [],
            },
            {
                "id": "metadata-only-boundary",
                "source_key": "legal_benchmark_default_promotion_signoff_packet",
                "status": "warn" if raw_input_field_count else "pass",
                "source_status": "metadata_only",
                "decision_effect": "requires_payload_sanitization" if raw_input_field_count else "allows_external_signoff_review",
                "reason": f"Forbidden raw/sensitive input field count is {raw_input_field_count}; raw values are not echoed.",
                "source_blocking_ids": [],
                "source_warning_ids": ["raw-input-field-detected"] if raw_input_field_count else [],
            },
        ]

    def _signoff_status(self, row: dict[str, Any], checklist: dict[str, Any]) -> str:
        row_status = self._safe_text(row.get("checklist_status"), "not_run")
        if self._is_blocked(checklist) or row_status == "blocked":
            return "blocked"
        if row_status == "ready_for_maintainer_review":
            return "ready_for_signoff"
        if row_status in {"not_run", "not_ready", "not_supplied"}:
            return "not_run"
        return "review_required"

    def _required_signoffs(self, signoff_status: str, row: dict[str, Any]) -> list[str]:
        if signoff_status == "not_run":
            return ["legal_quality_owner"]
        base = [
            signoff for signoff in self._string_list(row.get("required_signoffs"))
            if signoff in {"model_ops_maintainer", "legal_quality_owner", "release_owner"}
        ]
        if not base:
            base = ["model_ops_maintainer", "legal_quality_owner", "release_owner"]
        return base

    def _pre_signoff_checks(self, signoff_status: str) -> list[str]:
        if signoff_status == "ready_for_signoff":
            return [
                "confirm-checklist-row-still-current",
                "confirm-legal-quality-owner-review",
                "confirm-release-owner-approval-outside-this-service",
                "prepare-configuration-change-outside-this-service",
            ]
        if signoff_status == "blocked":
            return [
                "resolve-blocking-checklist-evidence",
                "keep-current-legal-default",
                "record-review-outside-this-service-after-blockers-clear",
            ]
        if signoff_status == "not_run":
            return [
                "attach-default-promotion-checklist-row",
                "rerun-signoff-packet",
            ]
        return [
            "complete-maintainer-checklist-review",
            "confirm-default-change-queue-mapping",
            "record-signoff-outside-this-service-only",
        ]

    def _derived_reason_codes(self, *, signoff_status: str, checklist_status: str) -> list[str]:
        codes: list[str] = []
        if signoff_status == "blocked":
            codes.append("checklist-blocked")
        if signoff_status == "not_run":
            codes.append("checklist-row-not-ready")
        if signoff_status == "review_required":
            codes.append("external-signoff-review-required")
        if checklist_status in REVIEW_STATUSES:
            codes.append("checklist-status-review")
        return codes

    def _item_action(self, signoff_status: str, row: dict[str, Any]) -> str:
        task = self._safe_text(row.get("task"), "unknown")
        model_id = self._safe_text(row.get("proposed_default_model"), "the model")
        if signoff_status == "ready_for_signoff":
            return f"Collect external maintainer signoff for {task} before any default change to {model_id}."
        if signoff_status == "blocked":
            return f"Do not promote {model_id} for {task}; resolve checklist blockers first."
        if signoff_status == "not_run":
            return f"Attach checklist evidence before requesting {task} signoff."
        return f"Complete external signoff review for {task}; this packet will not apply the change."

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        signoff_items: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [f"Resolve signoff packet blocker: {check['id']}." for check in blocking[:5]]
        actions = [
            "Keep legal-task defaults unchanged until signoff is recorded outside this service.",
            "Attach this signoff packet beside the checklist in release evidence before external configuration work.",
        ]
        if warnings:
            actions.append("Review signoff warnings: " + ", ".join(check["id"] for check in warnings[:5]) + ".")
        if not signoff_items:
            actions.append("Attach checklist rows before using this signoff packet in release review.")
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
