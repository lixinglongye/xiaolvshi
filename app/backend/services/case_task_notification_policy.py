from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
import re
from typing import Any


DONE_STATUSES = {"done", "completed", "closed", "cancelled"}
URGENT_PRIORITIES = {"urgent", "critical", "high"}
CLIENT_MATERIAL_STATUSES = {"waiting_client", "client_pending", "needs_client_materials"}
LAWYER_REVIEW_STATUSES = {"review_needed", "lawyer_review", "pending_review"}
BLOCKED_TASK_STATUSES = {"blocked", "stalled", "on_hold", "waiting_dependency", "waiting_external"}
URGENT_DUE_DATE_STATUSES = {"overdue", "past_due", "urgent", "due", "due_today", "today"}
DUE_SOON_DATE_STATUSES = {"near", "soon", "due_soon", "upcoming", "within_3_days"}
ACTIVE_ESCALATION_STATUSES = {"active", "pending", "requested", "escalated", "needs_escalation"}
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$")
SAFE_CODE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
RUNTIME_TASK_EVENT_SUMMARY_ID = "case-task-runtime-event-notification-summary-v1"


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

    def build_runtime_event_policy_summary(
        self,
        events: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Summarize notification and escalation suggestions from task runtime events.

        This helper is intentionally side-effect free. It accepts sanitized case
        workbench runtime events, extracts task metadata, and returns policy
        suggestions only. It does not dispatch notifications or persist message
        bodies.
        """
        event_items = self._runtime_event_items(events)
        task_candidates: list[dict[str, Any]] = []
        task_event_summaries: list[dict[str, Any]] = []
        ignored_event_count = 0
        malformed_task_state_count = 0

        for event_index, event in enumerate(event_items, start=1):
            section = self._safe_code(event.get("section"), "")
            if section != "tasks":
                ignored_event_count += 1
                continue

            task_states = self._runtime_task_states(event)
            valid_task_count = 0
            for task_index, task_state in enumerate(task_states, start=1):
                if not isinstance(task_state, Mapping):
                    malformed_task_state_count += 1
                    continue
                valid_task_count += 1
                task_candidates.append(self._task_from_runtime_event(event, task_state, task_index))

            task_event_summaries.append(
                {
                    "event_id": self._safe_identifier(event.get("event_id"), f"runtime-event-{event_index}"),
                    "case_id": self._safe_identifier(event.get("case_ref_hash"), "unknown-case"),
                    "section": "tasks",
                    "operation": self._safe_code(event.get("operation"), "unknown"),
                    "payload_kind": self._safe_code(event.get("payload_kind"), "unknown"),
                    "state_version": self._optional_int(event.get("state_version")),
                    "status_event": self._is_task_status_event(event),
                    "task_state_count": valid_task_count,
                    "changed_task_refs": self._safe_identifier_list(event.get("changed_item_refs")),
                }
            )

        policy = self.build_policy(task_candidates)
        status = "ready" if task_candidates else ("empty" if event_items else "template")
        notification_suggestions = policy["notification_queue"]
        escalation_suggestions = policy["blocking_urgent_tasks"]

        return {
            "status": status,
            "summary_id": RUNTIME_TASK_EVENT_SUMMARY_ID,
            "policy_id": policy["policy_id"],
            "method": {
                "type": "deterministic-runtime-task-event-notification-policy-summary",
                "notes": [
                    "The helper reads task runtime event metadata only.",
                    "No notification dispatch, external call, or database write is performed.",
                    "Raw text, message bodies, fact prose, document text, filenames, prompts, and model output are not copied into the summary.",
                ],
            },
            "summary": {
                "event_count": len(event_items),
                "task_event_count": len(task_event_summaries),
                "ignored_event_count": ignored_event_count,
                "task_status_event_count": sum(1 for item in task_event_summaries if item["status_event"]),
                "task_state_count": len(task_candidates),
                "malformed_task_state_count": malformed_task_state_count,
                "notification_suggestion_count": len(notification_suggestions),
                "escalation_suggestion_count": len(escalation_suggestions),
                "urgent_escalation_suggestion_count": policy["summary"]["urgent_escalation_count"],
                "missing_owner_count": policy["summary"]["missing_owner_count"],
                "dispatch_performed": False,
                "raw_text_stored": False,
            },
            "task_event_summaries": task_event_summaries,
            "notification_suggestions": notification_suggestions,
            "escalation_suggestions": escalation_suggestions,
            "policy_summary": policy["summary"],
            "privacy_notes": [
                "Runtime summaries include opaque case and task refs, status codes, priority, due-window metadata, and trigger ids only.",
                "The caller must render any human-readable notification copy from authorized live case content at dispatch time.",
                "This helper is suitable for previewing notification and escalation policy decisions, not for sending or storing notifications.",
            ],
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
            TriggerRule(
                rule_id="runtime-task-blocker-escalation",
                trigger="active task has blocker_codes, a blocked status, or an active escalation_status",
                severity="blocking",
                channel_order=("team_escalation", "case_workspace"),
                reviewer_action="Review the runtime blocker and either clear it, reassign the task, or escalate to the case owner.",
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
            EscalationRule(
                rule_id="runtime-task-blocker-escalation",
                applies_when="task runtime metadata reports blocker_codes, a blocked status, or an active escalation_status",
                escalate_to=("task_owner", "case_owner", "team_coordinator"),
                action="Create a policy suggestion for blocker review without sending a notification automatically.",
                audit_required=True,
            ),
        )

    def _evaluate_task(self, task: dict[str, Any]) -> dict[str, Any]:
        status = str(task.get("status") or "open").strip().lower()
        priority = str(task.get("priority") or "normal").strip().lower()
        days_until_due = self._optional_int(task.get("days_until_due"))
        due_date_status = self._safe_code(task.get("due_date_status"), "")
        escalation_status = self._safe_code(task.get("escalation_status"), "none")
        blocker_codes = self._safe_code_tuple(task.get("blocker_codes"))
        done = status in DONE_STATUSES
        owner_missing = not done and not self._has_owner(task)
        urgent_escalation = not done and (
            (days_until_due is not None and days_until_due <= self.URGENT_DUE_DAYS) or priority in URGENT_PRIORITIES
            or due_date_status in URGENT_DUE_DATE_STATUSES
        )
        due_soon = not done and (
            (days_until_due is not None and self.URGENT_DUE_DAYS < days_until_due <= self.DUE_SOON_DAYS)
            or due_date_status in DUE_SOON_DATE_STATUSES
        )
        client_material = not done and self._requires_client_materials(task, status)
        lawyer_review = not done and self._requires_lawyer_review(task, status)
        runtime_blocker = not done and (
            status in BLOCKED_TASK_STATUSES
            or escalation_status in ACTIVE_ESCALATION_STATUSES
            or bool(blocker_codes)
        )

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
        if runtime_blocker:
            triggers.append("runtime-task-blocker-escalation")
            recommended_channels.extend(["team_escalation", "case_workspace"])
            blocking_reasons.append("runtime_task_blocker")

        return {
            "task_id": str(task.get("task_id") or task.get("id") or "unknown-task"),
            "case_id": str(task.get("case_id") or "unknown-case"),
            "status": status,
            "priority": priority,
            "days_until_due": days_until_due,
            "due_date_status": due_date_status,
            "escalation_status": escalation_status,
            "blocker_codes": blocker_codes,
            "done": done,
            "owner_missing": owner_missing,
            "urgent_escalation": urgent_escalation,
            "requires_client_materials": client_material,
            "requires_lawyer_review": lawyer_review,
            "runtime_blocker": runtime_blocker,
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

    def _runtime_event_items(
        self,
        events: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[Mapping[str, Any]]:
        if events is None:
            return []
        if isinstance(events, Mapping):
            return [events]
        if isinstance(events, (str, bytes)):
            return []
        if isinstance(events, Iterable):
            return [event for event in events if isinstance(event, Mapping)]
        return []

    def _runtime_task_states(self, event: Mapping[str, Any]) -> list[Any]:
        state_delta = event.get("state_delta")
        if not isinstance(state_delta, Mapping):
            return []
        task_states = state_delta.get("task_states")
        if not isinstance(task_states, list):
            return []
        return task_states

    def _task_from_runtime_event(
        self,
        event: Mapping[str, Any],
        task_state: Mapping[str, Any],
        task_index: int,
    ) -> dict[str, Any]:
        return {
            "case_id": self._safe_identifier(event.get("case_ref_hash"), "unknown-case"),
            "task_id": self._safe_identifier(
                task_state.get("task_ref_hash") or task_state.get("task_id"),
                f"unknown-task-{task_index}",
            ),
            "status": self._safe_code(task_state.get("status"), "open"),
            "priority": self._safe_code(task_state.get("priority"), "normal"),
            "task_type": self._safe_code(task_state.get("task_type"), ""),
            "owner_role": self._safe_code(task_state.get("owner_role"), ""),
            "due_date_status": self._safe_code(task_state.get("due_date_status"), ""),
            "escalation_status": self._safe_code(task_state.get("escalation_status"), "none"),
            "blocker_codes": self._safe_code_tuple(task_state.get("blocker_codes")),
            "requires_lawyer_review": task_state.get("review_required") is True,
        }

    def _is_task_status_event(self, event: Mapping[str, Any]) -> bool:
        changed_fields = event.get("changed_field_names")
        if not isinstance(changed_fields, list):
            return False
        return any(isinstance(field, str) and field.strip().lower() == "status" for field in changed_fields)

    def _safe_identifier(self, value: Any, fallback: str) -> str:
        if not isinstance(value, str):
            return fallback
        text = value.strip()
        if not text or not SAFE_IDENTIFIER_PATTERN.match(text):
            return fallback
        return text

    def _safe_identifier_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        safe_items: list[str] = []
        for item in value:
            safe_item = self._safe_identifier(item, "")
            if safe_item:
                safe_items.append(safe_item)
        return list(dict.fromkeys(safe_items))

    def _safe_code(self, value: Any, fallback: str) -> str:
        if not isinstance(value, str):
            return fallback
        text = value.strip().lower()
        if not text or not SAFE_CODE_PATTERN.match(text):
            return fallback
        return text

    def _safe_code_tuple(self, value: Any) -> tuple[str, ...]:
        if not isinstance(value, list):
            return ()
        safe_codes = [self._safe_code(item, "") for item in value]
        return tuple(dict.fromkeys(code for code in safe_codes if code))
