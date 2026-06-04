from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any

from services.legal_rag_selected_source_validation import validate_selected_source_citations


PRIVACY_BOUNDARY = {
    "raw_legal_text_included": False,
    "user_claims_included": False,
    "pii_included": False,
    "output_scope": "selected-source validation status, counts, reason codes, and safe source identifiers only",
}


class DeepReviewSelectedSourceBindingService:
    """Attach selected-source citation validation to deep-review reports."""

    def bind(
        self,
        *,
        report: Mapping[str, Any] | None,
        request_metadata: Mapping[str, Any] | None,
        block_on_failure: bool = True,
    ) -> dict[str, Any]:
        safe_report = copy.deepcopy(dict(report or {}))
        citation_map = self._citation_map(safe_report)
        generation_plan = self._generation_plan(safe_report)
        validation = validate_selected_source_citations(
            request_metadata=request_metadata,
            citation_map=citation_map,
            generation_plan=generation_plan,
        )
        binding = self._binding_payload(validation, block_on_failure=block_on_failure)

        safe_report.setdefault("report_meta", {})
        if not isinstance(safe_report["report_meta"], dict):
            safe_report["report_meta"] = {}
        safe_report["report_meta"]["selected_source_validation"] = binding

        safe_report.setdefault("legal_rag", {})
        if not isinstance(safe_report["legal_rag"], dict):
            safe_report["legal_rag"] = {}
        safe_report["legal_rag"]["selected_source_validation"] = binding

        if binding["delivery_status"] == "blocked":
            blockers = safe_report.setdefault("delivery_blockers", [])
            if isinstance(blockers, list) and "selected_source_validation_blocked" not in blockers:
                blockers.append("selected_source_validation_blocked")

        return {
            "status": binding["delivery_status"],
            "report": safe_report,
            "binding": binding,
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def evaluate(
        self,
        *,
        report: Mapping[str, Any] | None,
        request_metadata: Mapping[str, Any] | None,
        block_on_failure: bool = True,
    ) -> dict[str, Any]:
        bound = self.bind(report=report, request_metadata=request_metadata, block_on_failure=block_on_failure)
        return {
            "status": bound["status"],
            "binding": bound["binding"],
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _binding_payload(self, validation: dict[str, Any], *, block_on_failure: bool) -> dict[str, Any]:
        validation_status = str(validation.get("status") or "blocked")
        delivery_status = "blocked" if block_on_failure and validation_status == "blocked" else "review_required"
        if validation_status == "pass":
            delivery_status = "ready"
        elif validation_status == "pass_with_warnings" and not block_on_failure:
            delivery_status = "review_required"
        elif validation_status == "pass_with_warnings":
            delivery_status = "review_required"

        return {
            "status": validation_status,
            "delivery_status": delivery_status,
            "reason_codes": list(validation.get("reason_codes") or []),
            "selected_source_ids": list(validation.get("selected_source_ids") or []),
            "cited_source_ids": list(validation.get("cited_source_ids") or []),
            "unexpected_source_ids": list(validation.get("unexpected_source_ids") or []),
            "missing_selected_source_ids": list(validation.get("missing_selected_source_ids") or []),
            "stale_source_ids": list(validation.get("stale_source_ids") or []),
            "unknown_source_ids": list(validation.get("unknown_source_ids") or []),
            "counts": dict(validation.get("counts") or {}),
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _citation_map(self, report: Mapping[str, Any]) -> Any:
        for key in ("citation_map", "citations", "source_citations"):
            if key in report:
                return report.get(key)
        legal_rag = report.get("legal_rag")
        if isinstance(legal_rag, Mapping):
            return legal_rag.get("citation_map") or legal_rag.get("citations")
        return None

    def _generation_plan(self, report: Mapping[str, Any]) -> Any:
        for key in ("generation_plan", "plan", "drafting_plan"):
            if key in report:
                return report.get(key)
        legal_rag = report.get("legal_rag")
        if isinstance(legal_rag, Mapping):
            return legal_rag.get("generation_plan") or legal_rag.get("plan")
        return None


def bind_deep_review_selected_source_validation(
    *,
    report: Mapping[str, Any] | None,
    request_metadata: Mapping[str, Any] | None,
    block_on_failure: bool = True,
) -> dict[str, Any]:
    return DeepReviewSelectedSourceBindingService().bind(
        report=report,
        request_metadata=request_metadata,
        block_on_failure=block_on_failure,
    )
