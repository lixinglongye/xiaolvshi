from __future__ import annotations

from typing import Any

from services.feedback_lifecycle_policy import FeedbackLifecyclePolicyService
from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService
from services.feedback_triage import FeedbackTriageService


class FeedbackCapturePlanService:
    """Build a metadata-only feedback intake packet before tickets enter support."""

    def __init__(
        self,
        triage_service: FeedbackTriageService | None = None,
        roadmap_service: FeedbackRoadmapAlignmentService | None = None,
        lifecycle_service: FeedbackLifecyclePolicyService | None = None,
    ) -> None:
        self.triage_service = triage_service or FeedbackTriageService()
        self.roadmap_service = roadmap_service or FeedbackRoadmapAlignmentService()
        self.lifecycle_service = lifecycle_service or FeedbackLifecyclePolicyService()

    def build_plan(self, item: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        source = {**(item or {}), **kwargs}
        triage = self.triage_service.triage(source)
        roadmap_alignment = self.roadmap_service.align(source)
        lifecycle = self.lifecycle_service.evaluate_ticket({**source, "state": source.get("state") or "triage"})
        lifecycle_state = lifecycle.get("current_state") or lifecycle.get("state")
        current_transition_blocking_ids = self._current_transition_blocking_ids(lifecycle)
        top_match = (roadmap_alignment.get("matches") or [{}])[0]
        linked_need_id = roadmap_alignment.get("top_need_id") or top_match.get("need_id")
        release_gate_links = _unique(
            [
                *list(top_match.get("release_gate_links") or []),
                *list(lifecycle.get("linkage", {}).get("release_gate_links") or []),
            ]
        )
        required_fields = self._required_fields(triage)
        missing_fields = [field for field in required_fields if not _text(source.get(field))]
        status = "needs_context" if missing_fields else "ready_to_create"

        return {
            "status": status,
            "capture_summary": {
                "priority": triage["priority"],
                "assignee": triage["assignee"],
                "sla_hours": triage["sla_hours"],
                "linked_need_id": linked_need_id,
                "roadmap_alignment_status": roadmap_alignment.get("status"),
                "release_gate_links": release_gate_links,
                "missing_required_fields": missing_fields,
                "high_risk": lifecycle.get("high_risk") is True,
            },
            "triage": triage,
            "roadmap_alignment": {
                "status": roadmap_alignment.get("status"),
                "top_need_id": linked_need_id,
                "match_count": len(roadmap_alignment.get("matches") or []),
                "top_match": top_match or None,
                "recommended_actions": roadmap_alignment.get("recommended_actions") or [],
            },
            "lifecycle": {
                "state": lifecycle_state,
                "next_state": lifecycle.get("next_state"),
                "next_allowed_states": lifecycle.get("next_allowed_states") or [],
                "blocking_check_ids": lifecycle.get("blocking_check_ids") or [],
                "current_transition_blocking_check_ids": current_transition_blocking_ids,
                "required_actions": lifecycle.get("required_actions") or [],
                "linkage": lifecycle.get("linkage") or {},
            },
            "ticket_defaults": {
                "status": triage["status"],
                "priority": triage["priority"],
                "assignee": triage["assignee"],
                "resolution_note": self.resolution_note(
                    triage=triage,
                    linked_need_id=linked_need_id,
                    release_gate_links=release_gate_links,
                    blocking_check_ids=current_transition_blocking_ids,
                ),
            },
            "intake_questions": self._intake_questions(triage, missing_fields),
            "public_acknowledgement": self._public_acknowledgement(triage, linked_need_id),
            "privacy_boundary": {
                "stores_raw_feedback": False,
                "returns_raw_feedback_text": False,
                "returns_user_contact": False,
                "calls_ai_model": False,
                "calls_external_network": False,
                "writes_database": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_feedback_capture_plan.py tests/test_feedback_lifecycle_policy.py tests/test_feedback_roadmap_alignment.py -q",
            ],
        }

    def enrich_ticket_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        plan = self.build_plan(payload)
        triage = plan["triage"]
        enriched = dict(payload)
        enriched["status"] = enriched.get("status") or triage["status"]
        enriched["priority"] = enriched.get("priority") or triage["priority"]
        enriched["assignee"] = enriched.get("assignee") or triage["assignee"]
        enriched["resolution_note"] = self._merged_resolution_note(
            existing=_text(enriched.get("resolution_note")),
            planned=plan["ticket_defaults"]["resolution_note"],
        )
        return enriched

    def resolution_note(
        self,
        *,
        triage: dict[str, Any],
        linked_need_id: Any,
        release_gate_links: list[str],
        blocking_check_ids: list[str],
    ) -> str:
        need = _text(linked_need_id) or "unmapped"
        gates = ", ".join(release_gate_links) if release_gate_links else "none"
        blockers = ", ".join(blocking_check_ids) if blocking_check_ids else "none"
        return (
            f"Auto-capture {triage['priority']} for {triage['assignee']}. "
            f"Roadmap need: {need}. Release gates: {gates}. Lifecycle blockers: {blockers}."
        )

    def _current_transition_blocking_ids(self, lifecycle: dict[str, Any]) -> list[str]:
        if lifecycle.get("next_allowed_states"):
            return []
        required_actions = lifecycle.get("required_actions") or []
        if not required_actions:
            return []
        return list(lifecycle.get("blocking_check_ids") or [])

    def _required_fields(self, triage: dict[str, Any]) -> list[str]:
        fields = ["category", "content"]
        labels = set(triage.get("labels") or [])
        if labels.intersection({"legal_quality", "high_risk_output", "pipeline", "document_processing"}):
            fields.append("affected_artifact_id")
        if labels.intersection({"payment", "access", "revenue_blocker"}):
            fields.append("account_context")
        return fields

    def _intake_questions(self, triage: dict[str, Any], missing_fields: list[str]) -> list[dict[str, str]]:
        questions = [
            {
                "field": "category",
                "question": "Which workflow did this affect?",
                "why": "Keeps feedback clustered by product module and support owner.",
            },
            {
                "field": "content",
                "question": "What happened, and what result did you expect?",
                "why": "Provides enough context for deterministic triage without storing extra documents.",
            },
        ]
        labels = set(triage.get("labels") or [])
        if labels.intersection({"legal_quality", "high_risk_output", "pipeline", "document_processing"}):
            questions.append(
                {
                    "field": "affected_artifact_id",
                    "question": "Which report, case, upload, or generated document was affected?",
                    "why": "Links the ticket to release validation without echoing legal matter text.",
                }
            )
        if labels.intersection({"payment", "access", "revenue_blocker"}):
            questions.append(
                {
                    "field": "account_context",
                    "question": "Which plan, invoice, or account action was blocked?",
                    "why": "Lets support verify entitlement state without collecting payment secrets.",
                }
            )
        return [
            {
                **question,
                "status": "missing" if question["field"] in missing_fields else "captured",
            }
            for question in questions
        ]

    def _public_acknowledgement(self, triage: dict[str, Any], linked_need_id: Any) -> str:
        need = _text(linked_need_id) or "the product roadmap"
        return (
            f"Feedback captured as {triage['priority']} and linked to {need}. "
            "The support team will review the release checks before closing it."
        )

    def _merged_resolution_note(self, *, existing: str, planned: str) -> str:
        if not existing:
            return planned
        if planned in existing:
            return existing
        return f"{existing} | {planned}"


def _text(value: Any) -> str:
    return str(value or "").strip()


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
