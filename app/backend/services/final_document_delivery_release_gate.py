from __future__ import annotations

from typing import Any

from services.document_delivery_package_manifest import DocumentDeliveryPackageManifestService
from services.document_version_diff_checklist import DocumentVersionDiffChecklistService
from services.legal_document_export_readiness import LegalDocumentExportReadinessService
from services.quota_delivery_decision import QuotaDeliveryDecisionService


class FinalDocumentDeliveryReleaseGateService:
    """Join final document-delivery checks without reading files or sending delivery."""

    def __init__(
        self,
        manifest_service: DocumentDeliveryPackageManifestService | None = None,
        diff_service: DocumentVersionDiffChecklistService | None = None,
        export_service: LegalDocumentExportReadinessService | None = None,
        quota_service: QuotaDeliveryDecisionService | None = None,
    ) -> None:
        self.manifest_service = manifest_service or DocumentDeliveryPackageManifestService()
        self.diff_service = diff_service or DocumentVersionDiffChecklistService()
        self.export_service = export_service or LegalDocumentExportReadinessService()
        self.quota_service = quota_service or QuotaDeliveryDecisionService()

    def build_gate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        source = payload if isinstance(payload, dict) else {}
        template_mode = not bool(source)
        manifest = self.manifest_service.build_manifest(
            None if template_mode else _first_dict(source, "delivery_package", "package_manifest", "manifest", default=source)
        )
        version_diff = self.diff_service.build_checklist(
            None if template_mode else _first_dict(source, "version_diff", "diff", "version_notes")
        )
        export_readiness = self.export_service.build_readiness(
            None if template_mode else _first_dict(source, "export_readiness", "export_gate", "final_export")
        )
        preliminary_blocked = any(
            item.get("status") == "blocked"
            for item in (manifest, version_diff, export_readiness)
        )
        quota_summary = _first_dict(source, "quota_summary", "quota")
        quota_decision = self._quota_decision(
            source=source,
            quota_summary=quota_summary,
            preliminary_blocked=preliminary_blocked,
            template_mode=template_mode,
        )
        component_gates = [
            self._manifest_component(manifest),
            self._diff_component(version_diff),
            self._export_component(export_readiness),
            self._quota_component(quota_decision, quota_summary, template_mode),
        ]
        status = self._status(component_gates, template_mode)
        blocking_component_ids = [item["id"] for item in component_gates if item["blocks_release"]]

        return {
            "status": status,
            "gate_id": "final-document-delivery-release-gate-v1",
            "summary": {
                "component_gate_count": len(component_gates),
                "ready_component_count": sum(1 for item in component_gates if item["ready"]),
                "blocking_component_count": len(blocking_component_ids),
                "blocking_component_ids": blocking_component_ids,
                "package_release_allowed": status == "ready",
                "final_export_allowed": status == "ready",
                "client_delivery_allowed": status == "ready",
            },
            "component_gates": component_gates,
            "release_decision": self._release_decision(status, quota_decision, blocking_component_ids),
            "audit_record_requirements": self._audit_record_requirements(),
            "recommended_actions": self._recommended_actions(component_gates, status),
            "privacy_boundary": {
                "raw_document_text_included": False,
                "raw_client_contact_included": False,
                "billing_provider_payload_included": False,
                "credential_material_included": False,
                "model_calls": False,
                "network_access": "disabled",
                "reads_files": False,
                "writes_files": False,
                "materializes_export": False,
                "sends_client_delivery": False,
                "output_scope": "component statuses, risk codes, counts, and reviewer actions only",
            },
            "claim_boundary": {
                "final_docx_pdf_generated": False,
                "client_delivery_sent": False,
                "live_payment_provider_settlement_verified": False,
                "legal_advice_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_final_document_delivery_release_gate.py -q",
                "python -m pytest tests/test_document_delivery_package_manifest.py tests/test_document_version_diff_checklist.py tests/test_legal_document_export_readiness.py tests/test_quota_delivery_decision.py -q",
                "python -m compileall services/final_document_delivery_release_gate.py",
            ],
        }

    def _quota_decision(
        self,
        *,
        source: dict[str, Any],
        quota_summary: dict[str, Any],
        preliminary_blocked: bool,
        template_mode: bool,
    ) -> dict[str, Any]:
        if template_mode:
            return {
                "status": "template",
                "action": "deliver_to_client",
                "reason_codes": [],
                "required_next_steps": ["Submit sanitized quota metadata before final delivery release."],
            }
        if not quota_summary:
            return {
                "status": "blocked",
                "action": _text(source.get("action") or "deliver_to_client"),
                "reason_codes": ["quota_summary_missing"],
                "required_next_steps": ["Attach sanitized quota metadata before final delivery release."],
            }
        release_status = "blocked" if preliminary_blocked else "ready"
        return self.quota_service.decide(
            action=_text(source.get("action") or "deliver_to_client"),
            quota_summary=quota_summary,
            release_decision={"status": release_status},
        )

    def _manifest_component(self, manifest: dict[str, Any]) -> dict[str, Any]:
        summary = manifest.get("summary") or {}
        risk_flags = manifest.get("risk_flags") or []
        return {
            "id": "document-delivery-package-manifest",
            "title": "Delivery package manifest",
            "status": manifest.get("status", "template"),
            "ready": manifest.get("status") == "ready",
            "blocks_release": manifest.get("status") == "blocked",
            "blocking_issue_count": summary.get("blocking_risk_count", 0),
            "blocker_ids": [flag.get("id") for flag in risk_flags if flag.get("severity") == "blocking"],
            "reviewer_actions": [item.get("action") for item in manifest.get("recommended_actions") or [] if item.get("action")],
        }

    def _diff_component(self, version_diff: dict[str, Any]) -> dict[str, Any]:
        summary = version_diff.get("summary") or {}
        risk_flags = version_diff.get("risk_flags") or []
        return {
            "id": "document-version-diff-checklist",
            "title": "Client-visible version diff",
            "status": version_diff.get("status", "template"),
            "ready": version_diff.get("status") == "ready",
            "blocks_release": version_diff.get("status") == "blocked",
            "blocking_issue_count": summary.get("blocking_issue_count", 0),
            "blocker_ids": [flag.get("id") for flag in risk_flags if flag.get("severity") == "blocking"],
            "reviewer_actions": [str(item) for item in version_diff.get("recommended_actions") or []],
        }

    def _export_component(self, export_readiness: dict[str, Any]) -> dict[str, Any]:
        summary = export_readiness.get("summary") or {}
        blockers = export_readiness.get("blocking_items") or []
        return {
            "id": "legal-document-export-readiness",
            "title": "Final export readiness",
            "status": export_readiness.get("status", "template"),
            "ready": export_readiness.get("status") == "ready",
            "blocks_release": export_readiness.get("status") == "blocked",
            "blocking_issue_count": summary.get("blocking_gate_count", 0),
            "blocker_ids": [item.get("id") for item in blockers],
            "reviewer_actions": [item.get("reviewer_action") for item in blockers if item.get("reviewer_action")],
        }

    def _quota_component(
        self,
        quota_decision: dict[str, Any],
        quota_summary: dict[str, Any],
        template_mode: bool,
    ) -> dict[str, Any]:
        status = quota_decision.get("status", "template")
        blocks = status == "blocked"
        return {
            "id": "quota-delivery-decision",
            "title": "Quota and account-plan delivery decision",
            "status": status,
            "ready": status == "ready",
            "blocks_release": blocks,
            "blocking_issue_count": len(quota_decision.get("reason_codes") or []) if blocks else 0,
            "blocker_ids": quota_decision.get("reason_codes") or [],
            "reviewer_actions": quota_decision.get("required_next_steps") or [],
            "quota_metadata_present": bool(quota_summary) and not template_mode,
        }

    def _status(self, component_gates: list[dict[str, Any]], template_mode: bool) -> str:
        if template_mode:
            return "template"
        if any(item["blocks_release"] for item in component_gates):
            return "blocked"
        if any(item["status"] == "review_required" for item in component_gates):
            return "review_required"
        if all(item["ready"] for item in component_gates):
            return "ready"
        return "blocked"

    def _release_decision(
        self,
        status: str,
        quota_decision: dict[str, Any],
        blocking_component_ids: list[str],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "delivery_action": quota_decision.get("action") or "deliver_to_client",
            "package_release_allowed": status == "ready",
            "final_export_allowed": status == "ready",
            "client_delivery_allowed": status == "ready",
            "materializes_export": False,
            "sends_client_delivery": False,
            "blocking_component_ids": blocking_component_ids,
            "decision": (
                "Final package release is allowed by sanitized metadata."
                if status == "ready"
                else "Final package release is blocked until component gates are resolved."
            ),
        }

    def _recommended_actions(self, component_gates: list[dict[str, Any]], status: str) -> list[dict[str, Any]]:
        if status == "ready":
            return [
                {
                    "id": "archive-final-delivery-release-gate",
                    "priority": "normal",
                    "owner": "legal_operations",
                    "action": "Archive package ID, version ID, format, manifest status, diff status, export status, quota status, and reviewer identity.",
                }
            ]
        actions: list[dict[str, Any]] = []
        for gate in component_gates:
            if gate["ready"]:
                continue
            actions.append(
                {
                    "id": f"resolve-{gate['id']}",
                    "priority": "high" if gate["blocks_release"] else "medium",
                    "owner": "legal_operations",
                    "action": (gate.get("reviewer_actions") or ["Resolve this component gate before final delivery."])[0],
                    "blocker_ids": gate.get("blocker_ids") or [],
                }
            )
        return actions

    def _audit_record_requirements(self) -> list[dict[str, str]]:
        return [
            {"field": "package_id", "reason": "Links release approval to one delivery package."},
            {"field": "case_id", "reason": "Keeps final delivery tied to one matter without exposing party details."},
            {"field": "current_version_id", "reason": "Locks export and client-visible diff to the reviewed version."},
            {"field": "export_format", "reason": "Shows which final file format was approved."},
            {"field": "component_gate_statuses", "reason": "Preserves manifest, diff, export, and quota gate outcomes."},
            {"field": "reviewer_id", "reason": "Records the responsible reviewer without storing notes or document text."},
        ]


def _first_dict(source: dict[str, Any], *keys: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    for key in keys:
        value = source.get(key)
        if isinstance(value, dict):
            return value
    return default or {}


def _text(value: Any) -> str:
    return str(value or "").strip()
