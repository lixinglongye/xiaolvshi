from __future__ import annotations

import re
from typing import Any

from services.modelops_legal_benchmark_default_promotion_bridge import (
    ModelOpsLegalBenchmarkDefaultPromotionBridgeService,
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
PASS_STATUSES = {"pass", "ready", "ok", "success"}
REVIEW_STATUSES = {
    "not_ready",
    "not_run",
    "not_supplied",
    "review_required",
    "review_recommended",
    "ready_for_maintainer_review",
    "ready_with_watchlist",
    "warn",
    "warning",
}


class ModelOpsLegalBenchmarkDefaultPromotionChecklistService:
    """Build a maintainer checklist for legal benchmark default-promotion review."""

    def __init__(
        self,
        bridge_service: ModelOpsLegalBenchmarkDefaultPromotionBridgeService | None = None,
    ) -> None:
        self.bridge_service = bridge_service or ModelOpsLegalBenchmarkDefaultPromotionBridgeService()

    def build_checklist(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        bridge = self._source_dict(data, "legal_benchmark_default_promotion_bridge", "default_promotion_bridge")
        if not bridge:
            bridge = self.bridge_service.build_bridge(data or None)
        release_decision = self._source_dict(data, "cheap_first_release_decision", "release_decision")
        default_change_queue = self._source_dict(data, "default_change_queue", "change_queue")

        raw_input_field_count = self._raw_input_field_count(data)
        queue_by_task = self._queue_by_task(default_change_queue)
        checklist_rows = self._checklist_rows(bridge, release_decision, default_change_queue, queue_by_task)
        source_status_rows = self._source_status_rows(bridge, release_decision, default_change_queue)
        checks = self._checks(
            bridge,
            release_decision,
            default_change_queue,
            checklist_rows,
            raw_input_field_count,
        )
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        ready_rows = [row for row in checklist_rows if row["checklist_status"] == "ready_for_maintainer_review"]
        review_rows = [row for row in checklist_rows if row["checklist_status"] == "review_required"]
        blocked_rows = [row for row in checklist_rows if row["checklist_status"] == "blocked"]
        not_run_rows = [row for row in checklist_rows if row["checklist_status"] == "not_run"]
        status = "blocked" if blocking or blocked_rows else "review_required"
        bridge_decision = bridge.get("decision") if isinstance(bridge.get("decision"), dict) else {}

        return {
            "id": "modelops-legal-benchmark-default-promotion-checklist",
            "title": "ModelOps legal benchmark default-promotion checklist",
            "status": status,
            "decision": {
                "status": status,
                "default_change_allowed_by_checklist": False,
                "configuration_change_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "maintainer_review_required": True,
                "requires_default_promotion_bridge": True,
                "requires_release_decision_not_failed": True,
                "requires_default_change_queue_review": True,
                "requires_metadata_only_boundary": True,
                "bridge_release_action": self._safe_text(
                    bridge_decision.get("bridge_release_action"),
                    "maintainer_review_required",
                ),
                "checklist_release_action": "block_default_promotion"
                if status == "blocked"
                else "maintainer_review_required",
            },
            "method": {
                "type": "metadata-only-legal-benchmark-default-promotion-checklist",
                "notes": [
                    "Consumes the legal benchmark default-promotion bridge and, when available, cheap-first release decision and default-change queue evidence.",
                    "Creates maintainer checklist rows for legal-task default-promotion review without approving or applying changes.",
                    "Keeps the checklist downstream of release decision and default-change queue to avoid circular release gates.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, public datasets, or the network.",
                ],
            },
            "summary": {
                "source_count": len(source_status_rows),
                "checklist_row_count": len(checklist_rows),
                "ready_for_maintainer_review_count": len(ready_rows),
                "review_required_count": len(review_rows),
                "blocked_count": len(blocked_rows),
                "not_run_count": len(not_run_rows),
                "bridge_status": self._status_text(bridge),
                "release_decision_status": self._status_text(release_decision),
                "default_change_queue_status": self._status_text(default_change_queue),
                "promotion_row_count": self._summary_int(bridge, "promotion_row_count")
                or len(self._list_of_dicts(bridge.get("promotion_rows"))),
                "queue_item_count": self._summary_int(default_change_queue, "queue_item_count")
                or len(self._list_of_dicts(default_change_queue.get("queue_items"))),
                "blocked_default_count": self._summary_int(bridge, "blocked_default_count"),
                "blocked_queue_item_count": len(default_change_queue.get("blocking_item_ids") or []),
                "raw_input_field_count": raw_input_field_count,
                "default_change_allowed_by_checklist": False,
                "configuration_written": False,
                "env_file_written": False,
                "approval_record_written": False,
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
            "checklist_rows": checklist_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "required_signoffs": [
                "model_ops_maintainer",
                "legal_quality_owner",
                "release_owner",
            ],
            "source_links": {
                "legal_benchmark_default_promotion_bridge": "/api/v1/aihub/models/legal-benchmark-default-promotion-bridge",
                "cheap_first_release_decision": "/api/v1/aihub/models/cheap-first-release-decision",
                "default_change_queue": "/api/v1/aihub/models/default-change-queue",
                "legal_benchmark_default_promotion_checklist": "/api/v1/aihub/models/legal-benchmark-default-promotion-checklist",
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, checklist_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_model_ids": True,
                "returns_source_statuses": True,
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
                "traffic_shifted": False,
                "output_scope": "source statuses, fixture ids, model ids, queue ids, checklist statuses, signoff roles, check ids, counts, and review actions only",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "maintainer_approval_claimed": False,
                "configuration_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_scores_claimed": False,
                "production_legal_quality_claimed": False,
                "legal_advice_claimed": False,
                "allowed_claim": "Metadata-only legal benchmark default-promotion evidence is ready for maintainer checklist review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_benchmark_default_promotion_checklist.py tests/test_modelops_legal_benchmark_default_promotion_bridge.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_default_change_queue.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _checklist_rows(
        self,
        bridge: dict[str, Any],
        release_decision: dict[str, Any],
        default_change_queue: dict[str, Any],
        queue_by_task: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        release_status = self._status_text(release_decision)
        queue_status = self._status_text(default_change_queue)
        release_blocked = self._is_blocked(release_decision)
        queue_blocked = self._is_blocked(default_change_queue)
        rows: list[dict[str, Any]] = []
        for index, promotion in enumerate(self._list_of_dicts(bridge.get("promotion_rows")), start=1):
            task = self._safe_text(promotion.get("task"), "unknown")
            queue_item = queue_by_task.get(task, {})
            checklist_status = self._checklist_status(
                promotion,
                release_status=release_status,
                queue_status=queue_status,
                release_blocked=release_blocked,
                queue_blocked=queue_blocked,
            )
            reason_codes = self._dedupe(
                [
                    *self._string_list(promotion.get("reason_codes")),
                    *self._row_reason_codes(
                        checklist_status=checklist_status,
                        release_status=release_status,
                        queue_status=queue_status,
                        queue_item=queue_item,
                    ),
                ]
            )
            rows.append(
                {
                    "id": f"legal-benchmark-default-promotion-checklist-{index}",
                    "requirement_id": self._safe_text(
                        promotion.get("id"),
                        f"legal-benchmark-default-promotion-{index}",
                    ),
                    "source_key": "legal_benchmark_default_promotion_bridge",
                    "fixture_id": self._safe_text(promotion.get("fixture_id"), "unknown"),
                    "task": task,
                    "proposed_default_model": self._safe_text(
                        promotion.get("proposed_default_model"),
                        "unknown",
                    ),
                    "model_cost_tier": self._safe_text(promotion.get("model_cost_tier"), "unknown"),
                    "evidence_status": self._safe_text(promotion.get("bridge_status"), "not_run"),
                    "promotion_status": self._safe_text(promotion.get("promotion_status"), "not_ready"),
                    "official_lifecycle": self._safe_text(promotion.get("official_lifecycle"), "unknown"),
                    "release_decision_status": release_status,
                    "default_change_queue_status": queue_status,
                    "matched_queue_item_id": self._safe_text(queue_item.get("id"), "not_mapped"),
                    "matched_queue_item_status": self._safe_text(queue_item.get("queue_status"), "not_mapped"),
                    "checklist_status": checklist_status,
                    "default_change_allowed_by_checklist": False,
                    "configuration_change_allowed": False,
                    "gateway_call_allowed": False,
                    "traffic_shift_allowed": False,
                    "required_signoffs": [
                        "model_ops_maintainer",
                        "legal_quality_owner",
                        "release_owner",
                    ],
                    "reason_codes": reason_codes,
                    "release_action": self._row_action(
                        checklist_status,
                        model_id=self._safe_text(promotion.get("proposed_default_model"), "the model"),
                        task=task,
                    ),
                }
            )
        return rows

    def _source_status_rows(
        self,
        bridge: dict[str, Any],
        release_decision: dict[str, Any],
        default_change_queue: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            self._source_status_row(
                "legal-benchmark-default-promotion-bridge",
                "Legal benchmark default-promotion bridge",
                "legal_benchmark_default_promotion_bridge",
                bridge,
            ),
            self._source_status_row(
                "cheap-first-release-decision",
                "Cheap-first release decision",
                "cheap_first_release_decision",
                release_decision,
            ),
            self._source_status_row(
                "default-change-queue",
                "Default change queue",
                "default_change_queue",
                default_change_queue,
            ),
        ]

    def _source_status_row(
        self,
        row_id: str,
        label: str,
        source_key: str,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        summary = self._summary(source)
        status = self._status_text(source)
        return {
            "id": row_id,
            "label": label,
            "source_key": source_key,
            "source_status": status,
            "checklist_status": "blocked"
            if self._is_blocked(source)
            else ("review_required" if status in REVIEW_STATUSES or not source else "ready"),
            "blocking_count": len(source.get("blocking_check_ids") or [])
            + len(source.get("blocking_item_ids") or [])
            + self._summary_int(source, "blocking_count")
            + self._summary_int(source, "blocked_count"),
            "warning_count": len(source.get("warning_check_ids") or [])
            + len(source.get("warning_item_ids") or [])
            + len(source.get("review_item_ids") or [])
            + self._summary_int(source, "warning_count")
            + self._summary_int(source, "review_required_count"),
            "configuration_written": bool(summary.get("configuration_written")),
            "gateway_called": bool(summary.get("gateway_called")),
            "network_called": bool(summary.get("network_called")),
            "raw_payload_echoed": bool(summary.get("raw_payload_echoed")),
            "raw_model_output_returned": bool(summary.get("raw_model_output_returned")),
        }

    def _checks(
        self,
        bridge: dict[str, Any],
        release_decision: dict[str, Any],
        default_change_queue: dict[str, Any],
        checklist_rows: list[dict[str, Any]],
        raw_input_field_count: int,
    ) -> list[dict[str, Any]]:
        return [
            self._source_check(
                "default-promotion-bridge-attached-not-blocked",
                "legal_benchmark_default_promotion_bridge",
                bridge,
                missing_status="fail",
                warn_statuses={"review_required", "ready_for_maintainer_review"},
                warn_reason="Legal benchmark default-promotion bridge requires maintainer review.",
                fail_reason="Legal benchmark default-promotion bridge is missing or blocked.",
            ),
            self._source_check(
                "cheap-first-release-decision-not-failed",
                "cheap_first_release_decision",
                release_decision,
                missing_status="warn",
                warn_statuses={"review_required", "warn", "warning"},
                warn_reason="Cheap-first release decision is unavailable or still requires maintainer review.",
                fail_reason="Cheap-first release decision blocks default changes.",
            ),
            self._source_check(
                "default-change-queue-not-blocked",
                "default_change_queue",
                default_change_queue,
                missing_status="warn",
                warn_statuses={"review_required", "warn", "warning"},
                warn_reason="Default-change queue is unavailable or still requires maintainer review.",
                fail_reason="Default-change queue has blocked items.",
            ),
            {
                "id": "promotion-rows-mapped-to-checklist",
                "source_key": "legal_benchmark_default_promotion_checklist",
                "status": "pass" if checklist_rows else "warn",
                "source_status": "mapped" if checklist_rows else "not_run",
                "decision_effect": "allows_maintainer_review" if checklist_rows else "requires_source_evidence",
                "reason": "Legal benchmark promotion rows were converted into checklist rows."
                if checklist_rows
                else "No legal benchmark promotion rows are available for checklist review.",
                "source_blocking_ids": [],
                "source_warning_ids": [] if checklist_rows else ["promotion-rows-not-attached"],
            },
            {
                "id": "metadata-only-boundary",
                "source_key": "legal_benchmark_default_promotion_checklist",
                "status": "warn" if raw_input_field_count else "pass",
                "source_status": "metadata_only",
                "decision_effect": "requires_payload_sanitization" if raw_input_field_count else "allows_maintainer_review",
                "reason": f"Forbidden raw/sensitive input field count is {raw_input_field_count}; raw values are not echoed.",
                "source_blocking_ids": [],
                "source_warning_ids": ["raw-input-field-detected"] if raw_input_field_count else [],
            },
        ]

    def _source_check(
        self,
        check_id: str,
        source_key: str,
        source: dict[str, Any],
        *,
        missing_status: str,
        warn_statuses: set[str],
        warn_reason: str,
        fail_reason: str,
    ) -> dict[str, Any]:
        status = self._status_text(source)
        source_blocking_ids = self._string_list(source.get("blocking_check_ids")) + self._string_list(
            source.get("blocking_item_ids")
        )
        source_warning_ids = self._string_list(source.get("warning_check_ids")) + self._string_list(
            source.get("review_item_ids")
        )
        if not source:
            check_status = missing_status
            decision_effect = "blocks_default_promotion" if missing_status == "fail" else "requires_maintainer_review"
            reason = fail_reason if missing_status == "fail" else warn_reason
        elif self._is_blocked(source):
            check_status = "fail"
            decision_effect = "blocks_default_promotion"
            reason = fail_reason
        elif status in warn_statuses or source_warning_ids:
            check_status = "warn"
            decision_effect = "requires_maintainer_review"
            reason = warn_reason
        else:
            check_status = "pass"
            decision_effect = "allows_maintainer_review"
            reason = "Source evidence is attached and does not block maintainer checklist review."
        return {
            "id": check_id,
            "source_key": source_key,
            "status": check_status,
            "source_status": status,
            "decision_effect": decision_effect,
            "reason": reason,
            "source_blocking_ids": source_blocking_ids,
            "source_warning_ids": source_warning_ids,
        }

    def _checklist_status(
        self,
        promotion: dict[str, Any],
        *,
        release_status: str,
        queue_status: str,
        release_blocked: bool,
        queue_blocked: bool,
    ) -> str:
        promotion_status = self._safe_text(promotion.get("bridge_status"), "not_run")
        if promotion_status == "blocked" or release_blocked or queue_blocked:
            return "blocked"
        if promotion_status == "ready_for_maintainer_review" and release_status in PASS_STATUSES and queue_status in {
            "ready",
            "pass",
            "ok",
            "success",
        }:
            return "ready_for_maintainer_review"
        if promotion_status in {"not_ready", "not_run", "not_supplied"}:
            return "not_run"
        return "review_required"

    def _row_reason_codes(
        self,
        *,
        checklist_status: str,
        release_status: str,
        queue_status: str,
        queue_item: dict[str, Any],
    ) -> list[str]:
        codes: list[str] = []
        if checklist_status == "blocked":
            codes.append("default-promotion-blocked")
        if release_status in {"missing", "not_supplied", "review_required", "warn", "warning"}:
            codes.append("release-decision-review-required")
        if release_status in FAIL_STATUSES:
            codes.append("release-decision-blocked")
        if not queue_item:
            codes.append("default-change-queue-not-mapped")
        elif self._safe_text(queue_item.get("queue_status"), "missing") in {"review_required", "warn", "warning"}:
            codes.append("default-change-queue-review-required")
        if queue_status in FAIL_STATUSES:
            codes.append("default-change-queue-blocked")
        return codes

    def _row_action(self, checklist_status: str, *, model_id: str, task: str) -> str:
        if checklist_status == "blocked":
            return f"Do not promote {model_id} for {task}; resolve blocking bridge, release, or queue evidence first."
        if checklist_status == "ready_for_maintainer_review":
            return f"Attach this row to maintainer review before any external default change for {task}."
        if checklist_status == "not_run":
            return f"Collect legal benchmark bridge evidence before reviewing {task} default promotion."
        return f"Complete maintainer checklist review for {task}; keep default changes outside this service."

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        checklist_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [f"Resolve legal default-promotion checklist blocker: {check['id']}." for check in blocking[:5]]
        actions = [
            "Keep legal-task cheap-first defaults unchanged until a maintainer signs off on the checklist.",
            "Attach the bridge, release decision, default-change queue, and this checklist to release evidence.",
        ]
        if warnings:
            actions.append("Review checklist warning checks: " + ", ".join(check["id"] for check in warnings[:5]) + ".")
        if not checklist_rows:
            actions.append("Attach legal benchmark promotion rows before using this checklist in a release review.")
        return actions[:6]

    def _queue_by_task(self, default_change_queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for row in self._list_of_dicts(default_change_queue.get("queue_items")):
            task = self._safe_text(row.get("task"), "")
            if task and task not in rows:
                rows[task] = row
        return rows

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
