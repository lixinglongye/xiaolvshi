from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PRIVACY_BOUNDARY = {
    "raw_document_text_included": False,
    "pii_included": False,
    "output_scope": "section presence, status, reason codes, and reviewer actions only",
}


REQUIRED_SECTIONS = (
    "report_meta",
    "risk_scoring",
    "citations",
    "evidence",
    "release_decision",
)


class CaseExportReadinessService:
    """Check whether a case report has the metadata needed for export review."""

    def evaluate(self, report: Mapping[str, Any] | None = None) -> dict[str, Any]:
        safe_report = report if isinstance(report, Mapping) else {}
        present = [section for section in REQUIRED_SECTIONS if section in safe_report and safe_report.get(section)]
        missing = [section for section in REQUIRED_SECTIONS if section not in present]
        release = safe_report.get("release_decision") if isinstance(safe_report.get("release_decision"), Mapping) else {}
        selected = self._selected_source_status(safe_report)
        reason_codes = []
        if missing:
            reason_codes.append("missing_required_export_sections")
        if str(release.get("status") or "").lower() in {"blocked", "fail", "failed"}:
            reason_codes.append("release_decision_blocked")
        if selected == "blocked":
            reason_codes.append("selected_source_validation_blocked")
        status = "blocked" if reason_codes else "ready"
        if status == "ready" and len(present) < len(REQUIRED_SECTIONS):
            status = "review_required"
        return {
            "status": status,
            "required_sections": list(REQUIRED_SECTIONS),
            "present_sections": present,
            "missing_sections": missing,
            "selected_source_validation_status": selected,
            "reason_codes": reason_codes,
            "recommended_actions": self._actions(reason_codes),
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _selected_source_status(self, report: Mapping[str, Any]) -> str:
        meta = report.get("report_meta") if isinstance(report.get("report_meta"), Mapping) else {}
        validation = meta.get("selected_source_validation") if isinstance(meta.get("selected_source_validation"), Mapping) else {}
        return str(validation.get("delivery_status") or validation.get("status") or "not_run")

    def _actions(self, reason_codes: list[str]) -> list[str]:
        if not reason_codes:
            return ["Export can proceed after normal reviewer confirmation."]
        actions = []
        if "missing_required_export_sections" in reason_codes:
            actions.append("Regenerate or enrich the report with missing metadata sections before export.")
        if "release_decision_blocked" in reason_codes:
            actions.append("Resolve release decision blockers before client-facing export.")
        if "selected_source_validation_blocked" in reason_codes:
            actions.append("Fix selected-source citation validation before exporting the report.")
        return actions
