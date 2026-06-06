from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from models.cases import Cases
from schemas.auth import UserResponse
from services.case_role_permission_matrix import (
    DECISION_ALLOW,
    DECISION_REQUIRES_APPROVAL,
    OPERATIONS,
    ROLES,
    CaseRolePermissionMatrixService,
)


ROLE_ALIASES = {
    "owner": "owner",
    "creator": "owner",
    "lawyer": "lawyer",
    "attorney": "lawyer",
    "counsel": "lawyer",
    "\u5f8b\u5e08": "lawyer",
    "reviewer": "reviewer",
    "approver": "reviewer",
    "\u590d\u6838": "reviewer",
    "assistant": "assistant",
    "paralegal": "assistant",
    "member": "assistant",
    "\u52a9\u7406": "assistant",
    "client": "client",
    "\u5ba2\u6237": "client",
    "admin": "admin",
}

TOKEN_SPLIT_RE = re.compile(r"[,;\n]+")
ROLE_TOKEN_RE = re.compile(r"\b(owner|lawyer|attorney|counsel|reviewer|approver|assistant|paralegal|member|client|admin)\b", re.I)
PLACEHOLDER_NAMES = {"user", "unknown", "anonymous"}


@dataclass(frozen=True)
class CaseActor:
    user_id: str
    email: str
    name: str
    platform_role: str

    @classmethod
    def from_user(cls, user: UserResponse) -> "CaseActor":
        return cls(
            user_id=str(getattr(user, "id", "") or "").strip().lower(),
            email=str(getattr(user, "email", "") or "").strip().lower(),
            name=str(getattr(user, "name", "") or "").strip().lower(),
            platform_role=str(getattr(user, "role", "") or "").strip().lower(),
        )

    def matches(self, value: Any) -> bool:
        needle = str(value or "").strip().lower()
        if not needle:
            return False
        return needle in {self.user_id, self.email, self.name}

    def matches_legacy_text(self, text: str) -> bool:
        lowered = text.lower()
        if self.user_id and self.user_id in lowered:
            return True
        if self.email and self.email in lowered:
            return True
        return bool(self.name and self.name not in PLACEHOLDER_NAMES and self.name in lowered)


class CaseAccessControlService:
    """Runtime case permission checks backed by existing case metadata.

    This intentionally returns metadata-only decisions: role, operation, policy
    status, gate, and reason codes. It never echoes team member strings, emails,
    client names, case narratives, or document text.
    """

    policy_id = "case-access-control-runtime-v1"

    def __init__(self, matrix: CaseRolePermissionMatrixService | None = None):
        self.matrix = matrix or CaseRolePermissionMatrixService()

    def build_permissions_summary(
        self,
        case: Cases,
        user: UserResponse,
        *,
        approval_granted: bool = False,
    ) -> dict[str, Any]:
        decisions = {
            operation: self.evaluate(case, user, operation, approval_granted=approval_granted)
            for operation in OPERATIONS
        }
        allowed_operations = tuple(operation for operation, decision in decisions.items() if decision["allowed"])
        approval_required_operations = tuple(
            operation for operation, decision in decisions.items() if decision["requires_approval"]
        )
        denied_operations = tuple(
            operation
            for operation, decision in decisions.items()
            if not decision["allowed"] and not decision["requires_approval"]
        )
        return {
            "policy_id": self.policy_id,
            "case_id": getattr(case, "id", None),
            "actor_role": decisions["read"]["actor_role"],
            "role_source": decisions["read"]["role_source"],
            "allowed_operations": allowed_operations,
            "approval_required_operations": approval_required_operations,
            "denied_operations": denied_operations,
            "decisions": decisions,
            "privacy_safe": True,
            "does_not_include": (
                "team_member_raw_text",
                "actor_email",
                "client_name",
                "case_narrative",
                "document_text",
                "credentials",
            ),
        }

    def evaluate(
        self,
        case: Cases | None,
        user: UserResponse,
        operation: str,
        *,
        approval_granted: bool = False,
    ) -> dict[str, Any]:
        actor = CaseActor.from_user(user)
        normalized_operation = self._normalize_operation(operation)
        actor_role, role_source = self.resolve_role(case, actor)

        if not case:
            return self._denied_payload(
                actor_role=actor_role,
                role_source=role_source,
                operation=normalized_operation,
                reason="case_not_found",
            )

        decision = self.matrix.evaluate_permission(actor_role, normalized_operation)
        allowed = decision.get("decision") == DECISION_ALLOW
        requires_approval = decision.get("decision") == DECISION_REQUIRES_APPROVAL
        if requires_approval and approval_granted:
            allowed = True

        reason = None
        if not allowed:
            reason = "approval_required" if requires_approval else decision.get("reason") or "permission_denied"

        return {
            "policy_id": self.policy_id,
            "case_id": getattr(case, "id", None),
            "actor_role": actor_role,
            "role_source": role_source,
            "operation": normalized_operation,
            "decision": decision.get("decision"),
            "status": "allowed" if allowed else ("requires_approval" if requires_approval else "denied"),
            "allowed": allowed,
            "requires_approval": requires_approval and not approval_granted,
            "approval_gate": decision.get("approval_gate"),
            "audit_required": bool(decision.get("audit_required", True)),
            "reason": reason,
            "privacy_safe": True,
        }

    def can_access(self, case: Cases | None, user: UserResponse, operation: str) -> bool:
        return self.evaluate(case, user, operation)["allowed"]

    def resolve_role(self, case: Cases | None, actor: CaseActor) -> tuple[str, str]:
        if not case:
            return ("unknown", "case_missing")
        if actor.user_id and actor.user_id == str(getattr(case, "user_id", "") or "").strip().lower():
            return ("owner", "case_owner")
        member_role = self._role_from_team_members(getattr(case, "team_members", None), actor)
        if member_role:
            return (member_role, "case_team_members")
        if actor.platform_role == "admin":
            return ("admin", "platform_role")
        return ("unknown", "no_case_assignment")

    def _role_from_team_members(self, raw: Any, actor: CaseActor) -> str | None:
        for item in self._team_member_items(raw):
            role = self._role_from_member_item(item, actor)
            if role:
                return role
        return None

    def _team_member_items(self, raw: Any) -> list[Any]:
        if raw is None:
            return []
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            return [raw]
        text = str(raw).strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
        return [part.strip() for part in TOKEN_SPLIT_RE.split(text) if part.strip()]

    def _role_from_member_item(self, item: Any, actor: CaseActor) -> str | None:
        if isinstance(item, dict):
            member_values = (
                item.get("user_id"),
                item.get("member_user_id"),
                item.get("email"),
                item.get("member_email"),
                item.get("name"),
                item.get("member_name"),
            )
            if not any(actor.matches(value) for value in member_values):
                return None
            return self._normalize_role(item.get("role") or item.get("case_role") or item.get("member_role")) or "lawyer"

        text = str(item or "").strip()
        if not text:
            return None
        lowered = text.lower()
        if not actor.matches_legacy_text(lowered):
            return None
        return self._normalize_role(text) or "lawyer"

    def _normalize_role(self, value: Any) -> str | None:
        lowered = str(value or "").strip().lower()
        if lowered in ROLE_ALIASES:
            role = ROLE_ALIASES[lowered]
            return role if role in ROLES else None
        match = ROLE_TOKEN_RE.search(lowered)
        if match:
            role = ROLE_ALIASES.get(match.group(1).lower())
            return role if role in ROLES else None
        for alias, role in ROLE_ALIASES.items():
            if alias in lowered and role in ROLES:
                return role
        return None

    @staticmethod
    def _normalize_operation(operation: str) -> str:
        normalized = str(operation or "").strip().lower()
        return normalized or "unknown"

    def _denied_payload(self, *, actor_role: str, role_source: str, operation: str, reason: str) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "case_id": None,
            "actor_role": actor_role,
            "role_source": role_source,
            "operation": operation,
            "decision": "deny",
            "status": "denied",
            "allowed": False,
            "requires_approval": False,
            "approval_gate": None,
            "audit_required": True,
            "reason": reason,
            "privacy_safe": True,
        }
