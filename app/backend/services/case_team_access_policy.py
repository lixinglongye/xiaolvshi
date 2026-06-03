from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CaseTeamRolePolicy:
    role: str
    purpose: str
    default_scope: str
    allowed_actions: tuple[str, ...]
    denied_actions: tuple[str, ...]
    approval_required_for: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SensitiveOperationPolicy:
    operation: str
    allowed_roles: tuple[str, ...]
    audit_required: bool
    approval_required: bool
    rationale: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class CaseTeamAccessPolicyService:
    """Describe least-privilege collaboration rules for a case workspace."""

    def build_policy(self) -> dict[str, Any]:
        role_matrix = [
            CaseTeamRolePolicy(
                role="owner",
                purpose="Owns the case workspace, billing boundary, retention settings, and final access decisions.",
                default_scope="full_case_workspace",
                allowed_actions=(
                    "manage_team",
                    "assign_roles",
                    "view_all_case_materials",
                    "approve_external_share",
                    "close_or_archive_case",
                ),
                denied_actions=("bypass_audit", "delete_audit_events"),
                approval_required_for=("export_case_file", "external_share", "bulk_delete_materials"),
            ),
            CaseTeamRolePolicy(
                role="lawyer",
                purpose="Leads legal analysis and client-facing work under the owner or firm mandate.",
                default_scope="assigned_case_workspace",
                allowed_actions=(
                    "view_case_materials",
                    "upload_materials",
                    "edit_case_notes",
                    "run_ai_review",
                    "prepare_client_deliverables",
                ),
                denied_actions=("delete_audit_events", "change_billing_owner"),
                approval_required_for=("external_share", "finalize_client_deliverable"),
            ),
            CaseTeamRolePolicy(
                role="paralegal",
                purpose="Supports evidence intake, chronology cleanup, and document organization.",
                default_scope="assigned_tasks_and_materials",
                allowed_actions=(
                    "view_assigned_materials",
                    "upload_materials",
                    "tag_evidence",
                    "draft_timeline",
                    "comment_on_tasks",
                ),
                denied_actions=("invite_client", "external_share", "finalize_client_deliverable", "manage_team"),
                approval_required_for=("bulk_download_materials", "change_evidence_status"),
            ),
            CaseTeamRolePolicy(
                role="reviewer",
                purpose="Reviews legal conclusions, risk flags, and citation support without owning the case.",
                default_scope="review_packet_and_comments",
                allowed_actions=(
                    "view_review_packet",
                    "comment_on_findings",
                    "request_evidence",
                    "approve_review_checkpoint",
                ),
                denied_actions=("upload_unapproved_materials", "manage_team", "external_share", "delete_materials"),
                approval_required_for=("mark_high_risk_resolved",),
            ),
            CaseTeamRolePolicy(
                role="client",
                purpose="Receives selected deliverables and can provide requested facts through a controlled channel.",
                default_scope="client_shared_items_only",
                allowed_actions=("view_shared_deliverables", "answer_fact_requests", "comment_on_shared_items"),
                denied_actions=(
                    "view_internal_notes",
                    "view_work_product_drafts",
                    "run_ai_review",
                    "invite_team_members",
                    "export_full_case_file",
                ),
                approval_required_for=(),
            ),
        ]

        sensitive_operations = [
            SensitiveOperationPolicy(
                operation="external_share",
                allowed_roles=("owner", "lawyer"),
                audit_required=True,
                approval_required=True,
                rationale="Sharing outside the case team can expose privileged or confidential material.",
            ),
            SensitiveOperationPolicy(
                operation="export_case_file",
                allowed_roles=("owner", "lawyer"),
                audit_required=True,
                approval_required=True,
                rationale="Full exports should be traceable because they may contain complete case history.",
            ),
            SensitiveOperationPolicy(
                operation="bulk_delete_materials",
                allowed_roles=("owner",),
                audit_required=True,
                approval_required=True,
                rationale="Bulk deletion can affect evidence preservation and retention duties.",
            ),
            SensitiveOperationPolicy(
                operation="change_role_or_scope",
                allowed_roles=("owner",),
                audit_required=True,
                approval_required=True,
                rationale="Privilege changes alter who can see confidential case material.",
            ),
            SensitiveOperationPolicy(
                operation="run_ai_review_on_sensitive_materials",
                allowed_roles=("owner", "lawyer"),
                audit_required=True,
                approval_required=False,
                rationale="Model-assisted review should leave a traceable record of who initiated it and why.",
            ),
            SensitiveOperationPolicy(
                operation="finalize_client_deliverable",
                allowed_roles=("owner", "lawyer", "reviewer"),
                audit_required=True,
                approval_required=True,
                rationale="Client-facing outputs need signoff and immutable review history.",
            ),
        ]

        return {
            "status": "ready",
            "policy_id": "case-team-access-policy-v1",
            "method": {
                "type": "least-privilege-case-collaboration-policy",
                "notes": [
                    "The policy describes backend authorization and audit expectations for a case workspace.",
                    "It is deterministic metadata only and does not inspect case files or user records.",
                    "Routers can call build_policy() directly until database-backed permissions are added.",
                ],
            },
            "summary": {
                "role_count": len(role_matrix),
                "sensitive_operation_count": len(sensitive_operations),
                "default_posture": "deny_by_default",
                "client_scope": "client_shared_items_only",
            },
            "role_matrix": [role.to_api() for role in role_matrix],
            "sensitive_operations": [operation.to_api() for operation in sensitive_operations],
            "audit_log_requirements": [
                {
                    "event": "access_granted_or_revoked",
                    "required_fields": (
                        "case_id",
                        "actor_id",
                        "target_member_id",
                        "role",
                        "scope",
                        "reason",
                        "timestamp",
                    ),
                    "retention": "retain_with_case_file_and_firm_policy",
                },
                {
                    "event": "sensitive_operation_attempted",
                    "required_fields": (
                        "case_id",
                        "actor_id",
                        "operation",
                        "decision",
                        "approval_id",
                        "timestamp",
                    ),
                    "retention": "retain_even_when_denied",
                },
                {
                    "event": "client_share_created_or_removed",
                    "required_fields": (
                        "case_id",
                        "actor_id",
                        "shared_item_id",
                        "recipient_role",
                        "share_state",
                        "timestamp",
                    ),
                    "retention": "retain_until_case_retention_window_ends",
                },
            ],
            "least_privilege_defaults": [
                "New members start with no case access until assigned to a case and role.",
                "Client access is limited to explicitly shared deliverables and fact requests.",
                "Internal notes, draft work product, model prompts, and review traces are never client-visible by default.",
                "Paralegal and reviewer access should be scoped to assigned tasks or review packets.",
                "Sensitive operations require audit events even when blocked by policy.",
                "External sharing and full export require explicit approval before execution.",
            ],
            "privacy_and_firm_compliance": [
                "Keep privilege boundaries visible between internal work product and client-shared material.",
                "Use role and case identifiers in policy payloads; avoid raw contact details or private case narratives.",
                "Preserve denied-access events because they are useful for incident review and supervision.",
                "Apply firm retention rules before destructive material changes.",
                "Treat AI review initiation as a traceable legal-workflow event, not a background-only action.",
            ],
            "future_api_contract": {
                "read_policy": "GET /api/v1/maintenance/case-team-access-policy",
                "evaluate_access": "POST /api/v1/cases/{case_id}/team/access/evaluate",
                "audit_events": "GET /api/v1/cases/{case_id}/team/access/audit",
            },
            "validation_commands": [
                "python -m pytest tests/test_case_team_access_policy.py -q",
                "Run the repository credential scan before wiring this policy into a public route.",
            ],
        }
