from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


RETENTION_RULES = (
    {
        "artifact_type": "uploaded_legal_document",
        "retention_days": 90,
        "delete_trigger": "case_closed_or_user_deletion_request",
        "requires_reviewer_confirmation": True,
    },
    {
        "artifact_type": "deep_review_report",
        "retention_days": 180,
        "delete_trigger": "case_closed_or_user_deletion_request",
        "requires_reviewer_confirmation": True,
    },
    {
        "artifact_type": "quota_usage_event",
        "retention_days": 400,
        "delete_trigger": "quota_window_closed",
        "requires_reviewer_confirmation": False,
    },
    {
        "artifact_type": "model_route_trace",
        "retention_days": 45,
        "delete_trigger": "debug_window_closed",
        "requires_reviewer_confirmation": False,
    },
    {
        "artifact_type": "feedback_ticket",
        "retention_days": 365,
        "delete_trigger": "issue_closed_and_no_active_release_link",
        "requires_reviewer_confirmation": False,
    },
)

PRIVACY_BOUNDARY = {
    "raw_document_text_included": False,
    "pii_included": False,
    "provider_payload_included": False,
    "output_scope": "artifact type, retention class, delete trigger, and counts only",
}


class PrivacyRetentionRulesService:
    """Describe and evaluate privacy-safe retention rules for legal workflow artifacts."""

    def build_policy(self, artifacts: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
        evaluations = [self._evaluate_artifact(item) for item in artifacts or [] if isinstance(item, Mapping)]
        return {
            "status": "ready",
            "policy_version": "privacy-retention-rules-v1",
            "default_rules": [dict(rule) for rule in RETENTION_RULES],
            "evaluations": evaluations,
            "summary": {
                "rule_count": len(RETENTION_RULES),
                "evaluated_artifact_count": len(evaluations),
                "manual_confirmation_count": sum(1 for item in evaluations if item["requires_reviewer_confirmation"]),
                "unknown_artifact_count": sum(1 for item in evaluations if item["retention_class"] == "unknown"),
            },
            "recommended_actions": self._recommended_actions(evaluations),
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _evaluate_artifact(self, artifact: Mapping[str, Any]) -> dict[str, Any]:
        artifact_type = str(artifact.get("artifact_type") or artifact.get("type") or "unknown").strip().lower()
        rule = next((item for item in RETENTION_RULES if item["artifact_type"] == artifact_type), None)
        artifact_id = str(artifact.get("artifact_id") or artifact.get("id") or "").strip()
        safe_id = artifact_id if self._safe_id(artifact_id) else "artifact_id_redacted"
        if not rule:
            return {
                "artifact_id": safe_id or "unknown",
                "retention_class": "unknown",
                "retention_days": None,
                "delete_trigger": "manual_policy_review_required",
                "requires_reviewer_confirmation": True,
                "reason_codes": ["unknown_artifact_type"],
            }
        return {
            "artifact_id": safe_id or "unknown",
            "retention_class": rule["artifact_type"],
            "retention_days": rule["retention_days"],
            "delete_trigger": rule["delete_trigger"],
            "requires_reviewer_confirmation": rule["requires_reviewer_confirmation"],
            "reason_codes": [],
        }

    def _recommended_actions(self, evaluations: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Apply retention rules before public release claims or customer-facing deletion promises.",
            "Keep raw legal documents, provider payloads, and PII out of retention evidence.",
        ]
        if any(item["retention_class"] == "unknown" for item in evaluations):
            actions.append("Route unknown artifact types to manual policy review before retention automation.")
        if any(item["requires_reviewer_confirmation"] for item in evaluations):
            actions.append("Require reviewer confirmation before deleting user-facing legal work product.")
        return actions

    def _safe_id(self, value: str) -> bool:
        if not value or len(value) > 80:
            return False
        lowered = value.lower()
        if "@" in lowered or "sk-" in lowered:
            return False
        return all(char.isalnum() or char in "-_:.#" for char in value)
