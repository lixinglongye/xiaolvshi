from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.case_export_readiness import CaseExportReadinessService
from services.deep_review_selected_source_binding import DeepReviewSelectedSourceBindingService


PRIVACY_BOUNDARY = {
    "raw_legal_text_included": False,
    "raw_document_text_included": False,
    "raw_report_returned": False,
    "user_claims_included": False,
    "pii_included": False,
    "model_calls": False,
    "newapi_called": False,
    "gemini_called": False,
    "gateway_calls": False,
    "network_calls": False,
    "credentials_included": False,
    "output_scope": "selected-source binding status, export readiness counts, reason codes, and release action only",
}


class LegalRagExportReadinessPacketService:
    """Join selected-source binding and export readiness into one review packet."""

    def __init__(
        self,
        *,
        binding_service: DeepReviewSelectedSourceBindingService | None = None,
        export_service: CaseExportReadinessService | None = None,
    ) -> None:
        self.binding_service = binding_service or DeepReviewSelectedSourceBindingService()
        self.export_service = export_service or CaseExportReadinessService()

    def build_packet(
        self,
        *,
        report: Mapping[str, Any] | None = None,
        request_metadata: Mapping[str, Any] | None = None,
        block_on_failure: bool = True,
    ) -> dict[str, Any]:
        bound = self.binding_service.bind(
            report=report,
            request_metadata=request_metadata,
            block_on_failure=block_on_failure,
        )
        binding = bound["binding"]
        export_readiness = self.export_service.evaluate(bound["report"])
        checks = self._checks(binding, export_readiness)
        blocker_count = sum(1 for check in checks if check["status"] == "blocked")
        review_count = sum(1 for check in checks if check["status"] == "review_required")
        status = "blocked" if blocker_count else "review_required" if review_count else "ready"
        release_action = self._release_action(status, binding, export_readiness)
        reason_codes = _dedupe(
            [
                *binding.get("reason_codes", []),
                *export_readiness.get("reason_codes", []),
                *[reason for check in checks for reason in check["reason_codes"]],
            ]
        )

        return {
            "id": "legal-rag-export-readiness-packet",
            "title": "Legal RAG export readiness packet",
            "status": status,
            "release_action": release_action,
            "summary": {
                "check_count": len(checks),
                "ready_check_count": sum(1 for check in checks if check["status"] == "ready"),
                "review_check_count": review_count,
                "blocked_check_count": blocker_count,
                "selected_source_count": binding["counts"].get("selected_source_count", 0),
                "cited_source_count": binding["counts"].get("cited_source_count", 0),
                "unexpected_source_count": binding["counts"].get("unexpected_source_count", 0),
                "missing_required_section_count": len(export_readiness.get("missing_sections", [])),
                "reason_code_count": len(reason_codes),
                "raw_report_returned": False,
                "model_calls": False,
                "network_calls": False,
            },
            "checks": checks,
            "selected_source_binding": {
                "status": binding["status"],
                "delivery_status": binding["delivery_status"],
                "reason_codes": list(binding.get("reason_codes") or []),
                "counts": dict(binding.get("counts") or {}),
                "unexpected_source_ids": list(binding.get("unexpected_source_ids") or []),
                "missing_selected_source_ids": list(binding.get("missing_selected_source_ids") or []),
                "stale_source_ids": list(binding.get("stale_source_ids") or []),
                "unknown_source_ids": list(binding.get("unknown_source_ids") or []),
            },
            "export_readiness": {
                "status": export_readiness["status"],
                "present_sections": list(export_readiness.get("present_sections") or []),
                "missing_sections": list(export_readiness.get("missing_sections") or []),
                "selected_source_validation_status": export_readiness.get("selected_source_validation_status"),
                "reason_codes": list(export_readiness.get("reason_codes") or []),
            },
            "linked_release_gates": [
                "legal-rag-selected-source-citation-validation",
                "deep-review-selected-source-binding",
                "case-export-readiness",
                "deep-review-export-readiness-route-gate",
            ],
            "reason_codes": reason_codes,
            "recommended_actions": self._recommended_actions(
                status=status,
                binding=binding,
                export_readiness=export_readiness,
            ),
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_export_readiness_packet.py tests/test_deep_review_selected_source_binding.py tests/test_case_export_readiness.py -q",
                "python -m pytest tests/test_deep_review_export_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py -q",
            ],
        }

    def _checks(self, binding: Mapping[str, Any], export_readiness: Mapping[str, Any]) -> list[dict[str, Any]]:
        binding_status = _normalize_status(binding.get("delivery_status"))
        export_status = _normalize_status(export_readiness.get("status"))
        missing_sections = list(export_readiness.get("missing_sections") or [])
        release_blocked = "release_decision_blocked" in set(export_readiness.get("reason_codes") or [])
        return [
            {
                "id": "selected-source-binding",
                "title": "Selected source binding",
                "status": binding_status,
                "reason_codes": list(binding.get("reason_codes") or []),
                "release_gate_link": "deep-review-selected-source-binding",
            },
            {
                "id": "case-export-readiness",
                "title": "Case export readiness",
                "status": export_status,
                "reason_codes": list(export_readiness.get("reason_codes") or []),
                "release_gate_link": "case-export-readiness",
            },
            {
                "id": "required-export-sections",
                "title": "Required export sections",
                "status": "blocked" if missing_sections else "ready",
                "reason_codes": ["missing_required_export_sections"] if missing_sections else [],
                "release_gate_link": "case-export-readiness",
            },
            {
                "id": "deep-review-route-gate",
                "title": "Deep-review export route gate",
                "status": "blocked" if export_status == "blocked" or release_blocked else "ready",
                "reason_codes": ["deep_review_export_not_ready"] if export_status == "blocked" or release_blocked else [],
                "release_gate_link": "deep-review-export-readiness-route-gate",
            },
            {
                "id": "metadata-only-boundary",
                "title": "Metadata-only boundary",
                "status": "ready",
                "reason_codes": [],
                "release_gate_link": "privacy-retention-rules",
            },
        ]

    def _release_action(
        self,
        status: str,
        binding: Mapping[str, Any],
        export_readiness: Mapping[str, Any],
    ) -> str:
        if status == "ready":
            return "allow_export_after_reviewer_confirmation"
        if binding.get("delivery_status") == "blocked":
            return "block_export_until_selected_sources_are_fixed"
        if export_readiness.get("status") == "blocked":
            return "block_export_until_required_sections_and_release_decision_pass"
        return "review_before_export"

    def _recommended_actions(
        self,
        *,
        status: str,
        binding: Mapping[str, Any],
        export_readiness: Mapping[str, Any],
    ) -> list[str]:
        actions: list[str] = []
        if binding.get("delivery_status") == "blocked":
            actions.append("Fix selected-source citation validation before any client-facing export.")
        if export_readiness.get("missing_sections"):
            actions.append("Regenerate or enrich missing report metadata sections before export.")
        if "release_decision_blocked" in set(export_readiness.get("reason_codes") or []):
            actions.append("Resolve release-decision blockers before serializing any report download.")
        if status == "ready":
            actions.append("Export may proceed after normal reviewer confirmation and route-level readiness check.")
        actions.append("Keep this packet metadata-only; do not attach report text, snippets, prompts, or model outputs.")
        return _dedupe(actions)


def _normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"ready", "pass"}:
        return "ready"
    if text in {"blocked", "fail", "failed"}:
        return "blocked"
    return "review_required"


def _dedupe(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
