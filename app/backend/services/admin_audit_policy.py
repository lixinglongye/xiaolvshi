from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


PRIVACY_BOUNDARY = {
    "raw_payload_included": False,
    "pii_included": False,
    "output_scope": "audit action type, risk level, required approval, and reason codes only",
}


SENSITIVE_ACTIONS = {
    "delete_case",
    "export_report",
    "change_plan",
    "invite_member",
    "remove_member",
    "override_quota",
    "delete_user_data",
}


class AdminAuditPolicyService:
    """Evaluate sensitive admin actions for approval and audit requirements."""

    def evaluate(self, actions: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
        checks = [self._check(action) for action in actions or [] if isinstance(action, Mapping)]
        return {
            "status": "review_required" if any(item["approval_required"] for item in checks) else "ready",
            "policy_version": "admin-audit-policy-v1",
            "checks": checks,
            "summary": {
                "action_count": len(checks),
                "approval_required_count": sum(1 for item in checks if item["approval_required"]),
                "high_risk_count": sum(1 for item in checks if item["risk_level"] == "high"),
            },
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _check(self, action: Mapping[str, Any]) -> dict[str, Any]:
        action_type = str(action.get("action_type") or action.get("type") or "unknown").strip().lower()
        approval_required = action_type in SENSITIVE_ACTIONS
        actor_role = str(action.get("actor_role") or "unknown").strip().lower()
        reason_codes = []
        if approval_required:
            reason_codes.append("sensitive_action_requires_approval")
        if actor_role not in {"admin", "owner", "maintainer"}:
            reason_codes.append("actor_role_requires_review")
        risk_level = "high" if approval_required or actor_role not in {"admin", "owner", "maintainer"} else "low"
        return {
            "action_type": action_type if action_type in SENSITIVE_ACTIONS else "general_admin_action",
            "risk_level": risk_level,
            "approval_required": approval_required,
            "audit_required": True,
            "reason_codes": reason_codes,
        }
