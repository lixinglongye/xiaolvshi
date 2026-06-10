from __future__ import annotations

import re
from typing import Any

from services.model_ops_gemini_official_lifecycle_drift_gate import (
    ModelOpsGeminiOfficialLifecycleDriftGateService,
)
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)
from services.modelops_legal_fixture_cheap_first_regression_budget import (
    ModelOpsLegalFixtureCheapFirstRegressionBudgetService,
)
from services.modelops_legal_fixture_default_promotion_packet import (
    ModelOpsLegalFixtureDefaultPromotionPacketService,
)
from services.modelops_legal_fixture_evidence_handoff import ModelOpsLegalFixtureEvidenceHandoffService


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


class ModelOpsLegalBenchmarkDefaultPromotionBridgeService:
    """Join legal fixture benchmark evidence with Gemini lifecycle default-promotion guardrails."""

    def __init__(
        self,
        benchmark_gate_service: ModelOpsLegalFixtureCheapFirstBenchmarkGateService | None = None,
        promotion_packet_service: ModelOpsLegalFixtureDefaultPromotionPacketService | None = None,
        regression_budget_service: ModelOpsLegalFixtureCheapFirstRegressionBudgetService | None = None,
        evidence_handoff_service: ModelOpsLegalFixtureEvidenceHandoffService | None = None,
        lifecycle_gate_service: ModelOpsGeminiOfficialLifecycleDriftGateService | None = None,
    ) -> None:
        self.benchmark_gate_service = benchmark_gate_service or ModelOpsLegalFixtureCheapFirstBenchmarkGateService()
        self.promotion_packet_service = promotion_packet_service or ModelOpsLegalFixtureDefaultPromotionPacketService()
        self.regression_budget_service = regression_budget_service or ModelOpsLegalFixtureCheapFirstRegressionBudgetService()
        self.evidence_handoff_service = evidence_handoff_service or ModelOpsLegalFixtureEvidenceHandoffService()
        self.lifecycle_gate_service = lifecycle_gate_service or ModelOpsGeminiOfficialLifecycleDriftGateService()

    def build_bridge(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        benchmark_gate = self._source_dict(
            data,
            "legal_fixture_cheap_first_benchmark_gate",
            "cheap_first_benchmark_gate",
            "benchmark_gate",
            "source_gate",
        ) or self.benchmark_gate_service.build_gate(data or None)
        promotion_packet = self._source_dict(
            data,
            "legal_fixture_cheap_first_default_promotion_packet",
            "default_promotion_packet",
            "promotion_packet",
        ) or self.promotion_packet_service.build_packet({"source_gate": benchmark_gate})
        regression_budget = self._source_dict(
            data,
            "legal_fixture_cheap_first_regression_budget",
            "regression_budget",
        ) or self.regression_budget_service.build_budget(
            {
                "legal_fixture_cheap_first_benchmark_gate": benchmark_gate,
                "legal_fixture_cheap_first_default_promotion_packet": promotion_packet,
            }
        )
        evidence_handoff = self._source_dict(
            data,
            "legal_fixture_evidence_handoff",
            "evidence_handoff",
            "handoff",
        ) or self.evidence_handoff_service.build_handoff(
            {
                "cheap_first_benchmark_gate": benchmark_gate,
                "default_promotion_packet": promotion_packet,
            }
        )
        lifecycle_gate = self._source_dict(
            data,
            "gemini_official_lifecycle_drift_gate",
            "lifecycle_drift_gate",
            "gemini_lifecycle_gate",
        ) or self.lifecycle_gate_service.build_gate(data or None)

        raw_input_field_count = self._raw_input_field_count(data)
        lifecycle_by_model = self._lifecycle_by_model(lifecycle_gate)
        promotion_rows = self._promotion_rows(promotion_packet, benchmark_gate, lifecycle_by_model)
        source_rows = self._source_rows(
            benchmark_gate,
            promotion_packet,
            regression_budget,
            evidence_handoff,
            lifecycle_gate,
        )
        checks = self._checks(
            benchmark_gate,
            promotion_packet,
            regression_budget,
            evidence_handoff,
            lifecycle_gate,
            raw_input_field_count,
        )
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else "review_required"

        return {
            "id": "modelops-legal-benchmark-default-promotion-bridge",
            "title": "ModelOps legal benchmark default-promotion bridge",
            "status": status,
            "decision": {
                "status": status,
                "default_change_allowed_by_bridge": False,
                "current_cheap_first_defaults_allowed": not blocking,
                "maintainer_review_required": True,
                "requires_legal_fixture_benchmark_gate": True,
                "requires_default_promotion_packet": True,
                "requires_regression_budget": True,
                "requires_evidence_handoff": True,
                "requires_gemini_lifecycle_drift_gate": True,
                "configuration_change_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "bridge_release_action": "maintainer_review_required"
                if not blocking
                else "block_default_promotion",
            },
            "method": {
                "type": "metadata-only-legal-benchmark-default-promotion-bridge",
                "notes": [
                    "Consumes existing legal fixture benchmark, default-promotion packet, regression budget, evidence handoff, and Gemini lifecycle drift evidence.",
                    "Gives maintainers one pre-promotion view for cheap-first legal defaults without replaying models or gateway calls.",
                    "Blocks default-promotion review when the Gemini lifecycle gate reports blocked defaults or legal fixture evidence is blocked.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, public datasets, or the network.",
                ],
            },
            "summary": {
                "source_count": len(source_rows),
                "ready_source_count": sum(1 for row in source_rows if row["bridge_status"] == "ready"),
                "review_source_count": sum(1 for row in source_rows if row["bridge_status"] == "review_required"),
                "blocked_source_count": sum(1 for row in source_rows if row["bridge_status"] == "blocked"),
                "not_run_source_count": sum(1 for row in source_rows if row["bridge_status"] == "not_run"),
                "promotion_row_count": len(promotion_rows),
                "promotion_ready_count": sum(
                    1 for row in promotion_rows if row["bridge_status"] == "ready_for_maintainer_review"
                ),
                "promotion_review_count": sum(1 for row in promotion_rows if row["bridge_status"] == "review_required"),
                "promotion_blocked_count": sum(1 for row in promotion_rows if row["bridge_status"] == "blocked"),
                "source_benchmark_gate_status": self._status_text(benchmark_gate),
                "source_default_promotion_packet_status": self._status_text(promotion_packet),
                "source_regression_budget_status": self._status_text(regression_budget),
                "source_evidence_handoff_status": self._status_text(evidence_handoff),
                "source_gemini_lifecycle_status": self._status_text(lifecycle_gate),
                "document_benchmark_status": self._summary_value(benchmark_gate, "document_benchmark_status", "not_run"),
                "fact_consistency_status": self._summary_value(benchmark_gate, "fact_consistency_status", "not_run"),
                "local_rule_baseline_status": self._summary_value(benchmark_gate, "local_rule_baseline_status", "not_run"),
                "calibration_status": self._summary_value(benchmark_gate, "calibration_status", "not_run"),
                "regressed_fixture_count": self._summary_int(regression_budget, "regressed_fixture_count"),
                "runbook_ready_evidence_row_count": self._summary_int(regression_budget, "runbook_ready_evidence_row_count"),
                "handoff_release_ready": bool(self._summary(evidence_handoff).get("release_ready")),
                "stable_flash_lite_default_count": self._summary_int(lifecycle_gate, "stable_flash_lite_default_count"),
                "blocked_default_count": self._summary_int(lifecycle_gate, "blocked_default_count"),
                "review_default_count": self._summary_int(lifecycle_gate, "review_default_count"),
                "raw_input_field_count": raw_input_field_count,
                "default_change_allowed_by_bridge": False,
                "configuration_written": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "traffic_shifted": False,
                "raw_fixture_text_returned": False,
                "raw_document_text_returned": False,
                "raw_model_output_returned": False,
                "raw_payload_echoed": False,
            },
            "source_rows": source_rows,
            "promotion_rows": promotion_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "source_links": {
                "legal_fixture_benchmark_gate": "/api/v1/aihub/models/legal-fixture-cheap-first-benchmark-gate",
                "legal_fixture_default_promotion_packet": "/api/v1/aihub/models/legal-fixture-cheap-first-default-promotion-packet",
                "legal_fixture_regression_budget": "/api/v1/aihub/models/legal-fixture-cheap-first-regression-budget",
                "legal_fixture_evidence_handoff": "/api/v1/aihub/models/legal-fixture-evidence-handoff",
                "gemini_lifecycle_drift_gate": "/api/v1/aihub/models/gemini-official-lifecycle-drift-gate",
                "default_promotion_bridge": "/api/v1/aihub/models/legal-benchmark-default-promotion-bridge",
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, source_rows),
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
                "output_scope": "source statuses, fixture ids, model ids, check ids, counts, reason codes, and review actions only",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "maintainer_approval_claimed": False,
                "configuration_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_scores_claimed": False,
                "production_legal_quality_claimed": False,
                "gemini_lifecycle_refresh_claimed": False,
                "legal_advice_claimed": False,
                "allowed_claim": "Metadata-only legal benchmark and Gemini lifecycle evidence is joined for maintainer default-promotion review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_benchmark_default_promotion_bridge.py tests/test_modelops_legal_fixture_cheap_first_regression_budget.py tests/test_model_ops_gemini_official_lifecycle_drift_gate.py -q",
                "python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _source_rows(
        self,
        benchmark_gate: dict[str, Any],
        promotion_packet: dict[str, Any],
        regression_budget: dict[str, Any],
        evidence_handoff: dict[str, Any],
        lifecycle_gate: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            self._source_row(
                "legal-fixture-benchmark-gate",
                "Legal fixture benchmark gate",
                "legal_fixture_cheap_first_benchmark_gate",
                benchmark_gate,
                "/api/v1/aihub/models/legal-fixture-cheap-first-benchmark-gate",
                "default_change_evidence_allowed",
            ),
            self._source_row(
                "legal-fixture-default-promotion-packet",
                "Legal fixture default promotion packet",
                "legal_fixture_cheap_first_default_promotion_packet",
                promotion_packet,
                "/api/v1/aihub/models/legal-fixture-cheap-first-default-promotion-packet",
                "default_change_allowed_by_packet",
            ),
            self._source_row(
                "legal-fixture-regression-budget",
                "Legal fixture regression budget",
                "legal_fixture_cheap_first_regression_budget",
                regression_budget,
                "/api/v1/aihub/models/legal-fixture-cheap-first-regression-budget",
                "default_change_allowed_by_budget",
            ),
            self._source_row(
                "legal-fixture-evidence-handoff",
                "Legal fixture evidence handoff",
                "legal_fixture_evidence_handoff",
                evidence_handoff,
                "/api/v1/aihub/models/legal-fixture-evidence-handoff",
                "release_ready",
            ),
            self._source_row(
                "gemini-official-lifecycle-drift-gate",
                "Gemini official lifecycle drift gate",
                "gemini_official_lifecycle_drift_gate",
                lifecycle_gate,
                "/api/v1/aihub/models/gemini-official-lifecycle-drift-gate",
                "stable_flash_lite_default_count",
            ),
        ]

    def _source_row(
        self,
        row_id: str,
        label: str,
        source_key: str,
        source: dict[str, Any],
        endpoint: str,
        primary_summary_key: str,
    ) -> dict[str, Any]:
        summary = self._summary(source)
        status = self._status_text(source)
        return {
            "id": row_id,
            "label": label,
            "source_key": source_key,
            "endpoint": endpoint,
            "source_status": status,
            "bridge_status": self._bridge_status(status),
            "primary_summary_key": primary_summary_key,
            "primary_summary_value": summary.get(primary_summary_key),
            "blocking_count": len(source.get("blocking_check_ids") or []) + self._summary_int(source, "blocking_count"),
            "warning_count": len(source.get("warning_check_ids") or []) + self._summary_int(source, "warning_count"),
            "configuration_written": bool(summary.get("configuration_written")),
            "gateway_called": bool(summary.get("gateway_called")),
            "network_called": bool(summary.get("network_called")),
            "raw_payload_returned": bool(summary.get("raw_payload_echoed")),
            "raw_model_output_returned": bool(summary.get("raw_model_output_returned")),
        }

    def _promotion_rows(
        self,
        promotion_packet: dict[str, Any],
        benchmark_gate: dict[str, Any],
        lifecycle_by_model: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        gate_summary = self._summary(benchmark_gate)
        rows: list[dict[str, Any]] = []
        for item in self._list_of_dicts(promotion_packet.get("promotion_items")):
            model_id = self._safe_text(item.get("proposed_default_model") or item.get("cheap_first_model"), "")
            lifecycle = lifecycle_by_model.get(model_id, {})
            reason_codes = self._string_list(item.get("reason_codes"))
            lifecycle_status = self._safe_text(lifecycle.get("official_lifecycle"), "unknown")
            if lifecycle_status in {"preview", "deprecated", "shutdown", "retired"}:
                reason_codes.append("gemini-lifecycle-blocks-default")
            bridge_status = self._promotion_bridge_status(item, lifecycle_status)
            rows.append(
                {
                    "id": self._safe_text(item.get("id"), "legal-fixture-promotion-unknown"),
                    "fixture_id": self._safe_text(item.get("fixture_id"), "unknown"),
                    "task": self._safe_text(item.get("task"), "unknown"),
                    "matter_type": self._safe_text(item.get("matter_type"), "unknown"),
                    "proposed_default_model": model_id or "unknown",
                    "model_cost_tier": self._safe_text(item.get("proposed_cost_tier"), "unknown"),
                    "promotion_status": self._safe_text(item.get("promotion_status"), "not_ready"),
                    "bridge_status": bridge_status,
                    "gate_status": self._safe_text(item.get("gate_status"), "not_run"),
                    "document_benchmark_status": self._safe_text(
                        item.get("document_benchmark_status") or gate_summary.get("document_benchmark_status"),
                        "not_run",
                    ),
                    "fact_consistency_status": self._safe_text(
                        item.get("fact_consistency_status") or gate_summary.get("fact_consistency_status"),
                        "not_run",
                    ),
                    "calibration_status": self._safe_text(item.get("calibration_status"), "not_mapped"),
                    "official_lifecycle": lifecycle_status,
                    "lifecycle_default_policy": self._safe_text(lifecycle.get("default_policy"), "review_required"),
                    "default_change_allowed_by_bridge": False,
                    "configuration_change_allowed": False,
                    "gateway_call_allowed": False,
                    "reason_codes": self._dedupe(reason_codes),
                    "action": self._promotion_action(bridge_status, model_id),
                }
            )
        return rows

    def _promotion_bridge_status(self, item: dict[str, Any], lifecycle_status: str) -> str:
        promotion_status = self._safe_text(item.get("promotion_status"), "not_ready")
        if promotion_status == "blocked" or lifecycle_status in {"preview", "deprecated", "shutdown", "retired"}:
            return "blocked"
        if promotion_status == "ready_for_maintainer_review":
            return "ready_for_maintainer_review"
        if promotion_status in {"review_required", "ready_with_watchlist"}:
            return "review_required"
        return "not_ready"

    def _checks(
        self,
        benchmark_gate: dict[str, Any],
        promotion_packet: dict[str, Any],
        regression_budget: dict[str, Any],
        evidence_handoff: dict[str, Any],
        lifecycle_gate: dict[str, Any],
        raw_input_field_count: int,
    ) -> list[dict[str, Any]]:
        return [
            self._source_check(
                "legal-fixture-benchmark-ready",
                "legal_fixture_cheap_first_benchmark_gate",
                benchmark_gate,
                pass_when=lambda source: self._status_text(source) in PASS_STATUSES
                and bool(source.get("default_change_evidence_allowed")),
                fail_reason="Legal fixture benchmark gate has blocked fixture, document, fact-consistency, local-rule, or calibration evidence.",
                warn_reason="Legal fixture benchmark evidence is not fully ready for default-promotion review.",
            ),
            self._source_check(
                "default-promotion-packet-ready",
                "legal_fixture_cheap_first_default_promotion_packet",
                promotion_packet,
                pass_when=lambda source: self._status_text(source) == "ready_for_maintainer_review",
                fail_reason="Legal fixture default-promotion packet is blocked.",
                warn_reason="Legal fixture default-promotion packet still needs maintainer review or source evidence.",
            ),
            self._source_check(
                "regression-budget-not-blocked",
                "legal_fixture_cheap_first_regression_budget",
                regression_budget,
                pass_when=lambda source: self._status_text(source) in {"pass", "ready", "review_required"},
                fail_reason="Legal fixture regression budget has fixture drift or source blockers.",
                warn_reason="Legal fixture regression budget is not ready or lacks baseline/current evidence.",
            ),
            self._source_check(
                "evidence-handoff-archive-safe",
                "legal_fixture_evidence_handoff",
                evidence_handoff,
                pass_when=lambda source: self._status_text(source) == "ready",
                fail_reason="Legal fixture evidence handoff has archive or source blockers.",
                warn_reason="Legal fixture evidence handoff is missing local review/archive evidence.",
            ),
            {
                "id": "gemini-lifecycle-defaults-not-blocked",
                "source_key": "gemini_official_lifecycle_drift_gate",
                "status": "fail"
                if self._status_text(lifecycle_gate) in FAIL_STATUSES
                or self._summary_int(lifecycle_gate, "blocked_default_count") > 0
                else "pass",
                "source_status": self._status_text(lifecycle_gate),
                "decision_effect": "blocks_default_promotion"
                if self._status_text(lifecycle_gate) in FAIL_STATUSES
                or self._summary_int(lifecycle_gate, "blocked_default_count") > 0
                else "allows_maintainer_review",
                "reason": "Gemini lifecycle drift gate blocks at least one configured default."
                if self._status_text(lifecycle_gate) in FAIL_STATUSES
                or self._summary_int(lifecycle_gate, "blocked_default_count") > 0
                else "No blocked Gemini lifecycle defaults are present; review-only defaults remain explicit.",
                "source_blocking_ids": self._string_list(lifecycle_gate.get("blocking_check_ids")),
                "source_warning_ids": self._string_list(lifecycle_gate.get("warning_check_ids")),
            },
            {
                "id": "metadata-only-boundary",
                "source_key": "legal_benchmark_default_promotion_bridge",
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
        pass_when: Any,
        fail_reason: str,
        warn_reason: str,
    ) -> dict[str, Any]:
        status = self._status_text(source)
        source_blocking_ids = self._string_list(source.get("blocking_check_ids"))
        source_warning_ids = self._string_list(source.get("warning_check_ids"))
        if not source:
            check_status = "warn"
            decision_effect = "requires_maintainer_review"
            reason = warn_reason
        elif status in FAIL_STATUSES or source_blocking_ids:
            check_status = "fail"
            decision_effect = "blocks_default_promotion"
            reason = fail_reason
        elif pass_when(source):
            check_status = "pass"
            decision_effect = "allows_maintainer_review"
            reason = "Source evidence supports maintainer default-promotion review."
        else:
            check_status = "warn"
            decision_effect = "requires_maintainer_review"
            reason = warn_reason
        return {
            "id": check_id,
            "source_key": source_key,
            "status": check_status,
            "source_status": status or "missing",
            "decision_effect": decision_effect,
            "reason": reason,
            "source_blocking_ids": source_blocking_ids,
            "source_warning_ids": source_warning_ids,
        }

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        source_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [
                f"Resolve blocker before legal default promotion: {check['id']}."
                for check in blocking[:5]
            ]
        actions = [
            "Keep legal-task cheap-first defaults unchanged until a maintainer approves the joined benchmark and lifecycle evidence.",
            "Attach this bridge beside the benchmark gate, promotion packet, regression budget, and lifecycle drift gate in release evidence.",
        ]
        if warnings:
            actions.append("Review warning sources: " + ", ".join(check["id"] for check in warnings[:5]) + ".")
        not_run = [row["id"] for row in source_rows if row["bridge_status"] == "not_run"]
        if not_run:
            actions.append("Run or attach source evidence for: " + ", ".join(not_run[:5]) + ".")
        return actions[:6]

    def _promotion_action(self, bridge_status: str, model_id: str) -> str:
        if bridge_status == "blocked":
            return f"Do not promote {model_id or 'the model'} until legal benchmark or lifecycle blockers are fixed."
        if bridge_status == "ready_for_maintainer_review":
            return f"Review {model_id or 'the model'} as evidence for a legal-task cheap-first default; apply changes outside this service."
        if bridge_status == "review_required":
            return f"Review watchlist evidence before using {model_id or 'the model'} for default-promotion support."
        return "Collect legal fixture, regression, handoff, and lifecycle evidence before promotion review."

    def _lifecycle_by_model(self, lifecycle_gate: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {
            str(row.get("model_id")): row
            for row in self._list_of_dicts(lifecycle_gate.get("lifecycle_rows"))
            if row.get("model_id")
        }

    def _source_dict(self, data: dict[str, Any], *keys: str) -> dict[str, Any]:
        for key in keys:
            value = data.get(key)
            if isinstance(value, dict):
                return value
        return {}

    def _summary(self, value: dict[str, Any]) -> dict[str, Any]:
        summary = value.get("summary")
        return summary if isinstance(summary, dict) else {}

    def _summary_value(self, value: dict[str, Any], key: str, fallback: str) -> str:
        return self._safe_text(self._summary(value).get(key), fallback)

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

    def _bridge_status(self, status: str) -> str:
        if status in FAIL_STATUSES:
            return "blocked"
        if status in PASS_STATUSES:
            return "ready"
        if status in {"not_run", "not_ready", "not_supplied"}:
            return "not_run"
        if status in REVIEW_STATUSES:
            return "review_required"
        return "review_required"

    def _list_of_dicts(self, value: Any) -> list[dict[str, Any]]:
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    def _string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [text for text in (self._safe_text(item, "") for item in value) if text]

    def _safe_text(self, value: Any, fallback: str) -> str:
        text = str(value or "").strip()
        return text[:180] if text else fallback

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value in seen:
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
