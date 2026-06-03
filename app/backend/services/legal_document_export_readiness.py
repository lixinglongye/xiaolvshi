from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SUPPORTED_EXPORT_FORMATS = ("docx", "pdf", "markdown", "json")


@dataclass(frozen=True)
class ExportGate:
    id: str
    title: str
    required_field: str
    pass_values: tuple[Any, ...]
    blocking: bool
    reviewer_action: str

    def to_api(self, payload: dict[str, Any]) -> dict[str, Any]:
        value = payload.get(self.required_field)
        passed = value in self.pass_values
        data = asdict(self)
        data["pass_values"] = list(self.pass_values)
        data["observed_value"] = value
        data["status"] = "pass" if passed else "fail"
        data["blocks_export"] = self.blocking and not passed
        return data


class LegalDocumentExportReadinessService:
    """Evaluate export gates for generated legal documents without reading files."""

    def build_readiness(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        gates = [gate.to_api(payload) for gate in self._gates()]
        format_status = self._format_status(payload.get("export_format"))
        blockers = [gate for gate in gates if gate["blocks_export"]]
        if format_status["blocks_export"]:
            blockers.append(format_status)

        if not payload:
            status = "template"
        elif blockers:
            status = "blocked"
        else:
            status = "ready"

        return {
            "status": status,
            "summary": {
                "gate_count": len(gates) + 1,
                "passed_gate_count": sum(1 for gate in gates if gate["status"] == "pass")
                + (0 if format_status["blocks_export"] else 1),
                "blocking_gate_count": len(blockers),
                "supported_export_formats": list(SUPPORTED_EXPORT_FORMATS),
                "ready_for_final_export": status == "ready",
            },
            "format_gate": format_status,
            "gates": gates,
            "blocking_items": [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "observed_value": item.get("observed_value"),
                    "reviewer_action": item["reviewer_action"],
                }
                for item in blockers
            ],
            "audit_record_requirements": [
                {
                    "field": "reviewed_version_id",
                    "reason": "Links the exported file to the exact lawyer-reviewed version.",
                },
                {
                    "field": "export_format",
                    "reason": "Allows later verification that the client received the intended file type.",
                },
                {
                    "field": "export_decision",
                    "reason": "Records whether export was approved, blocked, or revised.",
                },
                {
                    "field": "redaction_status",
                    "reason": "Confirms personal or confidential fields were minimized before delivery.",
                },
            ],
            "next_actions": self._next_actions(status, blockers),
            "validation_commands": [
                "python -m pytest tests/test_legal_document_export_readiness.py -q",
                "python -m pytest tests/test_legal_document_template_matrix.py tests/test_client_delivery_risk_checklist.py -q",
            ],
            "privacy_note": (
                "The export readiness payload stores booleans, status labels, version IDs, and format names only. "
                "It must not store raw legal text, party identifiers, full attachments, model outputs, API keys, "
                "login credentials, or user contact details."
            ),
        }

    def _gates(self) -> tuple[ExportGate, ...]:
        return (
            ExportGate(
                id="required-fields-complete",
                title="Required template fields are complete",
                required_field="required_fields_complete",
                pass_values=(True,),
                blocking=True,
                reviewer_action="Collect missing template variables before export.",
            ),
            ExportGate(
                id="pre-generation-blockers-cleared",
                title="Template blockers are cleared",
                required_field="blockers_cleared",
                pass_values=(True,),
                blocking=True,
                reviewer_action="Resolve unresolved parties, claims, evidence, authorization, or jurisdiction blockers.",
            ),
            ExportGate(
                id="lawyer-review-passed",
                title="Lawyer review passed",
                required_field="lawyer_review_status",
                pass_values=("pass", "approved"),
                blocking=True,
                reviewer_action="Keep the document in draft state until a responsible lawyer approves it.",
            ),
            ExportGate(
                id="source-support-complete",
                title="Citation and evidence support is complete",
                required_field="source_support_complete",
                pass_values=(True,),
                blocking=True,
                reviewer_action="Link client-visible conclusions to evidence, source citations, or explicit caveats.",
            ),
            ExportGate(
                id="privacy-redaction-passed",
                title="Privacy and metadata redaction passed",
                required_field="privacy_redaction_status",
                pass_values=("pass", "approved", "not_required"),
                blocking=True,
                reviewer_action="Review headers, footers, comments, metadata, and attachments before export.",
            ),
            ExportGate(
                id="version-locked",
                title="Reviewed version is locked",
                required_field="version_locked",
                pass_values=(True,),
                blocking=True,
                reviewer_action="Lock the reviewed version so the exported file matches the approved draft.",
            ),
        )

    def _format_status(self, export_format: Any) -> dict[str, Any]:
        observed = str(export_format or "").strip().lower()
        supported = observed in SUPPORTED_EXPORT_FORMATS
        return {
            "id": "supported-export-format",
            "title": "Export format is supported",
            "observed_value": observed or None,
            "supported_values": list(SUPPORTED_EXPORT_FORMATS),
            "status": "pass" if supported else "fail",
            "blocks_export": not supported,
            "reviewer_action": "Choose a supported export format before final delivery.",
        }

    def _next_actions(self, status: str, blockers: list[dict[str, Any]]) -> list[str]:
        if status == "template":
            return [
                "Send export status metadata after template generation, lawyer review, and redaction checks finish.",
                "Keep generated documents in draft state until all blocking gates pass.",
            ]
        if blockers:
            return [
                "Block final export and show the blocking gate IDs to the reviewer.",
                "Regenerate, revise, or reroute to lawyer review before trying export again.",
                "Store the blocked decision in the document audit trail.",
            ]
        return [
            "Allow final export for the reviewed and locked version.",
            "Archive export format, reviewed version ID, redaction status, and delivery decision.",
        ]
