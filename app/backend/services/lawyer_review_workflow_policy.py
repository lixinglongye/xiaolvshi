from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


ReviewWorkflowStatus = Literal[
    "draft",
    "lawyer_review",
    "approved",
    "rejected",
    "revise_required",
    "client_deliverable",
]

REVIEW_WORKFLOW_STATUSES: tuple[ReviewWorkflowStatus, ...] = (
    "draft",
    "lawyer_review",
    "approved",
    "rejected",
    "revise_required",
    "client_deliverable",
)


@dataclass(frozen=True)
class ReviewStatusDefinition:
    status: ReviewWorkflowStatus
    meaning: str
    responsible_roles: tuple[str, ...]
    client_visible: bool
    terminal: bool = False

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["responsible_roles"] = list(self.responsible_roles)
        return data


@dataclass(frozen=True)
class ReviewTransitionRule:
    from_status: ReviewWorkflowStatus
    to_status: ReviewWorkflowStatus
    allowed_roles: tuple[str, ...]
    required_fields: tuple[str, ...]
    audit_event: str
    reason_required: bool = False

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["allowed_roles"] = list(self.allowed_roles)
        data["required_fields"] = list(self.required_fields)
        return data


class LawyerReviewWorkflowPolicyService:
    """Describe the required lawyer review state machine for AI generated outputs."""

    LAWYER_ROLES = ("lawyer", "owner")
    REASON_REQUIRED_TARGETS = ("rejected", "revise_required")

    def build_policy(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        transitions = self._transition_rules()
        blocking_conditions = self._blocking_conditions(payload, transitions)

        return {
            "status": "ready",
            "policy_id": "lawyer-review-workflow-policy-v1",
            "summary": {
                "state_count": len(REVIEW_WORKFLOW_STATUSES),
                "transition_count": len(transitions),
                "lawyer_gate_required": True,
                "draft_direct_to_client_deliverable_allowed": False,
                "blocking_condition_count": len(blocking_conditions),
            },
            "state_enumeration": [item.to_api() for item in self._status_definitions()],
            "allowed_state_transitions": [item.to_api() for item in transitions],
            "forbidden_state_transitions": [
                {
                    "from_status": "draft",
                    "to_status": "client_deliverable",
                    "reason": "AI generated drafts must first pass lawyer_review and approved gates before client delivery.",
                },
                {
                    "from_status": "lawyer_review",
                    "to_status": "client_deliverable",
                    "reason": "Reviewed work must be explicitly approved before it becomes client deliverable.",
                },
            ],
            "blocking_conditions": blocking_conditions,
            "role_requirements": [
                {
                    "gate": "submit_for_lawyer_review",
                    "required_roles": ["lawyer", "owner", "paralegal"],
                    "notes": "Paralegals may submit drafts, but cannot approve client delivery.",
                },
                {
                    "gate": "approve_ai_output",
                    "required_roles": list(self.LAWYER_ROLES),
                    "notes": "Approval is restricted to a lawyer or owner role.",
                },
                {
                    "gate": "deliver_to_client",
                    "required_roles": list(self.LAWYER_ROLES),
                    "notes": "Client delivery requires a prior approved state and a lawyer accountable for the release.",
                },
                {
                    "gate": "reject_or_request_revision",
                    "required_roles": list(self.LAWYER_ROLES),
                    "required_fields": ["reason"],
                    "notes": "Rejection and revision requests must carry a concrete reason for audit and follow-up.",
                },
            ],
            "audit_log_requirements": [
                {
                    "event": "review_transition_requested",
                    "required_fields": [
                        "actor_id",
                        "actor_role",
                        "from_status",
                        "to_status",
                        "artifact_id",
                        "created_at",
                    ],
                },
                {
                    "event": "lawyer_review_decision_recorded",
                    "required_fields": ["actor_id", "actor_role", "decision", "artifact_id", "reason"],
                },
                {
                    "event": "client_deliverable_released",
                    "required_fields": ["actor_id", "actor_role", "artifact_id", "approved_at", "release_channel"],
                },
            ],
            "low_resource_validation_commands": [
                "python -m pytest tests/test_lawyer_review_workflow_policy.py -q",
                "python -m compileall services/lawyer_review_workflow_policy.py",
            ],
            "privacy_notes": [
                "Store only review metadata and artifact identifiers in this policy layer.",
                "Keep client facts, raw evidence text, and contact details in the case workspace with access controls.",
                "Expose client_deliverable artifacts only after the approved gate records a lawyer accountable for release.",
            ],
        }

    def _status_definitions(self) -> tuple[ReviewStatusDefinition, ...]:
        return (
            ReviewStatusDefinition(
                status="draft",
                meaning="AI output or human edited working copy that is not ready for legal reliance.",
                responsible_roles=("owner", "lawyer", "paralegal"),
                client_visible=False,
            ),
            ReviewStatusDefinition(
                status="lawyer_review",
                meaning="Queued or active review by a qualified lawyer before any client-facing use.",
                responsible_roles=self.LAWYER_ROLES,
                client_visible=False,
            ),
            ReviewStatusDefinition(
                status="approved",
                meaning="A lawyer has approved the artifact for controlled delivery or downstream generation.",
                responsible_roles=self.LAWYER_ROLES,
                client_visible=False,
            ),
            ReviewStatusDefinition(
                status="rejected",
                meaning="A lawyer rejected the artifact and recorded the reason it must not be used.",
                responsible_roles=self.LAWYER_ROLES,
                client_visible=False,
                terminal=True,
            ),
            ReviewStatusDefinition(
                status="revise_required",
                meaning="A lawyer requested changes before the artifact can be reviewed again.",
                responsible_roles=("owner", "lawyer", "paralegal"),
                client_visible=False,
            ),
            ReviewStatusDefinition(
                status="client_deliverable",
                meaning="Approved artifact released to the client-facing delivery surface.",
                responsible_roles=self.LAWYER_ROLES,
                client_visible=True,
                terminal=True,
            ),
        )

    def _transition_rules(self) -> tuple[ReviewTransitionRule, ...]:
        return (
            ReviewTransitionRule(
                from_status="draft",
                to_status="lawyer_review",
                allowed_roles=("owner", "lawyer", "paralegal"),
                required_fields=("artifact_id", "submitted_by", "review_scope"),
                audit_event="review_transition_requested",
            ),
            ReviewTransitionRule(
                from_status="lawyer_review",
                to_status="approved",
                allowed_roles=self.LAWYER_ROLES,
                required_fields=("artifact_id", "reviewer_id", "reviewed_at"),
                audit_event="lawyer_review_decision_recorded",
            ),
            ReviewTransitionRule(
                from_status="lawyer_review",
                to_status="rejected",
                allowed_roles=self.LAWYER_ROLES,
                required_fields=("artifact_id", "reviewer_id", "reason"),
                audit_event="lawyer_review_decision_recorded",
                reason_required=True,
            ),
            ReviewTransitionRule(
                from_status="lawyer_review",
                to_status="revise_required",
                allowed_roles=self.LAWYER_ROLES,
                required_fields=("artifact_id", "reviewer_id", "reason"),
                audit_event="lawyer_review_decision_recorded",
                reason_required=True,
            ),
            ReviewTransitionRule(
                from_status="revise_required",
                to_status="draft",
                allowed_roles=("owner", "lawyer", "paralegal"),
                required_fields=("artifact_id", "revision_id"),
                audit_event="review_transition_requested",
            ),
            ReviewTransitionRule(
                from_status="approved",
                to_status="client_deliverable",
                allowed_roles=self.LAWYER_ROLES,
                required_fields=("artifact_id", "approved_at", "release_channel"),
                audit_event="client_deliverable_released",
            ),
        )

    def _blocking_conditions(
        self,
        payload: dict[str, Any],
        transitions: tuple[ReviewTransitionRule, ...],
    ) -> list[dict[str, Any]]:
        if not payload:
            return []

        blockers: list[dict[str, Any]] = []
        from_status = payload.get("from_status")
        to_status = payload.get("to_status")
        actor_role = payload.get("actor_role")

        matched_transition = next(
            (
                transition
                for transition in transitions
                if transition.from_status == from_status and transition.to_status == to_status
            ),
            None,
        )

        if matched_transition is None:
            blockers.append(
                {
                    "code": "transition_not_allowed",
                    "message": f"{from_status or 'unknown'} cannot transition to {to_status or 'unknown'}.",
                }
            )
            return blockers

        if actor_role not in matched_transition.allowed_roles:
            blockers.append(
                {
                    "code": "role_not_allowed",
                    "message": f"{actor_role or 'unknown'} cannot move {from_status} to {to_status}.",
                    "allowed_roles": list(matched_transition.allowed_roles),
                }
            )

        missing_fields = [field for field in matched_transition.required_fields if not payload.get(field)]
        if missing_fields:
            blockers.append(
                {
                    "code": "missing_required_fields",
                    "message": "Transition is missing required review metadata.",
                    "missing_fields": missing_fields,
                }
            )

        if matched_transition.reason_required and not str(payload.get("reason", "")).strip():
            blockers.append(
                {
                    "code": "reason_required",
                    "message": "Rejected and revise_required decisions must include a reason.",
                    "required_for": list(self.REASON_REQUIRED_TARGETS),
                }
            )

        return blockers
