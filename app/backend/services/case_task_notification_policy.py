from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DONE_STATUSES = {"done", "completed", "closed", "cancelled"}
URGENT_PRIORITIES = {"urgent", "critical", "high"}
CLIENT_MATERIAL_STATUSES = {"waiting_client", "client_pending", "needs_client_materials"}
LAWYER_REVIEW_STATUSES = {"review_needed", "lawyer_review", "pending_review"}


@dataclass(frozen=True)
class NotificationChannel:
    channel: str
    purpose: str
    default_audience: tuple[str, ...]
    allowed_payload_fields: tuple[str, ...]
    cadence: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["default_audience"] = list(self.default_audience)
        data["allowed_payload_fields"] = list(self.allowed_payload_fields)
        return data


@dataclass(frozen=True)
class TriggerRule:
    rule_id: str
    trigger: str
    severity: str
    channel_order: tuple[str, ...]
    reviewer_action: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["channel_order"] = list(self.channel_order)
        return data


@dataclass(frozen=True)
class EscalationRule:
    rule_id: str
    applies_when: str
    escalate_to: tuple[str, ...]
    action: str
    audit_required: bool

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["escalate_to"] = list(self.escalate_to)
        return data


class CaseTaskNotificationPolicyService:
    """Build deterministic notification and escalation metadata for case tasks."""

    URGENT_DUE_DAYS = 1
    DUE_SOON_DAYS = 3

    def build_policy(self, tasks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        task_items = tasks if isinstance(tasks, list) else []
        evaluated_tasks = [self._evaluate_task(task) for task in task_items if isinstance(task, dict)]
        active_tasks = [item for item in evaluated_tasks if not item["done"]]
        blocking_urgent_tasks = [
            self._task_summary(item)
            for item in active_tasks
            if item["urgent_escalation"] or item["owner_missing"] or item["blocking_reasons"]
        ]
        notification_queue = [
            self._task_summary(item)
            for item in active_tasks
            if item["triggers"] and not item["owner_missing"]
        ]

        return {
            "status": "ready",
            "policy_id": "case-task-notification-policy-v1",
            "method": {
                "type": "deterministic-case-task-notification-policy",
                "notes": [
                    "The policy evaluates task metadata only and does not use the current date.",
                    "Call build_policy(tasks) with days_until_due, priority, status, owner_id, and task_type fields.",
                    "Completed tasks are excluded from reminders, escalations, and blocker lists.",
                ],
            },
            "summary": {
                "task_count": len(evaluated_tasks),
                "active_task_count": len(active_tasks),
                "done_task_count": len(evaluated_tasks) - len(active_tasks),
                "notification_count": len(notification_queue),
                "urgent_escalation_count": sum(1 for item in active_tasks if item["urgent_escalation"]),
                "missing_owner_count": sum(1 for item in active_tasks if item["owner_missing"]),
                "blocking_urgent_count": len(blocking_urgent_tasks),
            },
            "notification_channels": [channel.to_api() for channel in self._notification_channels()],
            "trigger_rules": [rule.to_api() for rule in self._trigger_rules()],
            "escalation_rules": [rule.to_api() for rule in self._escalation_rules()],
            "owner_assignment_requirements": [
                "Every active case task must have owner_id or owner_role before reminders can be dispatched.",
                "Missing owner blocks downstream notification because accountability would be ambiguous.",
                "Urgent tasks without an owner must route to case_owner and team_coordinator for assignment.",
                "Client material requests must include a responsible lawyer or case owner before client-facing reminders are sent.",
                "Lawyer review tasks must name a reviewer role or reviewer member before signoff reminders are emitted.",
            ],
            "notification_queue": notification_queue,
            "blocking_urgent_tasks": blocking_urgent_tasks,
            "evaluated_tasks": [self._task_summary(item, include_clear_tasks=True) for item in evaluated_tasks],
            "audit_record_requirements": [
                "case_id",
                "task_id",
                "trigger_rule_id",
                "escalation_rule_id",
                "actor_role",
                "target_role",
                "decision",
                "scheduled_at",
            ],
            "low_resource_validation_commands": [
                {
                    "id": "case-task-notification-policy-tests",
                    "command": "python -m pytest tests/test_case_task_notification_policy.py -q",
                    "resource_note": "Runs deterministic metadata tests only; no model call, network call, or large fixture is required.",
                },
                {
                    "id": "case-task-notification-policy-diff-check",
                    "command": "git diff --check -- app/backend/services/case_task_notification_policy.py app/backend/tests/test_case_task_notification_policy.py docs/CASE_TASK_NOTIFICATION_POLICY.md",
                    "resource_note": "Checks whitespace in the three files for this policy.",
                },
            ],
            "privacy_notes": [
                "Use case_id, task_id, role, status, priority, and due-window metadata instead of raw case narratives.",
                "Client-facing reminders should reference requested material categories, not internal legal work product.",
                "Notification payloads should avoid personal contact routes and full document text.",
                "Escalation audit records should store policy decisions and role targets rather than private message bodies.",
            ],
            "future_api_contract": {
                "read_policy": "GET /api/v1/maintenance/case-task-notification-policy",
                "evaluate_tasks": "POST /api/v1/cases/{case_id}/tasks/notification-policy/evaluate",
                "dispatch_log": "GET /api/v1/cases/{case_id}/tasks/notification-log",
            },
        }

    def _notification_channels(self) -> tuple[NotificationChannel, ...]:
        return (
            NotificationChannel(
                channel="case_workspace",
                purpose="Primary in-product reminder for active case team members.",
                default_audience=("owner", "lawyer", "paralegal", "reviewer"),
                allowed_payload_fields=("case_id", "task_id", "status", "priority", "days_until_due"),
                cadence="immediate_for_urgent_daily_for_due_soon",
            ),
            NotificationChannel(
                channel="client_portal",
                purpose="Controlled request path for client material collection.",
                default_audience=("client", "lawyer"),
                allowed_payload_fields=("case_id", "task_id", "requested_material_type", "days_until_due"),
                cadence="once_per_due_window_with_lawyer_owner_visible",
            ),
            NotificationChannel(
                channel="review_queue",
                purpose="Lawyer review and signoff reminders before client delivery.",
                default_audience=("lawyer", "reviewer", "owner"),
                allowed_payload_fields=("case_id", "task_id", "review_gate", "priority", "days_until_due"),
                cadence="immediate_for_review_needed_then_daily_until_resolved",
            ),
            NotificationChannel(
                channel="team_escalation",
                purpose="Escalation path for urgent due dates, missing owners, or blocked tasks.",
                default_audience=("case_owner", "team_coordinator", "supervising_lawyer"),
                allowed_payload_fields=("case_id", "task_id", "trigger_rule_id", "severity", "days_until_due"),
                cadence="immediate_for_blockers_and_urgent_tasks",
            ),
        )

    def _trigger_rules(self) -> tuple[TriggerRule, ...]:
        return (
            TriggerRule(
                rule_id="due-soon-reminder",
                trigger="active task has days_until_due between 2 and 3",
                severity="medium",
                channel_order=("case_workspace",),
                reviewer_action="Remind the assigned owner to update progress before the deadline window becomes urgent.",
            ),
            TriggerRule(
                rule_id="urgent-deadline-escalation",
                trigger="active task has days_until_due less than or equal to 1 or priority is urgent or critical",
                severity="critical",
                channel_order=("case_workspace", "team_escalation"),
                reviewer_action="Escalate to the responsible owner and supervising role until the task is moved forward or reassigned.",
            ),
            TriggerRule(
                rule_id="missing-owner-blocker",
                trigger="active task lacks owner_id and owner_role",
                severity="blocking",
                channel_order=("team_escalation",),
                reviewer_action="Assign an accountable owner before dispatching reminders or client requests.",
            ),
            TriggerRule(
                rule_id="client-material-reminder",
                trigger="active task waits on client materials or has requires_client_materials set",
                severity="high",
                channel_order=("client_portal", "case_workspace"),
                reviewer_action="Ask the client for the missing material while keeping the responsible lawyer visible.",
            ),
            TriggerRule(
                rule_id="lawyer-review-reminder",
                trigger="active task requires lawyer review or has a review-needed status",
                severity="high",
                channel_order=("review_queue", "case_workspace"),
                reviewer_action="Route the item to legal review before any client-facing delivery step.",
            ),
        )

    def _escalation_rules(self) -> tuple[EscalationRule, ...]:
        return (
            EscalationRule(
                rule_id="urgent-owner-escalation",
                applies_when="days_until_due less than or equal to 1 or priority is urgent or critical",
                escalate_to=("task_owner", "case_owner", "supervising_lawyer"),
                action="Create an urgent escalation record and keep reminders active until the status changes.",
                audit_required=True,
            ),
            EscalationRule(
                rule_id="missing-owner-escalation",
                applies_when="active task has no owner_id and no owner_role",
                escalate_to=("case_owner", "team_coordinator"),
                action="Block dispatch and request owner assignment.",
                audit_required=True,
            ),
            EscalationRule(
                rule_id="client-material-escalation",
                applies_when="client material request remains active inside the due-soon window",
                escalate_to=("task_owner", "lawyer", "case_owner"),
                action="Send a controlled client portal reminder and alert the responsible legal owner.",
                audit_required=True,
            ),
            EscalationRule(
                rule_id="lawyer-review-escalation",
                applies_when="lawyer review is required before delivery or deadline closure",
                escalate_to=("reviewer", "task_owner", "case_owner"),
                action="Move the task into review queue and block client delivery until review is complete.",
                audit_required=True,
            ),
        )

    def _evaluate_task(self, task: dict[str, Any]) -> dict[str, Any]:
        status = str(task.get("status") or "open").strip().lower()
        priority = str(task.get("priority") or "normal").strip().lower()
        days_until_due = self._optional_int(task.get("days_until_due"))
        done = status in DONE_STATUSES
        owner_missing = not done and not self._has_owner(task)
        urgent_escalation = not done and (
            (days_until_due is not None and days_until_due <= self.URGENT_DUE_DAYS) or priority in URGENT_PRIORITIES
        )
        due_soon = not done and days_until_due is not None and self.URGENT_DUE_DAYS < days_until_due <= self.DUE_SOON_DAYS
        client_material = not done and self._requires_client_materials(task, status)
        lawyer_review = not done and self._requires_lawyer_review(task, status)

        triggers: list[str] = []
        blocking_reasons: list[str] = []
        recommended_channels: list[str] = []

        if due_soon:
            triggers.append("due-soon-reminder")
            recommended_channels.append("case_workspace")
        if urgent_escalation:
            triggers.append("urgent-deadline-escalation")
            recommended_channels.extend(["case_workspace", "team_escalation"])
            blocking_reasons.append("urgent_due_window")
        if owner_missing:
            triggers.append("missing-owner-blocker")
            recommended_channels.append("team_escalation")
            blocking_reasons.append("missing_owner")
        if client_material:
            triggers.append("client-material-reminder")
            recommended_channels.extend(["client_portal", "case_workspace"])
        if lawyer_review:
            triggers.append("lawyer-review-reminder")
            recommended_channels.extend(["review_queue", "case_workspace"])

        return {
            "task_id": str(task.get("task_id") or task.get("id") or "unknown-task"),
            "case_id": str(task.get("case_id") or "unknown-case"),
            "status": status,
            "priority": priority,
            "days_until_due": days_until_due,
            "done": done,
            "owner_missing": owner_missing,
            "urgent_escalation": urgent_escalation,
            "requires_client_materials": client_material,
            "requires_lawyer_review": lawyer_review,
            "triggers": tuple(dict.fromkeys(triggers)),
            "blocking_reasons": tuple(dict.fromkeys(blocking_reasons)),
            "recommended_channels": tuple(dict.fromkeys(recommended_channels)),
        }

    def _task_summary(self, evaluated_task: dict[str, Any], include_clear_tasks: bool = False) -> dict[str, Any]:
        summary = {
            "case_id": evaluated_task["case_id"],
            "task_id": evaluated_task["task_id"],
            "status": evaluated_task["status"],
            "priority": evaluated_task["priority"],
            "days_until_due": evaluated_task["days_until_due"],
            "owner_missing": evaluated_task["owner_missing"],
            "urgent_escalation": evaluated_task["urgent_escalation"],
            "triggers": list(evaluated_task["triggers"]),
            "recommended_channels": list(evaluated_task["recommended_channels"]),
            "blocking_reasons": list(evaluated_task["blocking_reasons"]),
        }
        if include_clear_tasks:
            summary["done"] = evaluated_task["done"]
            summary["requires_client_materials"] = evaluated_task["requires_client_materials"]
            summary["requires_lawyer_review"] = evaluated_task["requires_lawyer_review"]
        return summary

    def _has_owner(self, task: dict[str, Any]) -> bool:
        return bool(task.get("owner_id") or task.get("owner_role"))

    def _requires_client_materials(self, task: dict[str, Any], status: str) -> bool:
        task_type = str(task.get("task_type") or "").strip().lower()
        return (
            task.get("requires_client_materials") is True
            or task.get("waiting_on_client") is True
            or status in CLIENT_MATERIAL_STATUSES
            or task_type in {"client_material_request", "client_intake_followup"}
        )

    def _requires_lawyer_review(self, task: dict[str, Any], status: str) -> bool:
        task_type = str(task.get("task_type") or "").strip().lower()
        return (
            task.get("requires_lawyer_review") is True
            or status in LAWYER_REVIEW_STATUSES
            or task_type in {"lawyer_review", "delivery_review", "legal_signoff"}
        )

    def _optional_int(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
