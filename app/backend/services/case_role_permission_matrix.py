from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DECISION_ALLOW = "allow"
DECISION_DENY = "deny"
DECISION_REQUIRES_APPROVAL = "requires_approval"

DECISIONS = (DECISION_ALLOW, DECISION_DENY, DECISION_REQUIRES_APPROVAL)
ROLES = ("owner", "lawyer", "reviewer", "assistant", "client", "admin")
OPERATIONS = ("read", "write", "export", "share", "billing", "audit", "review")


@dataclass(frozen=True)
class PermissionRule:
    role: str
    operation: str
    decision: str
    scope: str
    audit_required: bool
    approval_gate: str | None
    rationale: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RoleSummary:
    role: str
    purpose: str
    default_scope: str
    allowed_operations: tuple[str, ...]
    approval_required_operations: tuple[str, ...]
    denied_operations: tuple[str, ...]
    privacy_boundary: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class CaseRolePermissionMatrixService:
    """Build a deterministic, metadata-only permission matrix for matter/case roles."""

    def build_matrix(self) -> dict[str, Any]:
        permissions = self._permission_rules()
        role_summaries = self._role_summaries(permissions)
        forbidden_combinations = self._forbidden_combinations(permissions)
        approval_gates = [
            {
                "role": rule.role,
                "operation": rule.operation,
                "approval_gate": rule.approval_gate,
                "scope": rule.scope,
                "rationale": rule.rationale,
            }
            for rule in permissions
            if rule.decision == DECISION_REQUIRES_APPROVAL
        ]

        decision_counts = {
            decision: len([rule for rule in permissions if rule.decision == decision])
            for decision in DECISIONS
        }

        return {
            "status": "ready",
            "policy_id": "case-role-permission-matrix-v1",
            "scope": {
                "type": "pure-local-matter-case-role-permission-matrix",
                "data_classification": "metadata_only",
                "does_not_include": (
                    "case_narratives",
                    "document_text",
                    "direct_contact_details",
                    "payment_card_data",
                    "secret_tokens",
                ),
            },
            "decision_values": DECISIONS,
            "roles": ROLES,
            "operations": OPERATIONS,
            "summary": {
                "role_count": len(ROLES),
                "operation_count": len(OPERATIONS),
                "permission_count": len(permissions),
                "allow_count": decision_counts[DECISION_ALLOW],
                "deny_count": decision_counts[DECISION_DENY],
                "requires_approval_count": decision_counts[DECISION_REQUIRES_APPROVAL],
                "forbidden_combination_count": len(forbidden_combinations),
                "default_posture": "deny_by_default",
                "privacy_safe": True,
            },
            "matrix": self._decision_matrix(permissions),
            "permissions": [rule.to_api() for rule in permissions],
            "role_summaries": [summary.to_api() for summary in role_summaries],
            "approval_gates": approval_gates,
            "forbidden_combinations": forbidden_combinations,
            "privacy_safe_api_payload": self._privacy_safe_payload_contract(),
            "validation_commands": [
                "python -m pytest tests/test_case_role_permission_matrix.py -q",
                "python -m compileall services/case_role_permission_matrix.py tests/test_case_role_permission_matrix.py",
            ],
        }

    def build_privacy_safe_api_payload(self) -> dict[str, Any]:
        return self.build_matrix()

    def evaluate_permission(self, role: str, operation: str) -> dict[str, Any]:
        normalized_role = (role or "").strip().lower()
        normalized_operation = (operation or "").strip().lower()

        if normalized_role not in ROLES or normalized_operation not in OPERATIONS:
            return {
                "status": "denied",
                "role": normalized_role or "unknown",
                "operation": normalized_operation or "unknown",
                "decision": DECISION_DENY,
                "reason": "unknown_role_or_operation",
                "audit_required": True,
                "privacy_safe": True,
            }

        rule = next(
            item
            for item in self._permission_rules()
            if item.role == normalized_role and item.operation == normalized_operation
        )
        status_by_decision = {
            DECISION_ALLOW: "allowed",
            DECISION_REQUIRES_APPROVAL: "requires_approval",
            DECISION_DENY: "denied",
        }
        payload = rule.to_api()
        payload["status"] = status_by_decision[rule.decision]
        payload["privacy_safe"] = True
        return payload

    def _permission_rules(self) -> tuple[PermissionRule, ...]:
        matrix = self._matrix_definitions()
        rules: list[PermissionRule] = []
        for role in ROLES:
            for operation in OPERATIONS:
                item = matrix[role][operation]
                rules.append(
                    PermissionRule(
                        role=role,
                        operation=operation,
                        decision=item["decision"],
                        scope=item["scope"],
                        audit_required=item["audit_required"],
                        approval_gate=item.get("approval_gate"),
                        rationale=item["rationale"],
                    )
                )
        return tuple(rules)

    def _role_summaries(self, permissions: tuple[PermissionRule, ...]) -> tuple[RoleSummary, ...]:
        profile = self._role_profiles()
        summaries: list[RoleSummary] = []
        for role in ROLES:
            role_rules = [rule for rule in permissions if rule.role == role]
            summaries.append(
                RoleSummary(
                    role=role,
                    purpose=profile[role]["purpose"],
                    default_scope=profile[role]["default_scope"],
                    allowed_operations=tuple(
                        rule.operation for rule in role_rules if rule.decision == DECISION_ALLOW
                    ),
                    approval_required_operations=tuple(
                        rule.operation for rule in role_rules if rule.decision == DECISION_REQUIRES_APPROVAL
                    ),
                    denied_operations=tuple(
                        rule.operation for rule in role_rules if rule.decision == DECISION_DENY
                    ),
                    privacy_boundary=profile[role]["privacy_boundary"],
                )
            )
        return tuple(summaries)

    @staticmethod
    def _decision_matrix(permissions: tuple[PermissionRule, ...]) -> dict[str, dict[str, str]]:
        matrix: dict[str, dict[str, str]] = {role: {} for role in ROLES}
        for rule in permissions:
            matrix[rule.role][rule.operation] = rule.decision
        return matrix

    @staticmethod
    def _forbidden_combinations(permissions: tuple[PermissionRule, ...]) -> list[dict[str, Any]]:
        return [
            {
                "role": rule.role,
                "operation": rule.operation,
                "decision": rule.decision,
                "scope": rule.scope,
                "reason": rule.rationale,
                "safe_alternative": CaseRolePermissionMatrixService._safe_alternative(rule),
            }
            for rule in permissions
            if rule.decision == DECISION_DENY
        ]

    @staticmethod
    def _safe_alternative(rule: PermissionRule) -> str:
        alternatives = {
            "export": "request_owner_or_lawyer_approved_export",
            "share": "request_owner_or_lawyer_approved_share",
            "billing": "route_to_owner_or_billing_admin",
            "audit": "request_privacy_safe_audit_summary",
            "review": "request_assigned_lawyer_or_reviewer_decision",
            "write": "submit_draft_or_fact_update_for_approval",
            "read": "request_explicit_case_assignment_or_shared_item",
        }
        return alternatives.get(rule.operation, "request_case_owner_review")

    @staticmethod
    def _privacy_safe_payload_contract() -> dict[str, Any]:
        return {
            "description": "API payloads expose role, operation, decision, scope, approval gate, and rationale only.",
            "allowed_fields": (
                "policy_id",
                "role",
                "operation",
                "decision",
                "scope",
                "audit_required",
                "approval_gate",
                "rationale",
                "summary",
            ),
            "forbidden_fields": (
                "case_narrative",
                "document_text",
                "raw_client_name",
                "direct_contact_details",
                "payment_card_data",
                "secret_tokens",
            ),
            "response_rules": (
                "Use stable role and operation names instead of user names or case facts.",
                "Return denial reasons as policy categories, not private matter details.",
                "Record audit intent as metadata and keep raw legal work product out of the payload.",
            ),
            "sample_evaluate_response": {
                "role": "assistant",
                "operation": "write",
                "decision": DECISION_REQUIRES_APPROVAL,
                "status": "requires_approval",
                "privacy_safe": True,
            },
        }

    @staticmethod
    def _role_profiles() -> dict[str, dict[str, str]]:
        return {
            "owner": {
                "purpose": "Controls the matter workspace, team scope, billing boundary, and final release decisions.",
                "default_scope": "full_case_workspace",
                "privacy_boundary": "May see full case metadata and work product, with sensitive exports and shares still gated.",
            },
            "lawyer": {
                "purpose": "Performs legal work, prepares deliverables, and requests controlled disclosure.",
                "default_scope": "assigned_case_workspace",
                "privacy_boundary": "May access assigned matter content but cannot change billing ownership.",
            },
            "reviewer": {
                "purpose": "Reviews legal conclusions, risk flags, citations, and delivery readiness.",
                "default_scope": "review_packet_and_related_audit_metadata",
                "privacy_boundary": "Limited to review materials and review-relevant audit metadata.",
            },
            "assistant": {
                "purpose": "Supports intake, drafting, tagging, and task cleanup under lawyer supervision.",
                "default_scope": "assigned_tasks_and_materials",
                "privacy_boundary": "Cannot export, share, bill, audit, or approve legal review outcomes.",
            },
            "client": {
                "purpose": "Views shared deliverables and submits requested facts through controlled channels.",
                "default_scope": "client_shared_items_only",
                "privacy_boundary": "Never sees internal notes, draft work product, audit logs, or team-only review traces.",
            },
            "admin": {
                "purpose": "Handles operational support, billing support, and audit oversight without becoming case counsel.",
                "default_scope": "platform_metadata_and_break_glass_case_access",
                "privacy_boundary": "Case content access requires approval and must be audited as a support event.",
            },
        }

    @staticmethod
    def _matrix_definitions() -> dict[str, dict[str, dict[str, Any]]]:
        return {
            "owner": {
                "read": {
                    "decision": DECISION_ALLOW,
                    "scope": "full_case_workspace",
                    "audit_required": True,
                    "rationale": "The owner is accountable for the matter and must inspect case materials.",
                },
                "write": {
                    "decision": DECISION_ALLOW,
                    "scope": "full_case_workspace",
                    "audit_required": True,
                    "rationale": "The owner can update matter strategy, tasks, and workspace records.",
                },
                "export": {
                    "decision": DECISION_REQUIRES_APPROVAL,
                    "scope": "approved_case_export_package",
                    "audit_required": True,
                    "approval_gate": "owner_export_confirmation",
                    "rationale": "Full exports may contain privileged material and need explicit confirmation.",
                },
                "share": {
                    "decision": DECISION_REQUIRES_APPROVAL,
                    "scope": "approved_external_or_client_share",
                    "audit_required": True,
                    "approval_gate": "owner_share_confirmation",
                    "rationale": "Sharing changes privilege boundaries and must be deliberate.",
                },
                "billing": {
                    "decision": DECISION_ALLOW,
                    "scope": "matter_billing_controls",
                    "audit_required": True,
                    "rationale": "The owner controls the matter billing boundary and entitlement decisions.",
                },
                "audit": {
                    "decision": DECISION_ALLOW,
                    "scope": "case_audit_metadata",
                    "audit_required": True,
                    "rationale": "The owner needs audit metadata for supervision and incident review.",
                },
                "review": {
                    "decision": DECISION_ALLOW,
                    "scope": "legal_review_and_release_decisions",
                    "audit_required": True,
                    "rationale": "The owner can approve legal review checkpoints and delivery readiness.",
                },
            },
            "lawyer": {
                "read": {
                    "decision": DECISION_ALLOW,
                    "scope": "assigned_case_workspace",
                    "audit_required": True,
                    "rationale": "Assigned lawyers need matter materials to perform legal work.",
                },
                "write": {
                    "decision": DECISION_ALLOW,
                    "scope": "assigned_case_workspace",
                    "audit_required": True,
                    "rationale": "Assigned lawyers can update legal work product and case records.",
                },
                "export": {
                    "decision": DECISION_REQUIRES_APPROVAL,
                    "scope": "reviewed_deliverables_or_owner_approved_export",
                    "audit_required": True,
                    "approval_gate": "owner_or_lawyer_export_approval",
                    "rationale": "Exports require a checked version and an auditable release decision.",
                },
                "share": {
                    "decision": DECISION_REQUIRES_APPROVAL,
                    "scope": "approved_client_or_external_share",
                    "audit_required": True,
                    "approval_gate": "owner_or_lawyer_share_approval",
                    "rationale": "Lawyers can request sharing, but disclosure still needs explicit approval.",
                },
                "billing": {
                    "decision": DECISION_DENY,
                    "scope": "matter_billing_controls",
                    "audit_required": True,
                    "rationale": "Legal work assignment does not grant billing ownership or entitlement changes.",
                },
                "audit": {
                    "decision": DECISION_ALLOW,
                    "scope": "assigned_case_audit_metadata",
                    "audit_required": True,
                    "rationale": "Assigned lawyers need audit metadata for supervised legal delivery.",
                },
                "review": {
                    "decision": DECISION_ALLOW,
                    "scope": "assigned_legal_review_checkpoints",
                    "audit_required": True,
                    "rationale": "Assigned lawyers can approve legal review checkpoints within their case scope.",
                },
            },
            "reviewer": {
                "read": {
                    "decision": DECISION_ALLOW,
                    "scope": "review_packet",
                    "audit_required": True,
                    "rationale": "Reviewers need the packet needed to assess conclusions and citations.",
                },
                "write": {
                    "decision": DECISION_DENY,
                    "scope": "case_work_product",
                    "audit_required": True,
                    "rationale": "Reviewers should comment or decide review status instead of changing source records.",
                },
                "export": {
                    "decision": DECISION_DENY,
                    "scope": "case_export_package",
                    "audit_required": True,
                    "rationale": "Review assignment does not authorize downloads of case packages.",
                },
                "share": {
                    "decision": DECISION_DENY,
                    "scope": "external_or_client_share",
                    "audit_required": True,
                    "rationale": "Reviewers do not control disclosure boundaries.",
                },
                "billing": {
                    "decision": DECISION_DENY,
                    "scope": "matter_billing_controls",
                    "audit_required": True,
                    "rationale": "Reviewers have no billing administration purpose.",
                },
                "audit": {
                    "decision": DECISION_ALLOW,
                    "scope": "review_relevant_audit_metadata",
                    "audit_required": True,
                    "rationale": "Reviewers may need audit metadata tied to the reviewed version.",
                },
                "review": {
                    "decision": DECISION_ALLOW,
                    "scope": "assigned_review_checkpoints",
                    "audit_required": True,
                    "rationale": "Reviewers are assigned to approve, reject, or request changes.",
                },
            },
            "assistant": {
                "read": {
                    "decision": DECISION_ALLOW,
                    "scope": "assigned_tasks_and_materials",
                    "audit_required": True,
                    "rationale": "Assistants need assigned materials to support case preparation.",
                },
                "write": {
                    "decision": DECISION_REQUIRES_APPROVAL,
                    "scope": "draft_updates_and_task_notes",
                    "audit_required": True,
                    "approval_gate": "lawyer_or_owner_write_approval",
                    "rationale": "Assistant edits should remain drafts until a supervising lawyer approves them.",
                },
                "export": {
                    "decision": DECISION_DENY,
                    "scope": "case_export_package",
                    "audit_required": True,
                    "rationale": "Assistant support does not justify case package downloads.",
                },
                "share": {
                    "decision": DECISION_DENY,
                    "scope": "external_or_client_share",
                    "audit_required": True,
                    "rationale": "Assistants cannot create disclosure channels.",
                },
                "billing": {
                    "decision": DECISION_DENY,
                    "scope": "matter_billing_controls",
                    "audit_required": True,
                    "rationale": "Assistants cannot change billing or entitlement state.",
                },
                "audit": {
                    "decision": DECISION_DENY,
                    "scope": "case_audit_metadata",
                    "audit_required": True,
                    "rationale": "Audit metadata is limited to owners, lawyers, reviewers, and admins.",
                },
                "review": {
                    "decision": DECISION_DENY,
                    "scope": "legal_review_checkpoints",
                    "audit_required": True,
                    "rationale": "Assistants cannot approve legal review outcomes.",
                },
            },
            "client": {
                "read": {
                    "decision": DECISION_ALLOW,
                    "scope": "client_shared_items_only",
                    "audit_required": True,
                    "rationale": "Clients can view deliverables and requests explicitly shared with them.",
                },
                "write": {
                    "decision": DECISION_REQUIRES_APPROVAL,
                    "scope": "client_fact_submissions",
                    "audit_required": True,
                    "approval_gate": "lawyer_fact_intake_approval",
                    "rationale": "Client-provided facts should be reviewed before becoming case records.",
                },
                "export": {
                    "decision": DECISION_DENY,
                    "scope": "case_export_package",
                    "audit_required": True,
                    "rationale": "Client role does not grant full workspace or internal work-product export.",
                },
                "share": {
                    "decision": DECISION_DENY,
                    "scope": "external_or_client_share",
                    "audit_required": True,
                    "rationale": "Clients cannot expand access to the matter workspace.",
                },
                "billing": {
                    "decision": DECISION_DENY,
                    "scope": "matter_billing_controls",
                    "audit_required": True,
                    "rationale": "Client portal access does not permit billing control changes.",
                },
                "audit": {
                    "decision": DECISION_DENY,
                    "scope": "case_audit_metadata",
                    "audit_required": True,
                    "rationale": "Audit logs may expose internal supervision and privileged workflow metadata.",
                },
                "review": {
                    "decision": DECISION_DENY,
                    "scope": "legal_review_checkpoints",
                    "audit_required": True,
                    "rationale": "Clients cannot approve legal review or release readiness.",
                },
            },
            "admin": {
                "read": {
                    "decision": DECISION_REQUIRES_APPROVAL,
                    "scope": "break_glass_case_content_access",
                    "audit_required": True,
                    "approval_gate": "owner_or_security_break_glass_approval",
                    "rationale": "Admins should not read case content unless support access is approved and audited.",
                },
                "write": {
                    "decision": DECISION_DENY,
                    "scope": "case_work_product",
                    "audit_required": True,
                    "rationale": "Admin support does not authorize changing legal work product.",
                },
                "export": {
                    "decision": DECISION_DENY,
                    "scope": "case_export_package",
                    "audit_required": True,
                    "rationale": "Administrative support must not become a path to case exports.",
                },
                "share": {
                    "decision": DECISION_DENY,
                    "scope": "external_or_client_share",
                    "audit_required": True,
                    "rationale": "Admins cannot create matter disclosure channels.",
                },
                "billing": {
                    "decision": DECISION_ALLOW,
                    "scope": "billing_support_metadata",
                    "audit_required": True,
                    "rationale": "Admins may support billing metadata without viewing case narratives.",
                },
                "audit": {
                    "decision": DECISION_ALLOW,
                    "scope": "privacy_safe_audit_metadata",
                    "audit_required": True,
                    "rationale": "Admins need audit metadata for security, privacy, and operational support.",
                },
                "review": {
                    "decision": DECISION_DENY,
                    "scope": "legal_review_checkpoints",
                    "audit_required": True,
                    "rationale": "Admins are not legal reviewers or case counsel.",
                },
            },
        }
