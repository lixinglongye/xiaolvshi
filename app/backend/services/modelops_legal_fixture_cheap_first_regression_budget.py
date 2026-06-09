from __future__ import annotations

import re
from typing import Any

from services.legal_fixture_regression import LegalFixtureRegressionService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)
from services.modelops_legal_fixture_default_promotion_packet import (
    ModelOpsLegalFixtureDefaultPromotionPacketService,
)
from services.small_legal_document_benchmark_runbook_evidence import (
    SmallLegalDocumentBenchmarkRunbookEvidenceService,
)


RAW_INPUT_FIELD_NAMES = {
    "api_key",
    "authorization",
    "content",
    "credential",
    "credentials",
    "document_text",
    "fixture_text",
    "generated_text",
    "gateway_payload",
    "gateway_response",
    "headers",
    "messages",
    "output_text",
    "prompt",
    "raw_output",
    "raw_response",
    "secret",
}
SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b",
    re.IGNORECASE,
)
BLOCKING_STATUSES = {"blocked", "fail", "failed", "error", "needs_escalation"}
REVIEW_STATUSES = {
    "not_ready",
    "not_run",
    "review_required",
    "review_recommended",
    "ready_for_maintainer_review",
    "ready_with_watchlist",
    "warn",
    "warning",
}


class ModelOpsLegalFixtureCheapFirstRegressionBudgetService:
    """Bind cheap-first legal fixture regressions to a low-resource release budget."""

    def __init__(
        self,
        regression_service: LegalFixtureRegressionService | None = None,
        gate_service: ModelOpsLegalFixtureCheapFirstBenchmarkGateService | None = None,
        promotion_packet_service: ModelOpsLegalFixtureDefaultPromotionPacketService | None = None,
        runbook_service: SmallLegalDocumentBenchmarkRunbookEvidenceService | None = None,
    ) -> None:
        self.regression_service = regression_service or LegalFixtureRegressionService()
        self.gate_service = gate_service or ModelOpsLegalFixtureCheapFirstBenchmarkGateService()
        self.promotion_packet_service = promotion_packet_service or ModelOpsLegalFixtureDefaultPromotionPacketService()
        self.runbook_service = runbook_service or SmallLegalDocumentBenchmarkRunbookEvidenceService()

    def build_budget(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        source = payload if isinstance(payload, dict) else {}
        gate = self._source_dict(
            source,
            "legal_fixture_cheap_first_benchmark_gate",
            "cheap_first_benchmark_gate",
            "source_gate",
            "gate",
        ) or self.gate_service.build_gate(source or None)
        promotion_packet = self._source_dict(
            source,
            "legal_fixture_cheap_first_default_promotion_packet",
            "default_promotion_packet",
            "promotion_packet",
        ) or self.promotion_packet_service.build_packet({"source_gate": gate})
        runbook = self._source_dict(
            source,
            "small_legal_document_benchmark_runbook_evidence",
            "small_document_runbook_evidence",
            "runbook_evidence",
            "runbook",
        ) or self.runbook_service.build_evidence(source or None)
        regression_payload = source.get("regression") if isinstance(source.get("regression"), dict) else source
        regression = self._source_dict(
            source,
            "legal_fixture_regression",
            "fixture_regression",
            "regression_comparison",
        ) or self.regression_service.build_comparison(regression_payload if regression_payload else None)

        budget_rows = self._budget_rows(gate, promotion_packet, regression)
        checks = self._checks(gate, promotion_packet, regression, runbook, budget_rows)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = self._status(blocking, warnings, budget_rows)

        return {
            "id": "modelops-legal-fixture-cheap-first-regression-budget",
            "status": status,
            "decision": {
                "status": status,
                "default_change_allowed_by_budget": False,
                "current_cheap_first_default_allowed": status != "blocked",
                "requires_regression_pass": True,
                "requires_benchmark_gate_ready": True,
                "requires_document_runbook_ready": True,
                "requires_promotion_packet_review": True,
                "max_parallel_requests": self._max_parallel_requests(gate, runbook),
                "configuration_change_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
            },
            "method": {
                "type": "modelops-legal-fixture-cheap-first-regression-budget",
                "notes": [
                    "Joins fixture regression comparison, cheap-first benchmark gate, default-promotion packet, and small-document runbook evidence.",
                    "Keeps cheap-first Gemini legal defaults reviewable only when local fixture regressions are stable and tiny document checks are ready.",
                    "Returns metadata ids, statuses, counts, and budget actions only; it never calls models, gateways, public datasets, or the network.",
                ],
            },
            "summary": {
                "fixture_budget_row_count": len(budget_rows),
                "pass_count": sum(1 for row in budget_rows if row["budget_status"] == "pass"),
                "review_required_count": sum(1 for row in budget_rows if row["budget_status"] == "review_required"),
                "blocked_count": sum(1 for row in budget_rows if row["budget_status"] == "blocked"),
                "not_run_count": sum(1 for row in budget_rows if row["budget_status"] == "not_run"),
                "source_gate_status": str(gate.get("status") or "not_run"),
                "source_promotion_packet_status": str(promotion_packet.get("status") or "not_ready"),
                "source_regression_status": str(regression.get("status") or "not_run"),
                "source_runbook_status": str(runbook.get("status") or "review_required"),
                "regressed_fixture_count": self._summary_int(regression, "regressed_fixture_count"),
                "newly_blocking_fixture_count": self._summary_int(regression, "newly_blocking_fixture_count"),
                "resolved_blocking_fixture_count": self._summary_int(regression, "resolved_blocking_fixture_count"),
                "document_benchmark_status": self._summary_value(gate, "document_benchmark_status", "not_run"),
                "fact_consistency_status": self._summary_value(gate, "fact_consistency_status", "not_run"),
                "runbook_ready_evidence_row_count": self._summary_int(runbook, "ready_evidence_row_count"),
                "runbook_blocked_evidence_row_count": self._summary_int(runbook, "blocked_evidence_row_count"),
                "cheap_first_model_count": sum(1 for row in budget_rows if row["cheap_first_model"]),
                "max_parallel_requests": self._max_parallel_requests(gate, runbook),
                "raw_input_field_count": self._raw_input_field_count(source),
                "default_change_allowed_by_budget": False,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_fixture_text_returned": False,
                "raw_document_text_returned": False,
                "raw_model_output_returned": False,
            },
            "budget_rows": budget_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "source_links": {
                "fixture_regression": "/api/v1/maintenance/legal-review-benchmark/fixture-regression",
                "cheap_first_benchmark_gate": "/api/v1/aihub/models/legal-fixture-cheap-first-benchmark-gate",
                "default_promotion_packet": "/api/v1/aihub/models/legal-fixture-cheap-first-default-promotion-packet",
                "small_document_runbook": "/api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence",
                "regression_budget": "/api/v1/aihub/models/legal-fixture-cheap-first-regression-budget",
            },
            "recommended_actions": self._recommended_actions(status, blocking, warnings, budget_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_document_case_ids": False,
                "returns_fact_consistency_case_ids": False,
                "returns_raw_fixture_text": False,
                "returns_document_snippets": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "model_calls": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "output_scope": "fixture ids, source statuses, regression deltas, cost metadata, counts, reason codes, and review actions only",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "maintainer_approval_claimed": False,
                "public_benchmark_score_claimed": False,
                "production_legal_quality_claimed": False,
                "live_gateway_execution_claimed": False,
                "legal_advice_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_fixture_cheap_first_regression_budget.py tests/test_legal_fixture_regression.py tests/test_small_legal_document_benchmark_runbook_evidence.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _budget_rows(
        self,
        gate: dict[str, Any],
        promotion_packet: dict[str, Any],
        regression: dict[str, Any],
    ) -> list[dict[str, Any]]:
        promotion_by_fixture = {
            str(item.get("fixture_id")): item
            for item in promotion_packet.get("promotion_items", [])
            if isinstance(item, dict) and item.get("fixture_id")
        }
        regression_by_fixture = {
            str(row.get("fixture_id")): row
            for row in regression.get("fixture_deltas", [])
            if isinstance(row, dict) and row.get("fixture_id")
        }
        rows: list[dict[str, Any]] = []
        for gate_row in gate.get("gate_rows", []):
            if not isinstance(gate_row, dict) or not gate_row.get("fixture_id"):
                continue
            fixture_id = str(gate_row["fixture_id"])
            promotion_item = promotion_by_fixture.get(fixture_id, {})
            regression_row = regression_by_fixture.get(fixture_id, {})
            reasons = self._reason_codes(gate_row, promotion_item, regression_row)
            budget_status = self._row_status(gate_row, promotion_item, regression_row)
            rows.append(
                {
                    "id": f"regression-budget-{fixture_id}",
                    "fixture_id": fixture_id,
                    "title": gate_row.get("title"),
                    "cheap_first_model": gate_row.get("cheap_first_model"),
                    "model_cost_tier": gate_row.get("model_cost_tier"),
                    "gate_status": str(gate_row.get("gate_status") or "not_run"),
                    "promotion_status": str(promotion_item.get("promotion_status") or "not_ready"),
                    "baseline_status": str(regression_row.get("baseline_status") or "not_run"),
                    "current_status": str(regression_row.get("current_status") or "not_run"),
                    "score_delta": self._number_or_none(regression_row.get("score_delta")),
                    "cost_delta_usd": self._cost_delta(regression_row),
                    "regression_reason_codes": list(regression_row.get("regression_reason_codes") or []),
                    "budget_status": budget_status,
                    "budget_action": self._row_action(budget_status, reasons),
                    "reason_codes": reasons,
                    "default_change_allowed_by_budget": False,
                    "requires_document_benchmark": True,
                    "requires_fact_consistency": True,
                    "requires_regression_pass": True,
                    "gateway_called": False,
                    "raw_fixture_text_returned": False,
                    "raw_model_output_returned": False,
                }
            )
        return rows

    def _checks(
        self,
        gate: dict[str, Any],
        promotion_packet: dict[str, Any],
        regression: dict[str, Any],
        runbook: dict[str, Any],
        budget_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            self._check(
                "fixture-regression-pass",
                str(regression.get("status") or "not_run"),
                "Fixture regression comparison passed or improved.",
                "Run baseline and current fixture batches or review regression warnings before default promotion.",
                "Fixture regression introduced blockers for cheap-first legal defaults.",
                self._list(regression.get("regressed_fixture_ids")),
            ),
            self._check(
                "cheap-first-benchmark-gate-ready",
                str(gate.get("status") or "not_run"),
                "Cheap-first benchmark gate is ready.",
                "Cheap-first benchmark gate still requires fixture, document, fact, or calibration review.",
                "Cheap-first benchmark gate has blocking evidence.",
                self._list(gate.get("blocking_check_ids") or gate.get("blocked_fixture_ids")),
            ),
            self._check(
                "default-promotion-packet-reviewed",
                str(promotion_packet.get("status") or "not_ready"),
                "Default-promotion packet is ready for maintainer review.",
                "Default-promotion packet is not ready or awaits maintainer review.",
                "Default-promotion packet has blocking evidence.",
                self._list(promotion_packet.get("blocked_item_ids")),
            ),
            self._check(
                "small-document-runbook-ready",
                str(runbook.get("status") or "review_required"),
                "Small legal-document runbook evidence is ready.",
                "Run or review the small legal-document benchmark runbook before promoting defaults.",
                "Small legal-document runbook has blocking evidence.",
                self._list(runbook.get("blocking_check_ids")),
            ),
            {
                "id": "serial-low-resource-budget",
                "source_key": "regression_budget",
                "status": "pass" if budget_rows else "warn",
                "source_status": "pass" if budget_rows else "not_run",
                "decision_effect": "supports_laptop_safe_review" if budget_rows else "requires_fixture_rows",
                "reason": (
                    "Budget rows keep legal fixture default review serial and laptop-safe."
                    if budget_rows
                    else "No fixture budget rows are available yet."
                ),
                "source_blocking_ids": [],
                "source_warning_ids": [] if budget_rows else ["fixture-budget-rows-missing"],
            },
        ]

    def _check(
        self,
        check_id: str,
        source_status: str,
        pass_reason: str,
        warn_reason: str,
        fail_reason: str,
        blocking_ids: list[str],
    ) -> dict[str, Any]:
        normalized = source_status.strip().lower()
        if normalized in BLOCKING_STATUSES or blocking_ids:
            status = "fail"
            decision_effect = "blocks_default_changes"
            reason = fail_reason
        elif normalized in REVIEW_STATUSES:
            status = "warn"
            decision_effect = "requires_maintainer_review"
            reason = warn_reason
        elif normalized in {"pass", "ready", "ok", "success"}:
            status = "pass"
            decision_effect = "supports_current_defaults"
            reason = pass_reason
        else:
            status = "warn"
            decision_effect = "requires_maintainer_review"
            reason = "Source status is unrecognized and needs maintainer review."
        return {
            "id": check_id,
            "source_key": check_id.replace("-", "_"),
            "status": status,
            "source_status": normalized or "missing",
            "decision_effect": decision_effect,
            "reason": reason,
            "source_blocking_ids": blocking_ids if status == "fail" else [],
            "source_warning_ids": [] if status != "warn" else [check_id],
        }

    def _status(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        budget_rows: list[dict[str, Any]],
    ) -> str:
        if blocking or any(row["budget_status"] == "blocked" for row in budget_rows):
            return "blocked"
        if not budget_rows or all(row["budget_status"] == "not_run" for row in budget_rows):
            return "not_ready"
        if warnings or any(row["budget_status"] == "review_required" for row in budget_rows):
            return "review_required"
        return "ready_for_maintainer_review"

    def _row_status(
        self,
        gate_row: dict[str, Any],
        promotion_item: dict[str, Any],
        regression_row: dict[str, Any],
    ) -> str:
        gate_status = str(gate_row.get("gate_status") or "not_run")
        promotion_status = str(promotion_item.get("promotion_status") or "not_ready")
        regression_reasons = list(regression_row.get("regression_reason_codes") or [])
        current_status = str(regression_row.get("current_status") or "not_run")
        if gate_status == "blocked" or promotion_status == "blocked" or regression_reasons:
            return "blocked"
        if gate_status == "not_run" or current_status == "not_run":
            return "not_run"
        if gate_status != "pass" or promotion_status != "ready_for_maintainer_review":
            return "review_required"
        return "pass"

    def _reason_codes(
        self,
        gate_row: dict[str, Any],
        promotion_item: dict[str, Any],
        regression_row: dict[str, Any],
    ) -> list[str]:
        reasons = []
        gate_status = str(gate_row.get("gate_status") or "not_run")
        promotion_status = str(promotion_item.get("promotion_status") or "not_ready")
        regression_reasons = list(regression_row.get("regression_reason_codes") or [])
        if gate_status == "pass":
            reasons.append("benchmark-gate-pass")
        elif gate_status == "blocked":
            reasons.append("benchmark-gate-blocked")
        else:
            reasons.append("benchmark-gate-review")
        if promotion_status == "ready_for_maintainer_review":
            reasons.append("promotion-packet-ready-for-review")
        elif promotion_status == "blocked":
            reasons.append("promotion-packet-blocked")
        else:
            reasons.append("promotion-packet-not-ready")
        if regression_reasons:
            reasons.extend(f"regression-{reason}" for reason in regression_reasons[:4])
        elif str(regression_row.get("current_status") or "not_run") == "not_run":
            reasons.append("regression-current-not-run")
        else:
            reasons.append("regression-stable")
        return reasons

    def _row_action(self, status: str, reasons: list[str]) -> str:
        if status == "blocked":
            return "block_default_change_until_fixture_regression_and_gate_blockers_are_fixed"
        if status == "not_run":
            return "run_baseline_and_current_cheap_first_fixture_batches"
        if status == "review_required":
            return "attach_runbook_and_maintainer_review_before_default_change"
        if "promotion-packet-ready-for-review" in reasons:
            return "queue_for_maintainer_review_without_writing_configuration"
        return "keep_current_cheap_first_default_and_archive_evidence"

    def _recommended_actions(
        self,
        status: str,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        budget_rows: list[dict[str, Any]],
    ) -> list[str]:
        if status == "blocked":
            targets = [
                row["fixture_id"]
                for row in budget_rows
                if row["budget_status"] == "blocked"
            ][:4]
            prefix = "Block cheap-first default promotion until blocking budget rows are fixed"
            return [prefix + (": " + ", ".join(targets) if targets else ".")]
        if status == "not_ready":
            return ["Run baseline/current cheap-first fixture batches and the small document runbook before reviewing default changes."]
        if warnings:
            return [
                "Review low-resource budget warnings before default changes: "
                + ", ".join(check["id"] for check in warnings[:4])
                + "."
            ]
        return ["Budget is ready for maintainer review; keep this packet as evidence and do not write configuration from it."]

    def _source_dict(self, source: dict[str, Any], *keys: str) -> dict[str, Any] | None:
        for key in keys:
            value = source.get(key)
            if isinstance(value, dict):
                return value
        return None

    def _summary_int(self, source: dict[str, Any], key: str) -> int:
        summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
        return self._safe_int(summary.get(key))

    def _summary_value(self, source: dict[str, Any], key: str, default: str) -> str:
        summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
        return str(summary.get(key) or default)

    def _max_parallel_requests(self, gate: dict[str, Any], runbook: dict[str, Any]) -> int:
        gate_summary = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}
        runbook_summary = runbook.get("summary") if isinstance(runbook.get("summary"), dict) else {}
        values = [
            self._safe_int(gate_summary.get("max_parallel_requests")),
            self._safe_int(runbook_summary.get("max_parallel_requests")),
        ]
        known = [value for value in values if value > 0]
        return min(known) if known else 1

    def _cost_delta(self, row: dict[str, Any]) -> float | None:
        baseline = self._number_or_none(row.get("baseline_observed_cost_usd"))
        current = self._number_or_none(row.get("current_observed_cost_usd"))
        if baseline is None or current is None:
            return None
        return round(current - baseline, 8)

    def _raw_input_field_count(self, value: Any) -> int:
        if isinstance(value, dict):
            total = 0
            for key, nested in value.items():
                if str(key).lower() in RAW_INPUT_FIELD_NAMES:
                    total += 1
                total += self._raw_input_field_count(nested)
            return total
        if isinstance(value, list):
            return sum(self._raw_input_field_count(item) for item in value)
        if isinstance(value, str) and SENSITIVE_PATTERN.search(value):
            return 1
        return 0

    def _list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item is not None][:20]

    def _safe_int(self, value: Any) -> int:
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, float):
            return max(0, int(value))
        return 0

    def _number_or_none(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return round(float(value), 8)
        return None
