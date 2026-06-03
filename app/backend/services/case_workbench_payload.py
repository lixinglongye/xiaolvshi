from __future__ import annotations

from datetime import date
import re
from typing import Any

from services.case_evidence_graph import CaseEvidenceGraphService
from services.case_task_notification_policy import CaseTaskNotificationPolicyService
from services.case_timeline_deadline_risk import CaseTimelineDeadlineRiskService
from services.deadline_validation_policy import DeadlineValidationPolicyService
from services.matter_intake_readiness_policy import MatterIntakeReadinessPolicyService


SENSITIVE_TEXT_PATTERN = re.compile(
    r"("
    r"sk-[A-Za-z0-9]{20,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"password|secret|api[_ -]?key|authorization\s*[:=]|bearer\s+[A-Za-z0-9._-]+"
    r")",
    re.IGNORECASE,
)

SECTION_ORDER = (
    "matter_intake",
    "deadline_validation",
    "timeline_risk",
    "task_notifications",
    "evidence_graph",
)

SECTION_TITLES = {
    "matter_intake": "Matter intake",
    "deadline_validation": "Deadline validation",
    "timeline_risk": "Timeline risk",
    "task_notifications": "Task notifications",
    "evidence_graph": "Evidence graph",
}

SECTION_SOURCES = {
    "matter_intake": "MatterIntakeReadinessPolicyService",
    "deadline_validation": "DeadlineValidationPolicyService",
    "timeline_risk": "CaseTimelineDeadlineRiskService",
    "task_notifications": "CaseTaskNotificationPolicyService",
    "evidence_graph": "CaseEvidenceGraphService",
}

ACTION_PRIORITY_RANK = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


class CaseWorkbenchPayloadService:
    """Assemble deterministic case workbench metadata for frontend consumption."""

    def __init__(
        self,
        *,
        intake_service: MatterIntakeReadinessPolicyService | None = None,
        deadline_service: DeadlineValidationPolicyService | None = None,
        timeline_service: CaseTimelineDeadlineRiskService | None = None,
        task_service: CaseTaskNotificationPolicyService | None = None,
        evidence_service: CaseEvidenceGraphService | None = None,
    ) -> None:
        self.intake_service = intake_service or MatterIntakeReadinessPolicyService()
        self.deadline_service = deadline_service or DeadlineValidationPolicyService()
        self.timeline_service = timeline_service or CaseTimelineDeadlineRiskService()
        self.task_service = task_service or CaseTaskNotificationPolicyService()
        self.evidence_service = evidence_service or CaseEvidenceGraphService()

    def build_payload(
        self,
        *,
        case_id: str | int | None = None,
        matter_id: str | int | None = None,
        intake: dict[str, Any] | None = None,
        deadlines: list[dict[str, Any]] | None = None,
        timeline_events: list[dict[str, Any]] | None = None,
        tasks: list[dict[str, Any]] | None = None,
        evidence_report: dict[str, Any] | None = None,
        reference_date: str | date | None = None,
    ) -> dict[str, Any]:
        source_payloads = {
            "matter_intake": self._source_or_template(
                "matter_intake",
                intake is not None,
                lambda: self.intake_service.evaluate(intake),
            ),
            "deadline_validation": self._source_or_template(
                "deadline_validation",
                deadlines is not None,
                lambda: self.deadline_service.build_policy(deadlines, reference_date=reference_date),
            ),
            "timeline_risk": self._source_or_template(
                "timeline_risk",
                timeline_events is not None,
                lambda: self.timeline_service.build_assessment(events=timeline_events),
            ),
            "task_notifications": self._source_or_template(
                "task_notifications",
                tasks is not None,
                lambda: self.task_service.build_policy(tasks),
            ),
            "evidence_graph": self._source_or_template(
                "evidence_graph",
                evidence_report is not None,
                lambda: self.evidence_service.build_graph(evidence_report),
            ),
        }
        sections = [self._build_section(section_id, source_payloads[section_id]) for section_id in SECTION_ORDER]
        blockers = self._sort_blockers(self._build_blockers(source_payloads))
        next_actions = self._sort_actions(self._build_next_actions(source_payloads, blockers))
        dashboard = self._build_dashboard(sections, blockers, next_actions)

        payload = {
            "payload_id": "case-workbench-payload-v1",
            "version": 1,
            "status": dashboard["status"],
            "case_ref": self._safe_identifier(case_id, fallback="case-unspecified"),
            "matter_ref": self._safe_identifier(matter_id, fallback="matter-unspecified"),
            "method": {
                "type": "deterministic-local-case-workbench-payload",
                "notes": [
                    "Inputs are metadata dictionaries and lists supplied by the caller.",
                    "The service does not read databases, environment variables, files, the network, or the current date.",
                    "Sections with no supplied input are returned as frontend empty states.",
                ],
            },
            "dashboard": dashboard,
            "sections": sections,
            "blockers": blockers,
            "next_actions": next_actions,
            "source_contracts": self._source_contracts(source_payloads),
            "validation_commands": [
                "python -m pytest tests/test_case_workbench_payload.py -q",
                "python -m compileall services/case_workbench_payload.py tests/test_case_workbench_payload.py",
            ],
            "privacy_note": (
                "The payload exposes IDs, statuses, counts, controlled labels, and reviewer actions only. "
                "Keep raw narratives, document text, direct contact data, access tokens, and private messages "
                "outside this dashboard contract."
            ),
        }
        return self._sanitize(payload)

    def _source_or_template(
        self,
        section_id: str,
        supplied: bool,
        builder: Any,
    ) -> dict[str, Any]:
        if not supplied:
            return self._template_source(section_id)
        payload = builder()
        payload["_input_state"] = "evaluated"
        return payload

    def _template_source(self, section_id: str) -> dict[str, Any]:
        return {
            "status": "template",
            "_input_state": "not_supplied",
            "summary": {
                "deterministic": True,
                "evaluated": False,
            },
            "empty_state": {
                "title": SECTION_TITLES[section_id],
                "message": "No metadata was supplied for this workbench section.",
            },
            "recommended_actions": [
                f"Supply {section_id.replace('_', ' ')} metadata before relying on this section.",
            ],
        }

    def _build_section(self, section_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        return {
            "id": section_id,
            "title": SECTION_TITLES[section_id],
            "source": SECTION_SOURCES[section_id],
            "input_state": payload.get("_input_state", "evaluated"),
            "status": self._section_status(section_id, payload),
            "raw_status": str(payload.get("status") or "unknown"),
            "severity": self._section_severity(section_id, payload),
            "summary": self._safe_summary(section_id, summary),
            "metrics": self._section_metrics(section_id, summary),
            "preview_items": self._section_preview(section_id, payload),
            "empty_state": payload.get("empty_state"),
        }

    def _section_status(self, section_id: str, payload: dict[str, Any]) -> str:
        if payload.get("_input_state") == "not_supplied":
            return "template"

        raw_status = str(payload.get("status") or "").strip().lower()
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}

        if section_id == "matter_intake":
            return {"fail": "blocked", "warn": "needs_attention", "pass": "ready"}.get(raw_status, "needs_attention")
        if section_id == "deadline_validation":
            if raw_status in {"needs_date_verification", "lawyer_review_required"}:
                return "blocked"
            if raw_status == "reminder_required":
                return "needs_attention"
            return "ready"
        if section_id == "timeline_risk":
            if int(summary.get("blocking_urgent_count") or 0) > 0:
                return "blocked"
            if int(summary.get("risk_flag_count") or 0) > 0:
                return "needs_attention"
            return "ready" if raw_status != "template" else "template"
        if section_id == "task_notifications":
            if int(summary.get("blocking_urgent_count") or 0) > 0:
                return "blocked"
            if int(summary.get("notification_count") or 0) > 0:
                return "needs_attention"
            return "ready"
        if section_id == "evidence_graph":
            if raw_status == "blocked":
                return "blocked"
            if raw_status == "review_recommended":
                return "needs_attention"
            return "ready" if raw_status != "template" else "template"
        return raw_status or "unknown"

    def _section_severity(self, section_id: str, payload: dict[str, Any]) -> str:
        status = self._section_status(section_id, payload)
        return {
            "blocked": "blocking",
            "needs_attention": "warning",
            "ready": "clear",
            "template": "empty",
        }.get(status, "warning")

    def _safe_summary(self, section_id: str, summary: dict[str, Any]) -> dict[str, Any]:
        allowed_fields = {
            "matter_intake": (
                "check_count",
                "passed_check_count",
                "warning_check_count",
                "failed_check_count",
                "ready_for_matter_creation",
                "restricted_creation_allowed",
                "conflict_review_required",
                "lawyer_review_required",
                "privacy_minimized",
                "deterministic",
                "evaluated",
            ),
            "deadline_validation": (
                "check_count",
                "ok_count",
                "reminder_count",
                "lawyer_review_count",
                "overdue_count",
                "urgent_count",
                "near_count",
                "missing_date_count",
                "deterministic",
                "evaluated",
            ),
            "timeline_risk": (
                "assessed_event_count",
                "risk_flag_count",
                "blocking_urgent_count",
                "missing_fact_count",
                "deterministic",
                "evaluated",
            ),
            "task_notifications": (
                "task_count",
                "active_task_count",
                "done_task_count",
                "notification_count",
                "urgent_escalation_count",
                "missing_owner_count",
                "blocking_urgent_count",
                "deterministic",
                "evaluated",
            ),
            "evidence_graph": (
                "node_count",
                "edge_count",
                "risk_count",
                "evidence_requirement_count",
                "citation_count",
                "pending_fact_count",
                "blocking_gap_count",
                "warning_gap_count",
                "deterministic",
                "evaluated",
            ),
        }[section_id]
        return {field: summary[field] for field in allowed_fields if field in summary}

    def _section_metrics(self, section_id: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
        metric_fields = {
            "matter_intake": (
                ("check_count", "Checks"),
                ("failed_check_count", "Failed"),
                ("warning_check_count", "Warnings"),
            ),
            "deadline_validation": (
                ("check_count", "Deadlines"),
                ("overdue_count", "Overdue"),
                ("urgent_count", "Urgent"),
                ("missing_date_count", "Missing dates"),
            ),
            "timeline_risk": (
                ("assessed_event_count", "Events"),
                ("risk_flag_count", "Risk flags"),
                ("blocking_urgent_count", "Urgent blockers"),
            ),
            "task_notifications": (
                ("active_task_count", "Active tasks"),
                ("notification_count", "Notifications"),
                ("blocking_urgent_count", "Task blockers"),
            ),
            "evidence_graph": (
                ("risk_count", "Risks"),
                ("evidence_requirement_count", "Evidence needs"),
                ("blocking_gap_count", "Graph blockers"),
            ),
        }[section_id]
        return [
            {
                "id": field,
                "label": label,
                "value": summary.get(field, 0),
            }
            for field, label in metric_fields
        ]

    def _section_preview(self, section_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return []
        if section_id == "matter_intake":
            return [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "status": item["status"],
                    "missing_count": len(item.get("missing_fields") or []),
                    "blocks": bool(item.get("blocks_matter_creation")),
                }
                for item in payload.get("checks", [])
            ]
        if section_id == "deadline_validation":
            return [
                {
                    "id": item["deadline_id"],
                    "type": item["deadline_type"],
                    "status": item["risk_band"],
                    "days_until_due": item.get("days_until_due"),
                    "requires_lawyer_review": item.get("requires_lawyer_review"),
                }
                for item in payload.get("checks", [])
            ]
        if section_id == "timeline_risk":
            return [
                {
                    "id": item["event_id"],
                    "type": item["risk_type"],
                    "severity": item["severity"],
                    "blocking": item["blocking"],
                }
                for item in payload.get("risk_flags", [])
            ]
        if section_id == "task_notifications":
            return [
                {
                    "id": item["task_id"],
                    "status": item["status"],
                    "priority": item["priority"],
                    "triggers": item.get("triggers", []),
                    "owner_missing": item.get("owner_missing", False),
                }
                for item in payload.get("evaluated_tasks", [])
            ]
        if section_id == "evidence_graph":
            return [
                {
                    "id": item["id"],
                    "severity": item["severity"],
                    "target": item["target"],
                }
                for item in payload.get("gap_flags", [])
            ]
        return []

    def _build_blockers(self, source_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        blockers.extend(self._matter_blockers(source_payloads["matter_intake"]))
        blockers.extend(self._deadline_blockers(source_payloads["deadline_validation"]))
        blockers.extend(self._timeline_blockers(source_payloads["timeline_risk"]))
        blockers.extend(self._task_blockers(source_payloads["task_notifications"]))
        blockers.extend(self._evidence_blockers(source_payloads["evidence_graph"]))
        return self._dedupe_items(blockers)

    def _matter_blockers(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return []
        blockers = []
        for check in payload.get("checks", []):
            if check.get("status") != "fail":
                continue
            blockers.append(
                self._blocker(
                    section_id="matter_intake",
                    item_id=check["id"],
                    title=check["title"],
                    reason=self._reason_from_check(check),
                    required_action=check.get("recommended_action")
                    or "Resolve intake readiness before creating or advancing the matter.",
                    severity="blocking",
                )
            )
        return blockers

    def _deadline_blockers(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return []
        blockers = []
        for check in payload.get("checks", []):
            if check.get("risk_band") not in {"overdue", "urgent", "missing_date"}:
                continue
            blockers.append(
                self._blocker(
                    section_id="deadline_validation",
                    item_id=str(check.get("deadline_id") or "deadline"),
                    title=f"Deadline requires review: {check.get('deadline_type') or 'general_deadline'}",
                    reason=self._first_text(check.get("reasons"))
                    or "Deadline metadata requires verification before reminders or client delivery.",
                    required_action=", ".join(check.get("recommended_action_ids") or ["lawyer-date-review"]),
                    severity="blocking",
                )
            )
        return blockers

    def _timeline_blockers(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return []
        return [
            self._blocker(
                section_id="timeline_risk",
                item_id=str(item.get("event_id") or "event"),
                title=f"Urgent timeline item: {item.get('event_type') or 'deadline_event'}",
                reason=str(item.get("reason") or "Timeline risk is inside the urgent window."),
                required_action=str(item.get("required_owner_action") or "Create same-day lawyer review task."),
                severity="blocking",
            )
            for item in payload.get("blocking_urgent_items", [])
        ]

    def _task_blockers(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return []
        blockers = []
        for task in payload.get("blocking_urgent_tasks", []):
            reasons = task.get("blocking_reasons") or task.get("triggers") or ["task_requires_attention"]
            blockers.append(
                self._blocker(
                    section_id="task_notifications",
                    item_id=str(task.get("task_id") or "task"),
                    title="Task notification blocker",
                    reason=", ".join(str(reason) for reason in reasons),
                    required_action="Assign an accountable owner or escalate the urgent task before dispatch.",
                    severity="blocking",
                )
            )
        return blockers

    def _evidence_blockers(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return []
        blockers = []
        for flag in payload.get("gap_flags", []):
            if flag.get("severity") != "blocking":
                continue
            blockers.append(
                self._blocker(
                    section_id="evidence_graph",
                    item_id=str(flag.get("id") or "graph-gap"),
                    title="Evidence graph gap",
                    reason=str(flag.get("message") or "Evidence graph has a blocking gap."),
                    required_action="Resolve the graph gap before relying on high-risk conclusions.",
                    severity="blocking",
                )
            )
        return blockers

    def _blocker(
        self,
        *,
        section_id: str,
        item_id: str,
        title: str,
        reason: str,
        required_action: str,
        severity: str,
    ) -> dict[str, Any]:
        return {
            "id": f"{section_id}:{item_id}",
            "source_section": section_id,
            "source": SECTION_SOURCES[section_id],
            "severity": severity,
            "title": title,
            "reason": reason,
            "required_action": required_action,
        }

    def _build_next_actions(
        self,
        source_payloads: dict[str, dict[str, Any]],
        blockers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        actions.extend(self._matter_actions(source_payloads["matter_intake"]))
        actions.extend(self._deadline_actions(source_payloads["deadline_validation"]))
        actions.extend(self._timeline_actions(source_payloads["timeline_risk"]))
        actions.extend(self._task_actions(source_payloads["task_notifications"]))
        actions.extend(self._evidence_actions(source_payloads["evidence_graph"]))
        if not actions and not blockers:
            actions.append(
                self._action(
                    section_id="matter_intake",
                    item_id="monitor",
                    priority="low",
                    owner="case_team",
                    action="Keep monitoring the workbench sections as new case metadata arrives.",
                )
            )
        return self._dedupe_items(actions)

    def _matter_actions(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return [self._supply_action("matter_intake", "case_operator")]
        actions = []
        for check in payload.get("checks", []):
            if check.get("status") not in {"fail", "warn"}:
                continue
            actions.append(
                self._action(
                    section_id="matter_intake",
                    item_id=check["id"],
                    priority="critical" if check["status"] == "fail" else "high",
                    owner="case_operator",
                    action=check.get("recommended_action") or "Resolve the intake review item.",
                )
            )
        if not actions:
            for index, action in enumerate(payload.get("recommended_actions", [])[:2], start=1):
                actions.append(
                    self._action(
                        section_id="matter_intake",
                        item_id=f"ready-{index}",
                        priority="low",
                        owner="case_team",
                        action=str(action),
                    )
                )
        return actions

    def _deadline_actions(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return [self._supply_action("deadline_validation", "case_operator")]
        actions = []
        for check in payload.get("checks", []):
            priority = self._deadline_priority(str(check.get("risk_band") or "clear"))
            for action_id in check.get("recommended_action_ids", []):
                if priority == "low" and action_id == "standard-calendar-monitoring":
                    continue
                actions.append(
                    self._action(
                        section_id="deadline_validation",
                        item_id=f"{check.get('deadline_id')}:{action_id}",
                        priority=priority,
                        owner=self._deadline_owner(action_id),
                        action=self._deadline_action_label(action_id),
                    )
                )
        return actions

    def _timeline_actions(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return [self._supply_action("timeline_risk", "case_operator")]
        priority = "critical" if (payload.get("summary") or {}).get("blocking_urgent_count") else "medium"
        return [
            self._action(
                section_id="timeline_risk",
                item_id=f"action-{index}",
                priority=priority,
                owner="case_owner",
                action=str(action),
            )
            for index, action in enumerate(payload.get("next_actions", [])[:5], start=1)
        ]

    def _task_actions(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return [self._supply_action("task_notifications", "case_owner")]
        actions = []
        for task in payload.get("blocking_urgent_tasks", []):
            actions.append(
                self._action(
                    section_id="task_notifications",
                    item_id=f"{task.get('task_id')}:blocker",
                    priority="critical",
                    owner="case_owner",
                    action="Assign or escalate the blocked urgent task before dispatch.",
                )
            )
        for task in payload.get("notification_queue", []):
            actions.append(
                self._action(
                    section_id="task_notifications",
                    item_id=f"{task.get('task_id')}:notify",
                    priority="high" if task.get("urgent_escalation") else "medium",
                    owner="task_owner",
                    action="Queue the task reminder through the recommended channels.",
                )
            )
        return actions

    def _evidence_actions(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if payload.get("_input_state") == "not_supplied":
            return [self._supply_action("evidence_graph", "legal_reviewer")]
        actions = []
        for flag in payload.get("gap_flags", []):
            actions.append(
                self._action(
                    section_id="evidence_graph",
                    item_id=str(flag.get("id") or "gap"),
                    priority="critical" if flag.get("severity") == "blocking" else "medium",
                    owner="legal_reviewer",
                    action=str(flag.get("message") or "Review evidence graph gap."),
                )
            )
        return actions

    def _supply_action(self, section_id: str, owner: str) -> dict[str, Any]:
        return self._action(
            section_id=section_id,
            item_id="supply-metadata",
            priority="info",
            owner=owner,
            action=f"Supply {section_id.replace('_', ' ')} metadata to populate this workbench section.",
        )

    def _action(
        self,
        *,
        section_id: str,
        item_id: str,
        priority: str,
        owner: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            "id": f"{section_id}:{item_id}",
            "source_section": section_id,
            "priority": priority,
            "owner": owner,
            "action": action,
        }

    def _deadline_priority(self, risk_band: str) -> str:
        if risk_band in {"overdue", "urgent", "missing_date"}:
            return "critical"
        if risk_band in {"near", "watch"}:
            return "medium"
        return "low"

    def _deadline_owner(self, action_id: str) -> str:
        if action_id in {"lawyer-date-review", "preservation-review"}:
            return "responsible_lawyer"
        if action_id in {"same-day-escalation", "same-day-reminder"}:
            return "case_owner"
        return "case_operator"

    def _deadline_action_label(self, action_id: str) -> str:
        labels = {
            "collect-controlling-date": "Collect and normalize the controlling date.",
            "lawyer-date-review": "Route the date calculation to lawyer review.",
            "same-day-escalation": "Create a same-day escalation record.",
            "same-day-reminder": "Create a same-day deadline reminder.",
            "preservation-review": "Review preservation or remedial options.",
            "case-team-reminder": "Notify the case team before the due window closes.",
            "timeline-watch-checkpoint": "Schedule a timeline watch checkpoint.",
            "derive-dependent-deadlines": "Derive dependent deadlines from the verified service date.",
        }
        return labels.get(action_id, action_id.replace("-", " "))

    def _build_dashboard(
        self,
        sections: list[dict[str, Any]],
        blockers: list[dict[str, Any]],
        next_actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        evaluated_sections = [section for section in sections if section["input_state"] == "evaluated"]
        if not evaluated_sections:
            status = "template"
        elif blockers:
            status = "blocked"
        elif any(section["status"] == "needs_attention" for section in sections):
            status = "needs_attention"
        else:
            status = "ready"

        return {
            "status": status,
            "deterministic": True,
            "section_count": len(sections),
            "evaluated_section_count": len(evaluated_sections),
            "blocker_count": len(blockers),
            "next_action_count": len(next_actions),
            "critical_action_count": sum(1 for item in next_actions if item["priority"] == "critical"),
            "cards": [
                {
                    "section_id": section["id"],
                    "title": section["title"],
                    "status": section["status"],
                    "severity": section["severity"],
                    "primary_metric": section["metrics"][0] if section["metrics"] else None,
                }
                for section in sections
            ],
            "primary_blocker": blockers[0] if blockers else None,
            "primary_next_action": next_actions[0] if next_actions else None,
        }

    def _source_contracts(self, source_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        contracts = []
        for section_id in SECTION_ORDER:
            payload = source_payloads[section_id]
            contracts.append(
                {
                    "section_id": section_id,
                    "source": SECTION_SOURCES[section_id],
                    "input_state": payload.get("_input_state", "evaluated"),
                    "status": str(payload.get("status") or "unknown"),
                    "validation_commands": self._commands_from_payload(payload),
                }
            )
        return contracts

    def _commands_from_payload(self, payload: dict[str, Any]) -> list[str]:
        commands: list[str] = []
        for field in ("validation_commands", "low_resource_validation_commands"):
            value = payload.get(field)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        commands.append(item)
                    elif isinstance(item, dict) and item.get("command"):
                        commands.append(str(item["command"]))
        return list(dict.fromkeys(commands))

    def _reason_from_check(self, check: dict[str, Any]) -> str:
        missing_fields = check.get("missing_fields") or []
        if missing_fields:
            return "Missing fields: " + ", ".join(str(field) for field in missing_fields)
        return self._first_text(check.get("observations")) or "Readiness check failed."

    def _first_text(self, value: Any) -> str:
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
        if isinstance(value, str):
            return value.strip()
        return ""

    def _sort_blockers(self, blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        order = {section_id: index for index, section_id in enumerate(SECTION_ORDER)}
        return sorted(blockers, key=lambda item: (order.get(item["source_section"], 99), item["id"]))

    def _sort_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        order = {section_id: index for index, section_id in enumerate(SECTION_ORDER)}
        return sorted(
            actions,
            key=lambda item: (
                ACTION_PRIORITY_RANK.get(item["priority"], 99),
                order.get(item["source_section"], 99),
                item["id"],
            ),
        )

    def _dedupe_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for item in items:
            item_id = str(item.get("id") or "")
            if item_id in seen:
                continue
            seen.add(item_id)
            deduped.append(item)
        return deduped

    def _safe_identifier(self, value: Any, *, fallback: str) -> str:
        raw = str(value or "").strip()
        if not raw or SENSITIVE_TEXT_PATTERN.search(raw):
            return fallback
        return raw[:80]

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._sanitize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        if isinstance(value, tuple):
            return [self._sanitize(item) for item in value]
        if isinstance(value, str):
            return SENSITIVE_TEXT_PATTERN.sub("[redacted]", value)
        return value
