from __future__ import annotations

from typing import Any, Protocol

from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService
from services.feedback_triage import PRIORITY_RANK


class FeedbackAlignmentService(Protocol):
    def align(self, item: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        ...


STATES: tuple[str, ...] = (
    "intake",
    "triage",
    "linked_gap",
    "in_progress",
    "release_validation",
    "customer_visible_resolution",
    "closed",
)

TRANSITIONS: tuple[dict[str, Any], ...] = (
    {
        "from": "intake",
        "to": "triage",
        "check_ids": ("intake-signal-present",),
    },
    {
        "from": "triage",
        "to": "linked_gap",
        "check_ids": (
            "triage-complete",
            "roadmap-gap-or-release-gate-linked",
            "high_risk_feedback_linked",
        ),
    },
    {
        "from": "linked_gap",
        "to": "in_progress",
        "check_ids": ("work-owner-present",),
    },
    {
        "from": "in_progress",
        "to": "release_validation",
        "check_ids": (
            "release-validation-plan-present",
            "high_risk_release_gate_linked",
        ),
    },
    {
        "from": "release_validation",
        "to": "customer_visible_resolution",
        "check_ids": (
            "release-validation-accepted",
            "customer-resolution-note-present",
            "privacy-safe-public-note",
        ),
    },
    {
        "from": "customer_visible_resolution",
        "to": "closed",
        "check_ids": (
            "customer-notification-ready",
            "closure-summary-present",
        ),
    },
)


class FeedbackLifecyclePolicyService:
    """Pure local feedback lifecycle evaluator for the maintenance loop."""

    def __init__(self, alignment_service: FeedbackAlignmentService | None = None) -> None:
        self.alignment_service = alignment_service or FeedbackRoadmapAlignmentService()

    def build_policy(self) -> dict[str, Any]:
        sample_evaluations = [self.evaluate_ticket(ticket) for ticket in self._sample_tickets()]
        blocking_samples = [
            item["ticket_id"]
            for item in sample_evaluations
            if item["high_risk"] and not item["linkage"]["satisfies_high_risk_policy"]
        ]
        return {
            "status": "ready" if not blocking_samples else "needs_review",
            "state_machine": self.state_machine(),
            "transition_checks": self.transition_checks(),
            "high_risk_policy": {
                "definition": "Feedback is high risk when triage priority is P0/P1 or it carries privacy, security, legal quality, or revenue blocker labels.",
                "required_linkage": "Every high-risk item must have a roadmap_gap_id or at least one linked release gate before it can leave triage.",
                "blocking_sample_ticket_ids": blocking_samples,
            },
            "sample_tickets_evaluation": sample_evaluations,
            "privacy_note": self.privacy_note(),
            "validation_commands": self.validation_commands(),
        }

    def state_machine(self) -> dict[str, Any]:
        return {
            "states": [
                {
                    "id": state,
                    "order": index,
                    "terminal": state == "closed",
                }
                for index, state in enumerate(STATES)
            ],
            "transitions": [
                {
                    "from": transition["from"],
                    "to": transition["to"],
                    "check_ids": list(transition["check_ids"]),
                }
                for transition in TRANSITIONS
            ],
            "happy_path": list(STATES),
        }

    def transition_checks(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "intake-signal-present",
                "applies_to": "intake -> triage",
                "required": True,
                "reason": "Ticket has enough local user signal to triage: title, category, summary, or content.",
            },
            {
                "id": "triage-complete",
                "applies_to": "triage -> linked_gap",
                "required": True,
                "reason": "Deterministic triage must provide priority, assignee, labels, and matched rule IDs.",
            },
            {
                "id": "roadmap-gap-or-release-gate-linked",
                "applies_to": "triage -> linked_gap",
                "required": True,
                "reason": "Feedback should be clustered under a roadmap gap or release gate before work is scheduled.",
            },
            {
                "id": "high_risk_feedback_linked",
                "applies_to": "triage -> linked_gap",
                "required": True,
                "reason": "P0/P1, privacy/security, legal quality, or revenue blocker feedback cannot progress without gap or gate linkage.",
            },
            {
                "id": "work-owner-present",
                "applies_to": "linked_gap -> in_progress",
                "required": True,
                "reason": "The ticket must have an implementation owner, support owner, or triage assignee.",
            },
            {
                "id": "release-validation-plan-present",
                "applies_to": "in_progress -> release_validation",
                "required": True,
                "reason": "The validation step must name a roadmap gap or release gate to evaluate.",
            },
            {
                "id": "high_risk_release_gate_linked",
                "applies_to": "in_progress -> release_validation",
                "required": True,
                "reason": "High-risk feedback needs explicit release gate coverage before customer-visible resolution.",
            },
            {
                "id": "release-validation-accepted",
                "applies_to": "release_validation -> customer_visible_resolution",
                "required": True,
                "reason": "Release validation must pass or be explicitly waived before a public resolution is prepared.",
            },
            {
                "id": "customer-resolution-note-present",
                "applies_to": "release_validation -> customer_visible_resolution",
                "required": True,
                "reason": "The customer-facing resolution must explain what changed without exposing private data.",
            },
            {
                "id": "privacy-safe-public-note",
                "applies_to": "release_validation -> customer_visible_resolution",
                "required": True,
                "reason": "The public note must not contain obvious secrets, raw tokens, or credential-like values.",
            },
            {
                "id": "customer-notification-ready",
                "applies_to": "customer_visible_resolution -> closed",
                "required": True,
                "reason": "The user or support channel has a prepared or sent customer-visible update.",
            },
            {
                "id": "closure-summary-present",
                "applies_to": "customer_visible_resolution -> closed",
                "required": True,
                "reason": "The ticket needs a short closure summary for later maintenance review.",
            },
        ]

    def evaluate_ticket(self, item: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
        source = {**(item or {}), **kwargs}
        ticket_id = _text(source.get("id") or source.get("ticket_id") or "local-ticket")
        current_state = _normalize_state(source.get("state") or source.get("current_state") or "intake")
        alignment = self.alignment_service.align(source)
        triage = alignment.get("triage") or {}
        linked_gap_id = _text(
            source.get("roadmap_gap_id")
            or source.get("linked_roadmap_gap_id")
            or alignment.get("top_need_id")
        )
        linked_release_gates = _unique(
            _as_list(source.get("release_gate_links"))
            + _as_list(source.get("release_gates"))
            + _as_list(source.get("linked_release_gates"))
            + self._alignment_release_gates(alignment)
        )
        high_risk = self._is_high_risk(source, triage)
        checks = self._evaluate_checks(
            source=source,
            triage=triage,
            linked_gap_id=linked_gap_id,
            linked_release_gates=linked_release_gates,
            high_risk=high_risk,
        )
        blocking_ids = [check["id"] for check in checks if check["status"] == "fail"]
        next_state = self._next_state(current_state)
        next_allowed_states = self._next_allowed_states(current_state, checks)

        return {
            "ticket_id": ticket_id,
            "current_state": current_state,
            "next_state": next_state,
            "next_allowed_states": next_allowed_states,
            "high_risk": high_risk,
            "triage": triage,
            "roadmap_alignment_status": alignment.get("status"),
            "linkage": {
                "roadmap_gap_id": linked_gap_id or None,
                "release_gate_links": linked_release_gates,
                "satisfies_high_risk_policy": (not high_risk) or bool(linked_gap_id or linked_release_gates),
            },
            "checks": checks,
            "blocking_check_ids": blocking_ids,
            "required_actions": self._required_actions(current_state, checks),
        }

    def privacy_note(self) -> str:
        return (
            "This lifecycle service is local and deterministic. It evaluates ticket metadata, triage labels, "
            "roadmap gap IDs, release gate names, validation status, and customer-visible notes only. "
            "It does not call an AI model, persist feedback, inspect uploaded legal documents, or store raw "
            "personal data, credentials, prompts, or model outputs."
        )

    def validation_commands(self) -> list[str]:
        return [
            "python -m pytest app/backend/tests/test_feedback_lifecycle_policy.py",
            "python -m compileall app/backend/services/feedback_lifecycle_policy.py app/backend/tests/test_feedback_lifecycle_policy.py",
        ]

    def _alignment_release_gates(self, alignment: dict[str, Any]) -> list[str]:
        gates: list[str] = []
        for match in alignment.get("matches") or []:
            gates.extend(_as_list(match.get("release_gate_links")))
        return gates

    def _is_high_risk(self, source: dict[str, Any], triage: dict[str, Any]) -> bool:
        priority = _text(source.get("priority") or triage.get("priority")).upper()
        labels = set(_as_list(source.get("labels")) + _as_list(triage.get("labels")))
        risk_level = _text(source.get("risk_level")).lower()
        high_risk_labels = {
            "privacy",
            "security",
            "legal_quality",
            "high_risk_output",
            "revenue_blocker",
        }
        return (
            PRIORITY_RANK.get(priority, 99) <= PRIORITY_RANK["P1"]
            or bool(labels.intersection(high_risk_labels))
            or risk_level in {"high", "critical"}
        )

    def _evaluate_checks(
        self,
        *,
        source: dict[str, Any],
        triage: dict[str, Any],
        linked_gap_id: str,
        linked_release_gates: list[str],
        high_risk: bool,
    ) -> list[dict[str, Any]]:
        has_linkage = bool(linked_gap_id or linked_release_gates)
        has_release_gate = bool(linked_release_gates)
        public_note = _text(
            source.get("customer_visible_resolution")
            or source.get("customer_note")
            or source.get("public_resolution")
        )
        validation_status = _text(
            source.get("release_validation_status")
            or source.get("validation_status")
            or "not_run"
        ).lower()
        return [
            self._check(
                "intake-signal-present",
                self._has_intake_signal(source),
                "Ticket has title, category, summary, or content.",
                "Add a short category, summary, or user feedback excerpt before triage.",
            ),
            self._check(
                "triage-complete",
                bool(triage.get("priority") and triage.get("assignee") and triage.get("matched_rule_ids")),
                "Triage produced priority, assignee, and matched rules.",
                "Run deterministic feedback triage before linking lifecycle state.",
            ),
            self._check(
                "roadmap-gap-or-release-gate-linked",
                has_linkage,
                "Ticket is linked to a roadmap gap or release gate.",
                "Attach roadmap_gap_id or release_gate_links before scheduling work.",
            ),
            self._check(
                "high_risk_feedback_linked",
                (not high_risk) or has_linkage,
                "High-risk linkage policy is satisfied.",
                "High-risk feedback must reference a roadmap gap or release gate before it leaves triage.",
            ),
            self._check(
                "work-owner-present",
                bool(
                    source.get("work_owner")
                    or source.get("implementation_owner")
                    or source.get("owner")
                    or source.get("assignee")
                    or triage.get("assignee")
                ),
                "Ticket has a work owner or triage assignee.",
                "Assign an implementation, support, legal review, or privacy owner.",
            ),
            self._check(
                "release-validation-plan-present",
                has_linkage,
                "Release validation has a roadmap gap or gate to verify.",
                "Name the validation gate or roadmap gap that proves the feedback is handled.",
            ),
            self._check(
                "high_risk_release_gate_linked",
                (not high_risk) or has_release_gate,
                "High-risk ticket has at least one release gate link.",
                "Attach release_gate_links for high-risk feedback before validation.",
            ),
            self._check(
                "release-validation-accepted",
                validation_status in {"pass", "passed", "waived"},
                "Release validation passed or was explicitly waived.",
                "Set release_validation_status to pass or waived after local validation evidence is reviewed.",
            ),
            self._check(
                "customer-resolution-note-present",
                bool(public_note),
                "Customer-visible resolution note is present.",
                "Write a concise public resolution note before notifying the customer.",
            ),
            self._check(
                "privacy-safe-public-note",
                self._public_note_is_safe(public_note),
                "Public note does not contain obvious secrets or credential-like strings.",
                "Remove credentials, raw tokens, prompts, and private values from the public note.",
            ),
            self._check(
                "customer-notification-ready",
                _truthy(
                    source.get("customer_notified")
                    or source.get("customer_notification_ready")
                    or source.get("customer_notification_sent")
                ),
                "Customer notification is ready or sent.",
                "Prepare or send the customer-visible update before closure.",
            ),
            self._check(
                "closure-summary-present",
                bool(source.get("closure_summary") or source.get("closed_reason") or source.get("resolution_outcome")),
                "Closure summary is present.",
                "Add a short internal closure summary for maintenance review.",
            ),
        ]

    def _check(self, check_id: str, passed: bool, pass_reason: str, fail_reason: str) -> dict[str, Any]:
        return {
            "id": check_id,
            "status": "pass" if passed else "fail",
            "reason": pass_reason if passed else fail_reason,
        }

    def _has_intake_signal(self, source: dict[str, Any]) -> bool:
        return any(_text(source.get(key)) for key in ("title", "category", "summary", "content"))

    def _public_note_is_safe(self, public_note: str) -> bool:
        lowered = public_note.lower()
        blocked_fragments = ("sk-", "password", "api_key", "secret", "token:")
        return not any(fragment in lowered for fragment in blocked_fragments)

    def _next_state(self, current_state: str) -> str | None:
        if current_state not in STATES or current_state == STATES[-1]:
            return None
        return STATES[STATES.index(current_state) + 1]

    def _next_allowed_states(self, current_state: str, checks: list[dict[str, Any]]) -> list[str]:
        next_state = self._next_state(current_state)
        if not next_state:
            return []
        transition = next(
            (item for item in TRANSITIONS if item["from"] == current_state and item["to"] == next_state),
            None,
        )
        if not transition:
            return []
        check_status = {check["id"]: check["status"] for check in checks}
        if all(check_status.get(check_id) == "pass" for check_id in transition["check_ids"]):
            return [next_state]
        return []

    def _required_actions(self, current_state: str, checks: list[dict[str, Any]]) -> list[str]:
        next_state = self._next_state(current_state)
        if not next_state:
            return []
        transition = next(
            (item for item in TRANSITIONS if item["from"] == current_state and item["to"] == next_state),
            None,
        )
        if not transition:
            return ["Reset the ticket to a known lifecycle state before continuing."]
        check_by_id = {check["id"]: check for check in checks}
        return [
            check_by_id[check_id]["reason"]
            for check_id in transition["check_ids"]
            if check_by_id.get(check_id, {}).get("status") == "fail"
        ]

    def _sample_tickets(self) -> tuple[dict[str, Any], ...]:
        return (
            {
                "id": "sample-privacy-upload",
                "state": "in_progress",
                "category": "security",
                "content": "User reports personal information exposure after uploading a legal file.",
                "work_owner": "security_privacy_owner",
            },
            {
                "id": "sample-incorrect-citation",
                "state": "release_validation",
                "category": "report",
                "content": "The generated report has an incorrect citation and a hallucinated legal claim.",
                "release_validation_status": "pass",
                "customer_visible_resolution": "Citation audit and evidence gate were fixed; affected report guidance was refreshed.",
            },
            {
                "id": "sample-ocr-blank-output",
                "state": "customer_visible_resolution",
                "category": "bug",
                "content": "Scanned PDF upload produced blank OCR output.",
                "release_validation_status": "pass",
                "customer_visible_resolution": "OCR extraction now blocks blank text before review and asks for a clearer file.",
                "customer_notified": True,
                "closure_summary": "Extraction quality guard added to the upload review loop.",
            },
            {
                "id": "sample-export-template-request",
                "state": "triage",
                "category": "suggestion",
                "content": "Please add a reusable export template for client delivery summaries.",
            },
        )


def _normalize_state(value: Any) -> str:
    state = _text(value).lower()
    return state if state in STATES else "intake"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set)):
        return [_text(item) for item in value if _text(item)]
    return [_text(value)] if _text(value) else []


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _text(value: Any) -> str:
    return str(value or "").strip()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return _text(value).lower() in {"1", "true", "yes", "y", "ready", "sent", "done"}
