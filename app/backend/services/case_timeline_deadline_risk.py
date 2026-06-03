from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


SENSITIVE_TEXT_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CaseTimelineEventType:
    event_type: str
    display_name: str
    purpose: str
    required_fields: tuple[str, ...]
    deadline_family: str
    default_risk_tags: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeadlineRuleMetadata:
    rule_id: str
    applies_to_event_types: tuple[str, ...]
    trigger: str
    severity: str
    blocking: bool
    deterministic_input: str
    recommended_action: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class CaseTimelineDeadlineRiskService:
    """Build deterministic deadline risk metadata for a case workspace timeline."""

    DATE_FIELDS = ("key_date", "deadline_date", "event_date")
    URGENT_URGENCIES = {"urgent", "critical", "blocking", "overdue", "immediate"}
    MISSING_FACT_URGENCIES = {"missing_fact", "missing-date", "unknown", "needs_fact"}
    EVENT_TYPE_ALIASES = {
        "answer": "answer_deadline",
        "answer_due": "answer_deadline",
        "defense_deadline": "answer_deadline",
        "evidence_due": "evidence_deadline",
        "proof_deadline": "evidence_deadline",
        "statute_limit": "limitation_period_deadline",
        "limitation_deadline": "limitation_period_deadline",
        "performance_due": "performance_deadline",
        "payment_due": "performance_deadline",
        "appeal_due": "appeal_deadline",
        "enforcement_due": "enforcement_deadline",
        "served": "service_received",
    }

    def build_assessment(self, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        event_types = self._event_type_standards()
        deadline_rules = self._deadline_rules()
        event_type_index = {item.event_type: item for item in event_types}

        if not events:
            return {
                "status": "template",
                "assessment_id": "case-timeline-deadline-risk-v1",
                "method": self._method_notes(),
                "summary": {
                    "assessed_event_count": 0,
                    "risk_flag_count": 0,
                    "blocking_urgent_count": 0,
                    "missing_fact_count": 0,
                    "deterministic": True,
                },
                "event_type_standards": [item.to_api() for item in event_types],
                "deadline_rules_metadata": [item.to_api() for item in deadline_rules],
                "event_template": self._event_template(),
                "risk_flags": [],
                "blocking_urgent_items": [],
                "next_actions": self._template_next_actions(),
                "validation_commands": self._validation_commands(),
                "privacy_note": self._privacy_note(),
            }

        normalized_events: list[dict[str, Any]] = []
        risk_flags: list[dict[str, Any]] = []
        blocking_urgent_items: list[dict[str, Any]] = []

        for index, raw_event in enumerate(events, start=1):
            normalized_event = self._normalize_event(raw_event, index)
            normalized_events.append(normalized_event)

            event_risks = self._risk_flags_for_event(normalized_event, event_type_index)
            risk_flags.extend(event_risks)

            for risk in event_risks:
                if risk["blocking"] and risk["severity"] == "urgent":
                    blocking_urgent_items.append(
                        {
                            "event_id": normalized_event["event_id"],
                            "event_type": normalized_event["event_type"],
                            "reason": risk["reason"],
                            "required_owner_action": risk["owner_action"],
                        }
                    )

        missing_fact_count = sum(1 for item in risk_flags if item["risk_type"] == "missing_fact")
        return {
            "status": "ready",
            "assessment_id": "case-timeline-deadline-risk-v1",
            "method": self._method_notes(),
            "summary": {
                "assessed_event_count": len(normalized_events),
                "risk_flag_count": len(risk_flags),
                "blocking_urgent_count": len(blocking_urgent_items),
                "missing_fact_count": missing_fact_count,
                "deterministic": True,
            },
            "event_type_standards": [item.to_api() for item in event_types],
            "deadline_rules_metadata": [item.to_api() for item in deadline_rules],
            "normalized_events": normalized_events,
            "risk_flags": risk_flags,
            "blocking_urgent_items": blocking_urgent_items,
            "next_actions": self._next_actions(risk_flags, blocking_urgent_items),
            "validation_commands": self._validation_commands(),
            "privacy_note": self._privacy_note(),
        }

    def _normalize_event(self, event: dict[str, Any], index: int) -> dict[str, Any]:
        raw_event_type = str(event.get("event_type") or event.get("type") or "unknown").strip().lower()
        event_type = self.EVENT_TYPE_ALIASES.get(raw_event_type, raw_event_type)
        days_until_deadline = self._coerce_days(event.get("days_until_deadline"))

        return {
            "event_id": self._safe_text(event.get("event_id") or event.get("id") or f"event-{index}"),
            "event_type": event_type or "unknown",
            "title": self._safe_text(event.get("title") or event_type or f"Timeline event {index}"),
            "key_date_present": self._has_key_date(event),
            "days_until_deadline": days_until_deadline,
            "urgency": self._safe_text(event.get("urgency") or "normal").lower(),
            "source": self._safe_text(event.get("source") or "manual_or_imported_case_timeline"),
            "jurisdiction": self._safe_text(event.get("jurisdiction") or "unspecified"),
        }

    def _risk_flags_for_event(
        self,
        event: dict[str, Any],
        event_type_index: dict[str, CaseTimelineEventType],
    ) -> list[dict[str, Any]]:
        risk_flags: list[dict[str, Any]] = []
        event_type = event["event_type"]
        urgency = event["urgency"]
        days_until_deadline = event["days_until_deadline"]
        known_event_type = event_type in event_type_index

        if not known_event_type:
            risk_flags.append(
                self._risk_flag(
                    event,
                    risk_type="missing_fact",
                    severity="missing_fact",
                    blocking=False,
                    reason="Timeline event type is not mapped to a known deadline rule.",
                    owner_action="Classify the event using a supported event_type before relying on risk output.",
                )
            )

        if not event["key_date_present"]:
            risk_flags.append(
                self._risk_flag(
                    event,
                    risk_type="missing_fact",
                    severity="missing_fact",
                    blocking=False,
                    reason="A key date, deadline date, or event date is missing.",
                    owner_action="Collect and verify the controlling date from the file or court notice.",
                )
            )

        if urgency in self.MISSING_FACT_URGENCIES:
            risk_flags.append(
                self._risk_flag(
                    event,
                    risk_type="missing_fact",
                    severity="missing_fact",
                    blocking=False,
                    reason="The event was explicitly marked as missing required facts.",
                    owner_action="Request the missing fact before computing final deadline risk.",
                )
            )

        if urgency in self.URGENT_URGENCIES or (days_until_deadline is not None and days_until_deadline <= 3):
            risk_flags.append(
                self._risk_flag(
                    event,
                    risk_type="urgent_deadline",
                    severity="urgent",
                    blocking=True,
                    reason="Deadline is at or within the urgent window, or the event was explicitly marked urgent.",
                    owner_action="Escalate to the responsible lawyer and create a same-day review task.",
                )
            )
        elif days_until_deadline is not None and days_until_deadline <= 7:
            risk_flags.append(
                self._risk_flag(
                    event,
                    risk_type="near_deadline",
                    severity="high",
                    blocking=False,
                    reason="Deadline is within seven days.",
                    owner_action="Confirm owner, documents, and filing or performance plan.",
                )
            )
        elif days_until_deadline is not None and days_until_deadline <= 14:
            risk_flags.append(
                self._risk_flag(
                    event,
                    risk_type="watch_deadline",
                    severity="watch",
                    blocking=False,
                    reason="Deadline is within the watch window.",
                    owner_action="Schedule preparation checkpoint before the final week.",
                )
            )

        return risk_flags

    def _risk_flag(
        self,
        event: dict[str, Any],
        risk_type: str,
        severity: str,
        blocking: bool,
        reason: str,
        owner_action: str,
    ) -> dict[str, Any]:
        return {
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "risk_type": risk_type,
            "severity": severity,
            "blocking": blocking,
            "reason": reason,
            "owner_action": owner_action,
        }

    def _event_type_standards(self) -> list[CaseTimelineEventType]:
        return [
            CaseTimelineEventType(
                event_type="service_received",
                display_name="Service received",
                purpose="Record the date a complaint, arbitration notice, demand, or court document was served.",
                required_fields=("key_date", "source", "served_party"),
                deadline_family="trigger_event",
                default_risk_tags=("answer_deadline", "evidence_deadline"),
            ),
            CaseTimelineEventType(
                event_type="answer_deadline",
                display_name="Answer or defense deadline",
                purpose="Track the last day to answer, defend, object, or submit jurisdictional materials.",
                required_fields=("key_date", "days_until_deadline", "responsible_lawyer"),
                deadline_family="litigation_response",
                default_risk_tags=("urgent_when_days_until_deadline_le_3",),
            ),
            CaseTimelineEventType(
                event_type="evidence_deadline",
                display_name="Evidence or burden deadline",
                purpose="Track evidence exchange, proof submission, supplementation, or court-ordered evidence windows.",
                required_fields=("key_date", "days_until_deadline", "evidence_scope"),
                deadline_family="evidence_submission",
                default_risk_tags=("missing_fact_if_scope_unknown", "urgent_when_days_until_deadline_le_3"),
            ),
            CaseTimelineEventType(
                event_type="limitation_period_deadline",
                display_name="Limitation period deadline",
                purpose="Track statute of limitations, arbitration limitation, or preservation filing cutoff.",
                required_fields=("key_date", "days_until_deadline", "limitation_basis"),
                deadline_family="limitation_period",
                default_risk_tags=("lawyer_review_required", "urgent_when_days_until_deadline_le_3"),
            ),
            CaseTimelineEventType(
                event_type="performance_deadline",
                display_name="Performance or payment deadline",
                purpose="Track contract performance, payment, cure, delivery, or settlement obligation windows.",
                required_fields=("key_date", "days_until_deadline", "obligation_source"),
                deadline_family="contract_or_settlement_obligation",
                default_risk_tags=("client_confirmation_required", "urgent_when_days_until_deadline_le_3"),
            ),
            CaseTimelineEventType(
                event_type="appeal_deadline",
                display_name="Appeal or review deadline",
                purpose="Track appeal filing, reconsideration, retrial application, or administrative review cutoff.",
                required_fields=("key_date", "days_until_deadline", "decision_source"),
                deadline_family="post_decision_review",
                default_risk_tags=("lawyer_review_required", "urgent_when_days_until_deadline_le_3"),
            ),
            CaseTimelineEventType(
                event_type="enforcement_deadline",
                display_name="Enforcement deadline",
                purpose="Track enforcement application, preservation renewal, execution objection, or compliance cutoff.",
                required_fields=("key_date", "days_until_deadline", "enforcement_basis"),
                deadline_family="enforcement_or_compliance",
                default_risk_tags=("asset_or_order_review_required", "urgent_when_days_until_deadline_le_3"),
            ),
            CaseTimelineEventType(
                event_type="hearing",
                display_name="Hearing or meeting",
                purpose="Track hearing, mediation, evidence exchange meeting, or client conference dates.",
                required_fields=("key_date", "location_or_channel", "preparation_owner"),
                deadline_family="preparation_checkpoint",
                default_risk_tags=("preparation_required",),
            ),
        ]

    def _deadline_rules(self) -> list[DeadlineRuleMetadata]:
        return [
            DeadlineRuleMetadata(
                rule_id="urgent-window-le-3-days",
                applies_to_event_types=(
                    "answer_deadline",
                    "evidence_deadline",
                    "limitation_period_deadline",
                    "performance_deadline",
                    "appeal_deadline",
                    "enforcement_deadline",
                ),
                trigger="days_until_deadline <= 3",
                severity="urgent",
                blocking=True,
                deterministic_input="days_until_deadline",
                recommended_action="Block client delivery until a lawyer confirms the deadline plan.",
            ),
            DeadlineRuleMetadata(
                rule_id="explicit-urgent-override",
                applies_to_event_types=("all",),
                trigger="urgency in urgent, critical, blocking, overdue, immediate",
                severity="urgent",
                blocking=True,
                deterministic_input="urgency",
                recommended_action="Escalate regardless of missing or unknown computed date distance.",
            ),
            DeadlineRuleMetadata(
                rule_id="missing-key-date",
                applies_to_event_types=("all",),
                trigger="no key_date, deadline_date, or event_date",
                severity="missing_fact",
                blocking=False,
                deterministic_input="event date fields",
                recommended_action="Request the controlling date before final deadline assessment.",
            ),
            DeadlineRuleMetadata(
                rule_id="near-window-le-7-days",
                applies_to_event_types=("deadline_events",),
                trigger="4 <= days_until_deadline <= 7",
                severity="high",
                blocking=False,
                deterministic_input="days_until_deadline",
                recommended_action="Confirm owner and filing or performance checklist.",
            ),
            DeadlineRuleMetadata(
                rule_id="watch-window-le-14-days",
                applies_to_event_types=("deadline_events",),
                trigger="8 <= days_until_deadline <= 14",
                severity="watch",
                blocking=False,
                deterministic_input="days_until_deadline",
                recommended_action="Schedule preparation checkpoint before the final week.",
            ),
        ]

    def _next_actions(
        self,
        risk_flags: list[dict[str, Any]],
        blocking_urgent_items: list[dict[str, Any]],
    ) -> list[str]:
        actions = []
        if blocking_urgent_items:
            actions.append("Create same-day lawyer review tasks for every blocking urgent item.")
            actions.append("Pause client-facing delivery until urgent deadline ownership is confirmed.")
        if any(item["risk_type"] == "missing_fact" for item in risk_flags):
            actions.append("Request missing controlling dates or event classifications from the case owner.")
        if any(item["risk_type"] in {"near_deadline", "watch_deadline"} for item in risk_flags):
            actions.append("Schedule preparation checkpoints before the final week.")
        if not actions:
            actions.append("No deterministic deadline risk was triggered by the supplied fields.")
        actions.append("Keep the assessment attached to the case audit trail with source document references.")
        return actions

    def _template_next_actions(self) -> list[str]:
        return [
            "Collect service, filing, evidence, limitation, performance, appeal, and enforcement dates.",
            "Provide days_until_deadline or explicit urgency for each deadline event.",
            "Attach source references before showing deadline risk to a client-facing user.",
            "Require lawyer review before treating limitation or appeal deadlines as resolved.",
        ]

    def _event_template(self) -> dict[str, Any]:
        return {
            "event_id": "event-1",
            "event_type": "answer_deadline",
            "title": "Answer deadline",
            "key_date": "YYYY-MM-DD",
            "days_until_deadline": 3,
            "urgency": "normal",
            "source": "court_notice_or_case_file_reference",
            "jurisdiction": "court_or_forum",
        }

    def _method_notes(self) -> dict[str, Any]:
        return {
            "type": "deterministic-case-timeline-deadline-risk-assessment",
            "notes": [
                "The assessment never reads the system date or performs calendar arithmetic.",
                "Risk is derived only from supplied days_until_deadline, explicit urgency, event type, and key date presence.",
                "The service is safe to run on a low-resource machine because it is pure metadata and list processing.",
                "Final legal deadline interpretation still requires lawyer review and source document verification.",
            ],
        }

    def _validation_commands(self) -> list[str]:
        return [
            "python -m pytest tests/test_case_timeline_deadline_risk.py -q",
            "git diff --check -- app/backend/services/case_timeline_deadline_risk.py app/backend/tests/test_case_timeline_deadline_risk.py docs/CASE_TIMELINE_DEADLINE_RISK.md",
        ]

    def _privacy_note(self) -> list[str]:
        return [
            "Do not store raw client identifiers, direct contact details, credentials, or full evidence text in timeline metadata.",
            "Keep source document references, actor IDs, and audit records in controlled case storage.",
            "Only show client-facing deadline summaries after lawyer review and privilege screening.",
        ]

    def _has_key_date(self, event: dict[str, Any]) -> bool:
        return any(bool(event.get(field)) for field in self.DATE_FIELDS)

    def _coerce_days(self, value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("-"):
                return -int(stripped[1:]) if stripped[1:].isdigit() else None
            if stripped.isdigit():
                return int(stripped)
        return None

    def _safe_text(self, value: Any) -> str:
        text = str(value or "").strip()
        redacted = SENSITIVE_TEXT_PATTERN.sub("[redacted]", text)
        return redacted[:160]
