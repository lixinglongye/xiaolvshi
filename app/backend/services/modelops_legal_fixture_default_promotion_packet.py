from __future__ import annotations

import re
from typing import Any

from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b",
    re.IGNORECASE,
)


class ModelOpsLegalFixtureDefaultPromotionPacketService:
    """Build maintainer-only promotion packets from the legal fixture gate."""

    def __init__(
        self,
        gate_service: ModelOpsLegalFixtureCheapFirstBenchmarkGateService | None = None,
    ) -> None:
        self.gate_service = gate_service or ModelOpsLegalFixtureCheapFirstBenchmarkGateService()

    def build_packet(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        gate = self._gate(data)
        gate_status = str(gate.get("status") or "not_run")
        summary = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}
        document_summary = gate.get("document_benchmark_summary")
        if not isinstance(document_summary, dict):
            document_summary = {}
        fact_consistency_summary = gate.get("fact_consistency_summary")
        if not isinstance(fact_consistency_summary, dict):
            fact_consistency_summary = {}
        local_rule_baseline_summary = gate.get("local_rule_baseline_summary")
        if not isinstance(local_rule_baseline_summary, dict):
            local_rule_baseline_summary = {}
        privacy_boundary = gate.get("privacy_boundary") if isinstance(gate.get("privacy_boundary"), dict) else {}

        promotion_items = [
            self._promotion_item(row, gate, document_summary, fact_consistency_summary, local_rule_baseline_summary)
            for row in self._gate_rows(gate)
        ]
        ready_items = [item for item in promotion_items if item["promotion_status"] == "ready_for_maintainer_review"]
        blocked_items = [item for item in promotion_items if item["promotion_status"] == "blocked"]
        review_items = [item for item in promotion_items if item["promotion_status"] == "review_required"]
        not_ready_items = [item for item in promotion_items if item["promotion_status"] == "not_ready"]
        status = self._status(gate_status, bool(gate.get("default_change_evidence_allowed")), promotion_items)

        return {
            "status": status,
            "decision": {
                "status": status,
                "label": self._label(status),
                "approval_required": True,
                "configuration_change_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
                "default_change_allowed_by_packet": False,
                "requires_gate_ready": True,
                "requires_document_benchmark_pass": True,
                "requires_document_coverage_ready": True,
                "requires_fact_consistency_pass": True,
                "requires_local_rule_baseline_pass": True,
                "requires_cheap_first_calibration_pass": True,
            },
            "method": {
                "type": "modelops-legal-fixture-default-promotion-packet",
                "notes": [
                    "Consumes the metadata-only legal fixture cheap-first benchmark gate.",
                    "Creates maintainer review items for cheap-first default evidence but never applies configuration.",
                    "Requires fixture gate pass, document benchmark pass, fact consistency pass, local rule baseline pass, cheap-first calibration pass, ready document coverage, and privacy-safe boundaries.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, a gateway, or the network.",
                ],
            },
            "summary": {
                "promotion_item_count": len(promotion_items),
                "ready_for_review_count": len(ready_items),
                "blocked_count": len(blocked_items),
                "review_required_count": len(review_items),
                "not_ready_count": len(not_ready_items),
                "source_gate_status": gate_status,
                "source_default_change_evidence_allowed": bool(gate.get("default_change_evidence_allowed")),
                "source_selected_fixture_count": self._safe_int(summary.get("selected_fixture_count")),
                "source_default_evidence_allowed_count": self._safe_int(summary.get("default_evidence_allowed_count")),
                "document_benchmark_status": str(
                    document_summary.get("status") or summary.get("document_benchmark_status") or "not_run"
                ),
                "document_benchmark_score": self._safe_int(
                    document_summary.get("score") or summary.get("document_benchmark_score")
                ),
                "document_coverage_status": str(
                    document_summary.get("coverage_status") or summary.get("document_coverage_status") or "unknown"
                ),
                "document_coverage_missing_type_count": self._safe_int(
                    document_summary.get("missing_document_type_count")
                    or summary.get("document_coverage_missing_type_count")
                ),
                "fact_consistency_status": str(
                    fact_consistency_summary.get("status") or summary.get("fact_consistency_status") or "not_run"
                ),
                "fact_consistency_score": self._safe_int(
                    fact_consistency_summary.get("score") or summary.get("fact_consistency_score")
                ),
                "fact_consistency_case_count": self._safe_int(
                    fact_consistency_summary.get("case_count") or summary.get("fact_consistency_case_count")
                ),
                "fact_consistency_blocking_case_count": self._safe_int(
                    fact_consistency_summary.get("blocking_case_count")
                    or summary.get("fact_consistency_blocking_case_count")
                ),
                "fact_consistency_amount_mismatch_count": self._safe_int(
                    fact_consistency_summary.get("amount_mismatch_count")
                    or summary.get("fact_consistency_amount_mismatch_count")
                ),
                "fact_consistency_deadline_mismatch_count": self._safe_int(
                    fact_consistency_summary.get("deadline_mismatch_count")
                    or summary.get("fact_consistency_deadline_mismatch_count")
                ),
                "fact_consistency_contradiction_count": self._safe_int(
                    fact_consistency_summary.get("contradiction_count")
                    or summary.get("fact_consistency_contradiction_count")
                ),
                "local_rule_baseline_status": str(
                    local_rule_baseline_summary.get("status")
                    or summary.get("local_rule_baseline_status")
                    or "not_run"
                ),
                "local_rule_baseline_score": self._safe_int(
                    local_rule_baseline_summary.get("score") or summary.get("local_rule_baseline_score")
                ),
                "local_rule_baseline_case_count": self._safe_int(
                    local_rule_baseline_summary.get("case_count") or summary.get("local_rule_baseline_case_count")
                ),
                "local_rule_baseline_blocking_case_count": self._safe_int(
                    local_rule_baseline_summary.get("blocking_case_count")
                    or summary.get("local_rule_baseline_blocking_case_count")
                ),
                "local_rule_baseline_raw_prediction_returned": bool(
                    local_rule_baseline_summary.get("raw_prediction_payload_returned")
                    or summary.get("local_rule_baseline_raw_prediction_returned")
                ),
                "calibration_status": str(summary.get("calibration_status") or "not_run"),
                "calibration_task_count": self._safe_int(summary.get("calibration_task_count")),
                "linked_calibration_task_count": self._safe_int(summary.get("linked_calibration_task_count")),
                "calibration_blocking_count": self._safe_int(summary.get("calibration_blocking_count")),
                "calibration_warning_count": self._safe_int(summary.get("calibration_warning_count")),
                "calibration_pass_count": self._safe_int(summary.get("calibration_pass_count")),
                "privacy_boundary_passed": self._privacy_boundary_passed(privacy_boundary),
                "raw_input_field_count": self._safe_int(summary.get("raw_input_field_count")),
                "configuration_written": False,
                "gateway_called": False,
                "traffic_shifted": False,
                "raw_text_returned": False,
                "newapi_called": False,
            },
            "promotion_items": promotion_items,
            "ready_item_ids": [item["id"] for item in ready_items],
            "blocked_item_ids": [item["id"] for item in blocked_items],
            "review_item_ids": [item["id"] for item in review_items],
            "not_ready_item_ids": [item["id"] for item in not_ready_items],
            "required_signoffs": self._required_signoffs(status),
            "evidence_checklist": self._evidence_checklist(
                gate,
                document_summary,
                fact_consistency_summary,
                local_rule_baseline_summary,
                privacy_boundary,
            ),
            "recommended_actions": self._recommended_actions(status, promotion_items),
            "source_gate_links": {
                "cheap_first_benchmark_gate": "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
                "cheap_first_calibration": "/api/v1/aihub/models/cheap-first-calibration",
                "document_benchmark_suite": "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                "document_fixture_local_baseline": "/api/v1/maintenance/legal-review-benchmark/document-fixtures/local-baseline",
                "document_coverage": "/api/v1/maintenance/legal-review-benchmark/document-coverage",
                "document_fact_consistency": "/api/v1/maintenance/legal-review-benchmark/document-fact-consistency",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_document_case_ids": True,
                "returns_fact_consistency_case_ids": True,
                "returns_local_rule_baseline_case_ids": True,
                "returns_calibration_task_ids": True,
                "returns_local_rule_predictions": False,
                "returns_raw_fixture_text": False,
                "returns_calibration_payloads": False,
                "returns_document_snippets": False,
                "returns_candidate_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "network_called": False,
                "newapi_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "output_scope": "promotion item ids, fixture ids, document status counts, model ids, cost tiers, blockers, and signoff roles only",
            },
            "claim_boundary": {
                "maintainer_approval_claimed": False,
                "automatic_default_change_claimed": False,
                "configuration_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_scores_claimed": False,
                "legal_document_benchmark_scores_claimed": False,
                "fact_consistency_benchmark_scores_claimed": False,
                "local_rule_baseline_accuracy_claimed": False,
                "production_accuracy_claimed": False,
                "legal_advice_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_fixture_default_promotion_packet.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_gemini_newapi_cheap_first_calibration.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _gate(self, data: dict[str, Any]) -> dict[str, Any]:
        for key in (
            "legal_fixture_cheap_first_benchmark_gate",
            "cheap_first_benchmark_gate",
            "source_gate",
            "gate",
        ):
            value = data.get(key)
            if isinstance(value, dict) and value.get("summary"):
                return value
        return self.gate_service.build_gate(data or None)

    def _gate_rows(self, gate: dict[str, Any]) -> list[dict[str, Any]]:
        return [row for row in gate.get("gate_rows", []) if isinstance(row, dict)]

    def _promotion_item(
        self,
        row: dict[str, Any],
        gate: dict[str, Any],
        document_summary: dict[str, Any],
        fact_consistency_summary: dict[str, Any],
        local_rule_baseline_summary: dict[str, Any],
    ) -> dict[str, Any]:
        gate_status = str(row.get("gate_status") or "not_run")
        document_status = str(
            document_summary.get("status")
            or (gate.get("summary") or {}).get("document_benchmark_status")
            or "not_run"
        )
        coverage_status = str(
            document_summary.get("coverage_status")
            or (gate.get("summary") or {}).get("document_coverage_status")
            or "unknown"
        )
        fact_consistency_status = str(
            fact_consistency_summary.get("status")
            or (gate.get("summary") or {}).get("fact_consistency_status")
            or "not_run"
        )
        local_rule_baseline_status = str(
            local_rule_baseline_summary.get("status")
            or (gate.get("summary") or {}).get("local_rule_baseline_status")
            or "not_run"
        )
        reason_codes = self._item_reason_codes(
            row,
            gate,
            document_status,
            coverage_status,
            fact_consistency_status,
            local_rule_baseline_status,
        )
        promotion_status = self._promotion_status(row, gate, reason_codes)
        fixture_id = str(row.get("fixture_id") or "unknown-fixture")
        return {
            "id": f"legal-fixture-promotion-{fixture_id}",
            "fixture_id": fixture_id,
            "title": str(row.get("title") or fixture_id),
            "task": str(row.get("task") or "unknown"),
            "matter_type": str(row.get("matter_type") or "unknown"),
            "proposed_default_model": row.get("cheap_first_model"),
            "proposed_cost_tier": row.get("cheap_first_cost_tier"),
            "gate_status": gate_status,
            "document_benchmark_status": document_status,
            "document_coverage_status": coverage_status,
            "fact_consistency_status": fact_consistency_status,
            "local_rule_baseline_status": local_rule_baseline_status,
            "calibration_status": str(row.get("calibration_status") or "not_mapped"),
            "linked_calibration_task_ids": [str(item) for item in row.get("linked_calibration_task_ids", [])],
            "calibration_decisions": [str(item) for item in row.get("calibration_decisions", [])],
            "calibration_release_gates": [str(item) for item in row.get("calibration_release_gates", [])],
            "promotion_status": promotion_status,
            "default_change_evidence_allowed": bool(row.get("default_change_evidence_allowed"))
            and bool(gate.get("default_change_evidence_allowed")),
            "premium_escalation_candidate": bool(row.get("premium_escalation_candidate")),
            "required_evidence": [
                "legal fixture cheap-first gate pass",
                "document benchmark pass",
                "fact consistency pass",
                "local rule baseline pass",
                "cheap-first calibration pass",
                "document coverage ready",
                "metadata-only privacy boundary pass",
                "maintainer signoff outside this service",
            ],
            "required_signoffs": self._item_required_signoffs(promotion_status),
            "reason_codes": reason_codes,
            "configuration_change_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
            "action": self._item_action(promotion_status, row),
        }

    def _item_reason_codes(
        self,
        row: dict[str, Any],
        gate: dict[str, Any],
        document_status: str,
        coverage_status: str,
        fact_consistency_status: str,
        local_rule_baseline_status: str,
    ) -> list[str]:
        codes = [str(code) for code in row.get("reason_codes", []) if str(code).strip()]
        if row.get("gate_status") != "pass":
            codes.append("fixture-gate-not-pass")
        if not gate.get("default_change_evidence_allowed"):
            codes.append("packet-source-default-change-not-allowed")
        if document_status != "pass":
            codes.append("document-benchmark-not-pass")
        if fact_consistency_status != "pass":
            codes.append("fact-consistency-not-pass")
        if local_rule_baseline_status != "pass":
            codes.append("local-rule-baseline-not-pass")
        if row.get("calibration_status") != "pass":
            codes.append("cheap-first-calibration-not-pass")
        if coverage_status != "ready":
            codes.append("document-coverage-not-ready")
        if row.get("premium_escalation_candidate"):
            codes.append("premium-escalation-review-required")
        if self._contains_sensitive(row):
            codes.append("source-row-sensitive-value-rejected")
        return _dedupe(codes) or ["promotion-packet-ready"]

    def _promotion_status(self, row: dict[str, Any], gate: dict[str, Any], reason_codes: list[str]) -> str:
        if "source-row-sensitive-value-rejected" in reason_codes:
            return "blocked"
        if row.get("gate_status") == "blocked" or gate.get("status") == "blocked":
            return "blocked"
        if gate.get("default_change_evidence_allowed") and row.get("default_change_evidence_allowed"):
            review_ready_reason_codes = {
                "known-low-cost-gemini-cheap-first",
                "premium-escalation-candidate",
                "premium-escalation-review-required",
                "promotion-packet-ready",
                "public-source-license-review",
                "cheap-first-calibration-pass",
            }
            if reason_codes == ["promotion-packet-ready"] or all(
                code in review_ready_reason_codes
                for code in reason_codes
            ):
                return "ready_for_maintainer_review"
            return "review_required"
        if row.get("gate_status") == "review_required" or gate.get("status") == "ready_with_watchlist":
            return "review_required"
        return "not_ready"

    def _status(
        self,
        gate_status: str,
        source_default_allowed: bool,
        promotion_items: list[dict[str, Any]],
    ) -> str:
        if any(item["promotion_status"] == "blocked" for item in promotion_items) or gate_status == "blocked":
            return "blocked"
        if promotion_items and all(item["promotion_status"] == "ready_for_maintainer_review" for item in promotion_items):
            return "ready_for_maintainer_review"
        if any(item["promotion_status"] == "review_required" for item in promotion_items):
            return "review_required"
        if source_default_allowed:
            return "review_required"
        return "not_ready"

    def _label(self, status: str) -> str:
        return {
            "ready_for_maintainer_review": "legal fixture default promotion packet ready for maintainer review",
            "review_required": "legal fixture default promotion requires maintainer review",
            "blocked": "legal fixture default promotion blocked",
            "not_ready": "legal fixture default promotion evidence not ready",
        }.get(status, "legal fixture default promotion status unknown")

    def _evidence_checklist(
        self,
        gate: dict[str, Any],
        document_summary: dict[str, Any],
        fact_consistency_summary: dict[str, Any],
        local_rule_baseline_summary: dict[str, Any],
        privacy_boundary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        summary = gate.get("summary") if isinstance(gate.get("summary"), dict) else {}
        items = [
            (
                "legal-fixture-gate-ready",
                gate.get("status") == "ready" and gate.get("default_change_evidence_allowed") is True,
                str(gate.get("status") or "not_run"),
            ),
            (
                "document-benchmark-pass",
                (document_summary.get("status") or summary.get("document_benchmark_status")) == "pass",
                str(document_summary.get("status") or summary.get("document_benchmark_status") or "not_run"),
            ),
            (
                "document-coverage-ready",
                (document_summary.get("coverage_status") or summary.get("document_coverage_status")) == "ready"
                and self._safe_int(
                    document_summary.get("missing_document_type_count")
                    or summary.get("document_coverage_missing_type_count")
                )
                == 0,
                str(document_summary.get("coverage_status") or summary.get("document_coverage_status") or "unknown"),
            ),
            (
                "fact-consistency-pass",
                (fact_consistency_summary.get("status") or summary.get("fact_consistency_status")) == "pass",
                str(fact_consistency_summary.get("status") or summary.get("fact_consistency_status") or "not_run"),
            ),
            (
                "local-rule-baseline-pass",
                (local_rule_baseline_summary.get("status") or summary.get("local_rule_baseline_status")) == "pass",
                str(
                    local_rule_baseline_summary.get("status")
                    or summary.get("local_rule_baseline_status")
                    or "not_run"
                ),
            ),
            (
                "cheap-first-calibration-pass",
                summary.get("calibration_status") == "pass"
                and self._safe_int(summary.get("calibration_blocking_count")) == 0
                and self._safe_int(summary.get("calibration_warning_count")) == 0,
                str(summary.get("calibration_status") or "not_run"),
            ),
            (
                "metadata-only-boundary",
                self._privacy_boundary_passed(privacy_boundary),
                "metadata_only",
            ),
        ]
        return [
            {
                "id": item_id,
                "status": "pass" if passed else "blocked",
                "passed": passed,
                "source_status": source_status,
            }
            for item_id, passed, source_status in items
        ]

    def _privacy_boundary_passed(self, privacy_boundary: dict[str, Any]) -> bool:
        if not privacy_boundary:
            return False
        forbidden_flags = (
            "returns_raw_fixture_text",
            "returns_calibration_payloads",
            "returns_document_snippets",
            "returns_candidate_text",
            "returns_prompt_text",
            "returns_raw_model_output",
            "returns_gateway_payloads",
            "returns_credentials",
            "network_called",
            "newapi_called",
        )
        return privacy_boundary.get("metadata_only") is True and not any(
            privacy_boundary.get(flag) is True for flag in forbidden_flags
        )

    def _required_signoffs(self, status: str) -> list[str]:
        if status == "ready_for_maintainer_review":
            return ["maintainer_owner", "model_ops_reviewer", "legal_quality_reviewer"]
        return ["model_ops_reviewer"]

    def _item_required_signoffs(self, promotion_status: str) -> list[str]:
        if promotion_status == "ready_for_maintainer_review":
            return ["maintainer_owner", "model_ops_reviewer", "legal_quality_reviewer"]
        if promotion_status == "blocked":
            return []
        return ["model_ops_reviewer"]

    def _item_action(self, promotion_status: str, row: dict[str, Any]) -> str:
        task = str(row.get("task") or "unknown")
        model = str(row.get("cheap_first_model") or "cheap-first model")
        if promotion_status == "ready_for_maintainer_review":
            return f"Review {model} as the cheap-first default evidence for {task}; apply any config change outside this service."
        if promotion_status == "blocked":
            return f"Do not promote the {task} default until blocking fixture or document benchmark evidence is fixed."
        if promotion_status == "review_required":
            return f"Review watchlist evidence before using {model} as default-change support for {task}."
        return f"Run required fixture and document benchmark evidence before reviewing {task} default promotion."

    def _recommended_actions(self, status: str, promotion_items: list[dict[str, Any]]) -> list[str]:
        if status == "ready_for_maintainer_review":
            return [
                "Collect maintainer, model-ops, and legal-quality signoff before changing defaults outside this service.",
                "Keep this packet archived with the legal fixture gate and document benchmark evidence.",
            ]
        if status == "blocked":
            return [
                "Fix blocked legal fixture, document benchmark, or fact consistency evidence before any cheap-first default promotion.",
                "Rerun the legal fixture default promotion packet after blockers clear.",
            ]
        if status == "review_required":
            return [
                "Review watchlist rows before treating cheap-first evidence as promotion-ready.",
                "Keep premium escalation candidates explicit-only unless separate exception evidence is attached.",
            ]
        return [
            "Run selected legal fixtures, the document benchmark suite, and fact consistency benchmark before requesting default promotion review.",
            "Do not write configuration or shift traffic from this packet.",
        ]

    def _contains_sensitive(self, value: Any) -> bool:
        if isinstance(value, dict):
            return any(self._contains_sensitive(child) for child in value.values())
        if isinstance(value, list):
            return any(self._contains_sensitive(item) for item in value[:50])
        return isinstance(value, str) and bool(SENSITIVE_PATTERN.search(value))

    def _safe_int(self, value: Any) -> int:
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, float):
            return max(0, int(value))
        return 0


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
