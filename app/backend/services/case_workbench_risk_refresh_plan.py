from __future__ import annotations

from collections.abc import Mapping
from typing import Any


RISK_REFRESH_PLAN_ID = "case-workbench-risk-refresh-plan"
RISK_RELEVANT_SECTIONS = ("facts", "deadlines", "evidence_graph", "tasks", "parties")
RISK_REFRESH_FIELDS = {
    "status",
    "priority",
    "review_required",
    "escalation_status",
    "blocker_codes",
    "deadline_ref_hash",
    "due_at",
    "urgency",
    "days_until_due_bucket",
    "fact_ref_hash",
    "materiality",
    "dispute_status",
    "confidence_level",
    "source_evidence_refs",
    "legal_issue_codes",
    "risk_refs",
    "node_count",
    "edge_count",
    "gap_count",
    "blocking_gap_count",
    "warning_gap_count",
}


class CaseWorkbenchRiskRefreshPlanService:
    """Build metadata-only risk/evidence refresh plans from runtime state."""

    def build_plan(
        self,
        payload: Mapping[str, Any] | None = None,
        recent_events: list[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        data = payload if isinstance(payload, Mapping) else {}
        sections = data.get("sections") if isinstance(data.get("sections"), Mapping) else {}
        events = [event for event in recent_events or [] if isinstance(event, Mapping)]
        section_rows = [self._section_row(section, sections.get(section)) for section in RISK_RELEVANT_SECTIONS]
        trigger_rows = [self._trigger_row(event) for event in events]
        refresh_rows = [row for row in section_rows if row["refresh_required"]]
        risk_triggers = [row for row in trigger_rows if row["requires_risk_state_refresh"]]
        graph_triggers = [row for row in trigger_rows if row["requires_evidence_graph_refresh"]]
        blocking_rows = [
            row
            for row in section_rows
            if row["blocking_gap_count"] > 0 or row["blocked_count"] > 0 or row["urgent_count"] > 0
        ]
        review_rows = [row for row in section_rows if row["review_required_count"] > 0]
        risk_state_badges = self._risk_state_badges(section_rows, trigger_rows)

        return {
            "id": RISK_REFRESH_PLAN_ID,
            "status": self._status(section_rows, trigger_rows, blocking_rows, review_rows),
            "method": {
                "type": RISK_REFRESH_PLAN_ID,
                "notes": [
                    "Converts sanitized case-workbench section state and recent event metadata into a risk/evidence refresh plan.",
                    "Flags facts, deadlines, evidence graph, tasks, and party-state deltas that should refresh live risk state.",
                    "Returns metadata only: section ids, counts, event ids, field names, and reason codes.",
                ],
            },
            "summary": {
                "section_count": len(section_rows),
                "populated_section_count": sum(1 for row in section_rows if row["status"] != "empty"),
                "refresh_required_count": len(refresh_rows),
                "blocking_section_count": len(blocking_rows),
                "review_section_count": len(review_rows),
                "recent_event_count": len(trigger_rows),
                "risk_affecting_event_count": len(risk_triggers),
                "evidence_graph_affecting_event_count": len(graph_triggers),
                "task_active_count": self._sum_summary(section_rows, "active_count"),
                "task_blocked_count": self._sum_summary(section_rows, "blocked_count"),
                "deadline_urgent_count": self._sum_summary(section_rows, "urgent_count"),
                "evidence_graph_blocking_gap_count": self._sum_summary(section_rows, "blocking_gap_count"),
                "review_required_count": self._sum_summary(section_rows, "review_required_count"),
                "risk_state_badge_count": len(risk_state_badges),
                "critical_badge_count": sum(1 for badge in risk_state_badges if badge["severity"] == "critical"),
                "warning_badge_count": sum(1 for badge in risk_state_badges if badge["severity"] == "warning"),
                "raw_text_returned": False,
                "event_payloads_returned": False,
                "risk_state_written": False,
                "evidence_graph_written": False,
                "notification_sent": False,
            },
            "section_refresh_rows": section_rows,
            "event_trigger_rows": trigger_rows,
            "refresh_required_section_ids": [row["section"] for row in refresh_rows],
            "risk_affecting_event_ids": [row["event_id"] for row in risk_triggers],
            "evidence_graph_affecting_event_ids": [row["event_id"] for row in graph_triggers],
            "blocking_section_ids": [row["section"] for row in blocking_rows],
            "review_section_ids": [row["section"] for row in review_rows],
            "evidence_graph_plan": self._evidence_graph_plan(section_rows, graph_triggers),
            "risk_state_badges": risk_state_badges,
            "risk_state_badge_summary": self._risk_state_badge_summary(risk_state_badges),
            "recommended_actions": self._recommended_actions(refresh_rows, blocking_rows, review_rows, graph_triggers),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_section_ids": True,
                "returns_event_ids": True,
                "returns_changed_field_names": True,
                "returns_risk_state_badges": True,
                "returns_raw_event_payload": False,
                "returns_raw_fact_text": False,
                "returns_raw_evidence_text": False,
                "returns_party_names": False,
                "returns_client_contact_details": False,
                "returns_document_text": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "writes_risk_state": False,
                "writes_evidence_graph": False,
                "sends_notifications": False,
            },
            "claim_boundary": {
                "live_risk_state_updated": False,
                "evidence_graph_refreshed": False,
                "lawyer_review_completed": False,
                "client_notification_sent": False,
                "legal_advice_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_case_workbench_risk_refresh_plan.py tests/test_case_workbench_runtime_binding.py tests/test_case_workbench_runtime_router.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _section_row(self, section: str, value: Any) -> dict[str, Any]:
        state = value if isinstance(value, Mapping) else {}
        status = str(state.get("status") or "empty")
        summary = state.get("summary") if isinstance(state.get("summary"), Mapping) else {}
        collection_counts = state.get("collection_counts") if isinstance(state.get("collection_counts"), Mapping) else {}
        state_data = state.get("state") if isinstance(state.get("state"), Mapping) else {}
        reason_codes = self._section_reason_codes(section, status, summary)
        refresh_required = status != "empty" and bool(reason_codes)
        return {
            "section": section,
            "status": status,
            "state_version": self._safe_int(state.get("state_version")),
            "latest_event_id": state.get("latest_event_id"),
            "validation_status": state.get("validation_status"),
            "collection_counts": {
                str(key): self._safe_int(value)
                for key, value in collection_counts.items()
                if isinstance(key, str)
            },
            "summary": {
                key: self._safe_int(summary.get(key))
                for key in (
                    "active_count",
                    "blocked_count",
                    "completed_count",
                    "review_required_count",
                    "urgent_count",
                    "overdue_count",
                    "blocking_gap_count",
                    "warning_gap_count",
                    "gap_count",
                    "node_count",
                    "edge_count",
                )
                if key in summary
            },
            "item_count": self._safe_int(state_data.get("item_count") or summary.get("item_count")),
            "active_count": self._safe_int(summary.get("active_count")),
            "blocked_count": self._blocked_count(section, summary, state_data),
            "urgent_count": self._safe_int(summary.get("urgent_count") or summary.get("overdue_count")),
            "blocking_gap_count": self._safe_int(summary.get("blocking_gap_count")),
            "review_required_count": self._safe_int(summary.get("review_required_count")),
            "refresh_required": refresh_required,
            "refresh_targets": self._refresh_targets(section, reason_codes),
            "reason_codes": reason_codes,
            "raw_content_returned": False,
        }

    def _trigger_row(self, event: Mapping[str, Any]) -> dict[str, Any]:
        event_json = event.get("event_json") if isinstance(event.get("event_json"), Mapping) else {}
        section = str(event.get("section") or event_json.get("section") or "unknown")
        changed_fields = [
            str(field)
            for field in event_json.get("changed_field_names", [])
            if isinstance(field, str) and field.strip()
        ][:20]
        risk_fields = sorted({field for field in changed_fields if field in RISK_REFRESH_FIELDS})
        requires_risk = section in RISK_RELEVANT_SECTIONS and bool(risk_fields or section == "evidence_graph")
        requires_graph = section in {"facts", "evidence_graph", "deadlines"} or bool(
            {"source_evidence_refs", "risk_refs", "deadline_refs"}.intersection(changed_fields)
        )
        reason_codes = []
        if requires_risk:
            reason_codes.append("runtime-event-affects-risk-state")
        if requires_graph:
            reason_codes.append("runtime-event-affects-evidence-graph")
        if event.get("validation_status") not in {"pass", "warn"}:
            reason_codes.append("event-validation-not-pass")
        return {
            "event_id": str(event.get("event_id") or "unknown-event"),
            "section": section,
            "operation": str(event.get("operation") or event_json.get("operation") or "unknown"),
            "state_version": self._safe_int(event.get("state_version") or event_json.get("state_version")),
            "validation_status": str(event.get("validation_status") or event_json.get("validation_status") or "unknown"),
            "changed_item_count": len(
                [item for item in event_json.get("changed_item_refs", []) if isinstance(item, str)]
            ),
            "changed_field_names": risk_fields,
            "requires_risk_state_refresh": requires_risk,
            "requires_evidence_graph_refresh": requires_graph,
            "raw_event_payload_returned": False,
            "reason_codes": reason_codes or ["runtime-event-does-not-affect-risk-refresh"],
        }

    def _section_reason_codes(self, section: str, status: str, summary: Mapping[str, Any]) -> list[str]:
        if status == "empty":
            return []
        codes: list[str] = []
        if section == "tasks":
            if self._safe_int(summary.get("active_count")):
                codes.append("active-task-state")
            if self._safe_int(summary.get("review_required_count")):
                codes.append("lawyer-review-required")
        if section == "deadlines":
            if self._safe_int(summary.get("urgent_count") or summary.get("overdue_count")):
                codes.append("urgent-deadline-state")
        if section == "evidence_graph":
            if self._safe_int(summary.get("blocking_gap_count")):
                codes.append("blocking-evidence-gap")
            elif self._safe_int(summary.get("gap_count") or summary.get("warning_gap_count")):
                codes.append("evidence-graph-gap-review")
            else:
                codes.append("evidence-graph-ready-for-risk-sync")
        if section == "facts":
            if self._safe_int(summary.get("fact_count") or summary.get("review_required_count")):
                codes.append("fact-state-affects-risk")
        if section == "parties":
            if self._safe_int(summary.get("review_required_count")):
                codes.append("party-review-affects-risk")
        return codes

    def _refresh_targets(self, section: str, reason_codes: list[str]) -> list[str]:
        targets = set()
        if reason_codes:
            targets.add("risk_state")
        if section in {"facts", "deadlines", "evidence_graph"} or any("evidence" in code for code in reason_codes):
            targets.add("evidence_graph")
        if any(code in reason_codes for code in ("active-task-state", "lawyer-review-required", "urgent-deadline-state")):
            targets.add("review_queue")
        return sorted(targets)

    def _blocked_count(self, section: str, summary: Mapping[str, Any], state_data: Mapping[str, Any]) -> int:
        if "blocked_count" in summary:
            return self._safe_int(summary.get("blocked_count"))
        if section != "tasks":
            return 0
        task_states = state_data.get("task_states")
        if not isinstance(task_states, list):
            return 0
        return sum(1 for item in task_states if isinstance(item, Mapping) and item.get("status") == "blocked")

    def _evidence_graph_plan(self, section_rows: list[dict[str, Any]], graph_triggers: list[dict[str, Any]]) -> dict[str, Any]:
        evidence_graph = next((row for row in section_rows if row["section"] == "evidence_graph"), None)
        needs_refresh = bool(graph_triggers) or bool(evidence_graph and evidence_graph["refresh_required"])
        return {
            "status": "refresh_required" if needs_refresh else "watch",
            "required_before_client_delivery": needs_refresh,
            "source_sections": [
                row["section"]
                for row in section_rows
                if "evidence_graph" in row["refresh_targets"] or row["section"] == "evidence_graph"
            ],
            "blocking_gap_count": evidence_graph["blocking_gap_count"] if evidence_graph else 0,
            "trigger_event_count": len(graph_triggers),
            "writes_graph": False,
            "action": (
                "Refresh evidence graph and risk state outside this metadata service before client delivery."
                if needs_refresh
                else "Keep watching runtime events; no evidence graph write is performed here."
            ),
        }

    def _risk_state_badges(
        self,
        section_rows: list[dict[str, Any]],
        trigger_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows = {row["section"]: row for row in section_rows}
        badges: list[dict[str, Any]] = []

        tasks = rows.get("tasks", {})
        blocked_tasks = self._safe_int(tasks.get("blocked_count"))
        review_tasks = self._safe_int(tasks.get("review_required_count"))
        active_tasks = self._safe_int(tasks.get("active_count"))
        if blocked_tasks:
            badges.append(
                self._badge(
                    "blocked-task-review",
                    "Blocked task review",
                    "critical",
                    "tasks",
                    blocked_tasks,
                    ("blocked-task-state", "lawyer-review-required"),
                    "Resolve blocked task dependencies before delivery.",
                )
            )
        elif review_tasks or active_tasks:
            badges.append(
                self._badge(
                    "active-lawyer-review",
                    "Active lawyer review",
                    "warning",
                    "tasks",
                    max(review_tasks, active_tasks),
                    ("active-task-state",),
                    "Complete or reassign active lawyer review tasks.",
                )
            )

        deadlines = rows.get("deadlines", {})
        urgent_deadlines = self._safe_int(deadlines.get("urgent_count"))
        if urgent_deadlines:
            badges.append(
                self._badge(
                    "urgent-deadline-risk",
                    "Urgent deadline risk",
                    "critical",
                    "deadlines",
                    urgent_deadlines,
                    ("urgent-deadline-state",),
                    "Review urgent or overdue deadlines before client delivery.",
                )
            )

        evidence_graph = rows.get("evidence_graph", {})
        blocking_gaps = self._safe_int(evidence_graph.get("blocking_gap_count"))
        warning_gaps = self._safe_int(evidence_graph.get("summary", {}).get("gap_count")) or self._safe_int(
            evidence_graph.get("summary", {}).get("warning_gap_count")
        )
        if blocking_gaps:
            badges.append(
                self._badge(
                    "blocking-evidence-gap",
                    "Blocking evidence gap",
                    "critical",
                    "evidence_graph",
                    blocking_gaps,
                    ("blocking-evidence-gap",),
                    "Link required evidence before relying on risk conclusions.",
                )
            )
        elif warning_gaps:
            badges.append(
                self._badge(
                    "evidence-gap-review",
                    "Evidence gap review",
                    "warning",
                    "evidence_graph",
                    warning_gaps,
                    ("evidence-graph-gap-review",),
                    "Review evidence graph gaps and decide whether they block delivery.",
                )
            )

        risk_events = [row for row in trigger_rows if row["requires_risk_state_refresh"]]
        if risk_events:
            badges.append(
                self._badge(
                    "runtime-event-risk-refresh",
                    "Runtime event risk refresh",
                    "warning",
                    "runtime_events",
                    len(risk_events),
                    ("runtime-event-affects-risk-state",),
                    "Recompute visible risk badges from recent runtime event deltas.",
                )
            )

        if badges:
            return badges
        if any(row["status"] != "empty" for row in section_rows):
            return [
                self._badge(
                    "risk-state-watch",
                    "Risk state watch",
                    "ready",
                    "workbench",
                    0,
                    ("risk-state-no-blocking-badges",),
                    "No blocking risk badge is projected from current metadata.",
                )
            ]
        return [
            self._badge(
                "risk-state-empty",
                "Risk state empty",
                "watch",
                "workbench",
                0,
                ("risk-state-metadata-empty",),
                "Collect workbench section events before projecting risk badges.",
            )
        ]

    def _badge(
        self,
        badge_id: str,
        label: str,
        severity: str,
        source: str,
        count: int,
        reason_codes: tuple[str, ...],
        action: str,
    ) -> dict[str, Any]:
        return {
            "id": badge_id,
            "label": label,
            "severity": severity,
            "source": source,
            "count": self._safe_int(count),
            "reason_codes": list(reason_codes),
            "action": action,
            "writes_risk_state": False,
            "writes_evidence_graph": False,
            "raw_content_returned": False,
        }

    def _risk_state_badge_summary(self, badges: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "badge_count": len(badges),
            "critical_count": sum(1 for badge in badges if badge["severity"] == "critical"),
            "warning_count": sum(1 for badge in badges if badge["severity"] == "warning"),
            "ready_count": sum(1 for badge in badges if badge["severity"] == "ready"),
            "watch_count": sum(1 for badge in badges if badge["severity"] == "watch"),
            "writes_risk_state": False,
            "writes_evidence_graph": False,
            "raw_content_returned": False,
        }

    def _recommended_actions(
        self,
        refresh_rows: list[dict[str, Any]],
        blocking_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        graph_triggers: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if blocking_rows:
            actions.append("Review blocking task, deadline, or evidence graph gaps before marking the matter delivery-ready.")
        if review_rows:
            actions.append("Queue lawyer review for sections with review_required_count above zero.")
        if graph_triggers:
            actions.append("Refresh evidence graph links after fact, deadline, or evidence_graph runtime events.")
        if refresh_rows:
            actions.append("Recompute live risk-state badges from the listed section ids outside this metadata service.")
        return actions or ["No runtime risk refresh is required yet; continue collecting metadata-only workbench events."]

    def _status(
        self,
        section_rows: list[dict[str, Any]],
        trigger_rows: list[dict[str, Any]],
        blocking_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
    ) -> str:
        if not any(row["status"] != "empty" for row in section_rows) and not trigger_rows:
            return "empty"
        if blocking_rows:
            return "blocked"
        if any(row["requires_risk_state_refresh"] or row["requires_evidence_graph_refresh"] for row in trigger_rows):
            return "refresh_required"
        if review_rows:
            return "review_required"
        return "watch"

    def _sum_summary(self, rows: list[dict[str, Any]], key: str) -> int:
        return sum(self._safe_int(row.get(key) or row.get("summary", {}).get(key)) for row in rows)

    def _safe_int(self, value: Any) -> int:
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, float):
            return max(0, int(value))
        return 0
