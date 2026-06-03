from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AuditEventPolicy:
    event_type: str
    category: str
    required_fields: tuple[str, ...]
    forbidden_fields: tuple[str, ...]
    retention_bucket: str
    reviewer_value: str
    blocking_if_missing: tuple[str, ...]

    def to_api(self, sample: dict[str, Any] | None = None) -> dict[str, Any]:
        sample = sample or {}
        missing_fields = [field for field in self.required_fields if not sample.get(field)]
        forbidden_present = [field for field in self.forbidden_fields if field in sample]
        data = asdict(self)
        data["required_fields"] = list(self.required_fields)
        data["forbidden_fields"] = list(self.forbidden_fields)
        data["missing_fields"] = missing_fields
        data["forbidden_fields_present"] = forbidden_present
        data["status"] = "pass" if not missing_fields and not forbidden_present else "fail"
        data["blocks_release"] = bool(forbidden_present) or any(field in missing_fields for field in self.blocking_if_missing)
        return data


class MatterAuditRetentionPolicyService:
    """Define privacy-minimized audit logging rules for legal matter workflows."""

    def build_policy(self, sample_events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        policies = self._event_policies()
        samples_by_type = {
            str(event.get("event_type") or ""): event
            for event in sample_events or []
            if isinstance(event, dict)
        }
        event_checks = [policy.to_api(samples_by_type.get(policy.event_type)) for policy in policies]
        blockers = [item for item in event_checks if item["blocks_release"]]

        return {
            "status": "template" if sample_events is None else ("blocked" if blockers else "ready"),
            "policy_id": "matter-audit-retention-policy-v1",
            "summary": {
                "event_type_count": len(policies),
                "checked_event_count": len(sample_events or []),
                "blocking_issue_count": len(blockers),
                "retention_bucket_count": len({policy.retention_bucket for policy in policies}),
                "privacy_minimized": True,
            },
            "event_policies": event_checks,
            "blocking_items": [
                {
                    "event_type": item["event_type"],
                    "missing_fields": item["missing_fields"],
                    "forbidden_fields_present": item["forbidden_fields_present"],
                    "reviewer_value": item["reviewer_value"],
                }
                for item in blockers
            ],
            "retention_buckets": [
                {
                    "id": "case_lifecycle",
                    "description": "Case open, archive, access, assignment, and status-change events.",
                    "default_retention": "retain_with_case_file",
                },
                {
                    "id": "client_delivery",
                    "description": "Export, share, disclosure acknowledgement, and lawyer approval decisions.",
                    "default_retention": "retain_with_reviewed_version",
                },
                {
                    "id": "security_privacy",
                    "description": "Denied access, sensitive operation attempts, redaction status, and deletion requests.",
                    "default_retention": "retain_for_incident_review",
                },
            ],
            "data_minimization_rules": [
                "Store actor IDs, matter IDs, event IDs, decisions, timestamps, and source references.",
                "Do not store full legal text, raw client narratives, direct contact details, API keys, login credentials, or full attachments.",
                "Use document IDs, version IDs, citation IDs, and redaction status instead of duplicating file contents.",
                "Denied sensitive-operation attempts must be retained because they support supervision and incident review.",
            ],
            "validation_commands": [
                "python -m pytest tests/test_matter_audit_retention_policy.py -q",
                "python -m pytest tests/test_case_team_access_policy.py tests/test_client_delivery_risk_checklist.py -q",
            ],
            "privacy_note": (
                "The audit policy is metadata-only. It defines event schemas, retention buckets, and forbidden "
                "fields without storing user documents, raw legal output, secrets, or contact details."
            ),
        }

    def _event_policies(self) -> tuple[AuditEventPolicy, ...]:
        return (
            AuditEventPolicy(
                event_type="case_access_changed",
                category="collaboration",
                required_fields=("event_id", "matter_id", "actor_id", "target_member_id", "role", "decision", "timestamp"),
                forbidden_fields=("raw_client_name", "email", "phone", "full_document_text"),
                retention_bucket="case_lifecycle",
                reviewer_value="Explains who changed case access and why.",
                blocking_if_missing=("matter_id", "actor_id", "target_member_id", "role", "decision"),
            ),
            AuditEventPolicy(
                event_type="ai_review_started",
                category="model_ops",
                required_fields=("event_id", "matter_id", "actor_id", "route_id", "purpose", "timestamp"),
                forbidden_fields=("api_key", "raw_prompt", "raw_model_output", "full_document_text"),
                retention_bucket="security_privacy",
                reviewer_value="Shows why a model-assisted legal workflow was initiated without storing raw prompts.",
                blocking_if_missing=("matter_id", "actor_id", "route_id", "purpose"),
            ),
            AuditEventPolicy(
                event_type="lawyer_review_decision",
                category="legal_quality",
                required_fields=("event_id", "matter_id", "reviewer_id", "decision", "version_id", "timestamp"),
                forbidden_fields=("full_review_text", "raw_client_name", "email", "phone"),
                retention_bucket="client_delivery",
                reviewer_value="Links a client-facing version to the responsible lawyer decision.",
                blocking_if_missing=("matter_id", "reviewer_id", "decision", "version_id"),
            ),
            AuditEventPolicy(
                event_type="client_delivery_exported",
                category="delivery",
                required_fields=("event_id", "matter_id", "actor_id", "version_id", "export_format", "redaction_status", "timestamp"),
                forbidden_fields=("full_attachment_bytes", "full_document_text", "email", "phone"),
                retention_bucket="client_delivery",
                reviewer_value="Records what reviewed version was exported and whether redaction passed.",
                blocking_if_missing=("matter_id", "version_id", "export_format", "redaction_status"),
            ),
            AuditEventPolicy(
                event_type="sensitive_operation_denied",
                category="security",
                required_fields=("event_id", "matter_id", "actor_id", "operation", "reason", "timestamp"),
                forbidden_fields=("api_key", "login_secret", "full_document_text", "raw_client_name"),
                retention_bucket="security_privacy",
                reviewer_value="Supports supervision when an unsafe share, export, delete, or role change was blocked.",
                blocking_if_missing=("matter_id", "actor_id", "operation", "reason"),
            ),
        )
