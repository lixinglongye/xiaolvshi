from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import re
from typing import Any


REFERENCE_DATE = date(2026, 6, 4)

SENSITIVE_TEXT_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DeadlineRiskBand:
    band: str
    day_range: str
    reminder_required: bool
    lawyer_review_required: bool
    action: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class DeadlineValidationPolicyService:
    """Evaluate legal deadline metadata with deterministic local rules."""

    DATE_FIELDS = (
        "due_date",
        "deadline_date",
        "service_date",
        "served_at",
        "evidence_due_date",
        "appeal_due_date",
        "contract_performance_date",
        "case_date",
        "event_date",
    )
    DEADLINE_TYPE_ALIASES = {
        "served": "service_date",
        "service": "service_date",
        "delivery": "service_date",
        "proof": "evidence_deadline",
        "evidence": "evidence_deadline",
        "appeal": "appeal_deadline",
        "contract": "contract_performance_deadline",
        "performance": "contract_performance_deadline",
        "limitation": "limitation_period",
        "statute": "limitation_period",
        "filing": "filing_deadline",
        "case": "case_date",
    }

    def build_policy(
        self,
        deadlines: list[dict[str, Any]] | None = None,
        reference_date: str | date | None = None,
    ) -> dict[str, Any]:
        effective_reference_date = self._parse_reference_date(reference_date)
        input_items = deadlines if isinstance(deadlines, list) else self._example_deadlines()
        checks = [
            self._evaluate_deadline(item, index, effective_reference_date)
            for index, item in enumerate(input_items, start=1)
            if isinstance(item, dict)
        ]

        summary = self._summary(checks)
        return {
            "status": self._status(summary),
            "policy_id": "deadline-validation-policy-v1",
            "reference_date": effective_reference_date.isoformat(),
            "summary": summary,
            "checks": checks,
            "risk_bands": [band.to_api() for band in self._risk_bands()],
            "recommended_actions": self._recommended_actions(summary),
            "privacy_note": (
                "Deadline validation uses identifiers, deadline types, and ISO date metadata only. "
                "Free text is redacted before output, and tokens, credentials, emails, and case narratives "
                "must not be stored in reminder payloads."
            ),
            "validation_commands": [
                {
                    "id": "deadline-validation-policy-tests",
                    "command": "python -m pytest tests/test_deadline_validation_policy.py -q",
                    "resource_note": "Runs deterministic local date tests only; no network, model call, or large fixture is required.",
                },
                {
                    "id": "deadline-validation-policy-diff-check",
                    "command": (
                        "git diff --check -- app/backend/services/deadline_validation_policy.py "
                        "app/backend/tests/test_deadline_validation_policy.py docs/DEADLINE_VALIDATION_POLICY.md"
                    ),
                    "resource_note": "Checks whitespace in only the files owned by this policy task.",
                },
            ],
        }

    def _evaluate_deadline(
        self,
        item: dict[str, Any],
        index: int,
        reference_date: date,
    ) -> dict[str, Any]:
        deadline_type = self._deadline_type(item)
        raw_date = self._first_present(item, self.DATE_FIELDS)
        parsed_date = self._parse_iso_date(raw_date)
        item_id = self._safe_identifier(item.get("deadline_id") or item.get("id") or f"deadline-{index}")

        if parsed_date is None:
            return {
                "deadline_id": item_id,
                "deadline_type": deadline_type,
                "date_present": False,
                "date_valid": False,
                "days_until_due": None,
                "risk_band": "missing_date",
                "requires_reminder": False,
                "requires_lawyer_review": True,
                "reasons": [
                    "A controlling date is missing or is not an ISO date.",
                    "A lawyer or trained case operator must verify the source document before reminders are scheduled.",
                ],
                "recommended_action_ids": ["collect-controlling-date", "lawyer-date-review"],
                "safe_label": self._safe_label(item, item_id),
            }

        days_until_due = (parsed_date - reference_date).days
        risk_band = self._risk_band_for_days(days_until_due)
        requires_lawyer_review = risk_band in {"overdue", "urgent", "missing_date"} or deadline_type in {
            "appeal_deadline",
            "limitation_period",
        }
        requires_reminder = risk_band in {"overdue", "urgent", "near"}

        return {
            "deadline_id": item_id,
            "deadline_type": deadline_type,
            "date_present": True,
            "date_valid": True,
            "deadline_date": parsed_date.isoformat(),
            "days_until_due": days_until_due,
            "risk_band": risk_band,
            "requires_reminder": requires_reminder,
            "requires_lawyer_review": requires_lawyer_review,
            "reasons": self._reasons(deadline_type, risk_band, days_until_due),
            "recommended_action_ids": self._action_ids(deadline_type, risk_band, requires_lawyer_review),
            "safe_label": self._safe_label(item, item_id),
        }

    def _deadline_type(self, item: dict[str, Any]) -> str:
        raw_type = str(
            item.get("deadline_type")
            or item.get("event_type")
            or item.get("type")
            or item.get("category")
            or "general_deadline"
        ).strip().lower()
        normalized = raw_type.replace("-", "_").replace(" ", "_")
        return self.DEADLINE_TYPE_ALIASES.get(normalized, normalized or "general_deadline")

    def _summary(self, checks: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "check_count": len(checks),
            "ok_count": sum(1 for item in checks if item["risk_band"] in {"watch", "clear"}),
            "reminder_count": sum(1 for item in checks if item["requires_reminder"]),
            "lawyer_review_count": sum(1 for item in checks if item["requires_lawyer_review"]),
            "overdue_count": sum(1 for item in checks if item["risk_band"] == "overdue"),
            "urgent_count": sum(1 for item in checks if item["risk_band"] == "urgent"),
            "near_count": sum(1 for item in checks if item["risk_band"] == "near"),
            "missing_date_count": sum(1 for item in checks if item["risk_band"] == "missing_date"),
            "deterministic": True,
        }

    def _status(self, summary: dict[str, Any]) -> str:
        if summary["missing_date_count"]:
            return "needs_date_verification"
        if summary["overdue_count"] or summary["urgent_count"]:
            return "lawyer_review_required"
        if summary["reminder_count"] or summary["lawyer_review_count"]:
            return "reminder_required"
        return "ready"

    def _risk_band_for_days(self, days_until_due: int) -> str:
        if days_until_due < 0:
            return "overdue"
        if days_until_due <= 3:
            return "urgent"
        if days_until_due <= 7:
            return "near"
        if days_until_due <= 14:
            return "watch"
        return "clear"

    def _reasons(self, deadline_type: str, risk_band: str, days_until_due: int) -> list[str]:
        reasons = {
            "overdue": [f"The controlling date passed {-days_until_due} day(s) before the reference date."],
            "urgent": [f"The controlling date is within {days_until_due} day(s) of the reference date."],
            "near": ["The controlling date is within the seven-day reminder window."],
            "watch": ["The controlling date is in the watch window and should stay visible on the case timeline."],
            "clear": ["The controlling date is outside the low-resource reminder window."],
        }[risk_band]

        if deadline_type in {"appeal_deadline", "limitation_period"}:
            reasons.append("This deadline type is high-consequence and should receive lawyer review even when not urgent.")
        if deadline_type == "service_date":
            reasons.append("Service dates should be checked against answer, evidence, and appeal computation rules.")
        if deadline_type == "contract_performance_deadline":
            reasons.append("Contract performance dates should be checked before default, termination, or demand workflows.")
        return reasons

    def _action_ids(self, deadline_type: str, risk_band: str, requires_lawyer_review: bool) -> list[str]:
        action_ids: list[str] = []
        if risk_band == "overdue":
            action_ids.extend(["same-day-escalation", "preservation-review"])
        elif risk_band == "urgent":
            action_ids.extend(["same-day-reminder", "lawyer-date-review"])
        elif risk_band == "near":
            action_ids.append("case-team-reminder")
        elif risk_band == "watch":
            action_ids.append("timeline-watch-checkpoint")
        else:
            action_ids.append("standard-calendar-monitoring")

        if requires_lawyer_review and "lawyer-date-review" not in action_ids:
            action_ids.append("lawyer-date-review")
        if deadline_type == "service_date":
            action_ids.append("derive-dependent-deadlines")
        return action_ids

    def _recommended_actions(self, summary: dict[str, Any]) -> list[dict[str, Any]]:
        actions = [
            {
                "id": "collect-controlling-date",
                "when": "missing_date_count is greater than zero",
                "owner": "case_operator",
                "action": "Collect the source document date and normalize it to YYYY-MM-DD before computing reminders.",
            },
            {
                "id": "lawyer-date-review",
                "when": "deadline is overdue, urgent, an appeal deadline, or a limitation period",
                "owner": "responsible_lawyer",
                "action": "Review calculation basis, jurisdictional rule, service method, and filing or performance plan.",
            },
            {
                "id": "same-day-escalation",
                "when": "overdue_count or urgent_count is greater than zero",
                "owner": "case_owner",
                "action": "Create same-day escalation in the case workspace and block client delivery until reviewed.",
            },
            {
                "id": "case-team-reminder",
                "when": "deadline is within four to seven days",
                "owner": "case_team",
                "action": "Notify the assigned owner and confirm documents, evidence, or performance materials are ready.",
            },
            {
                "id": "derive-dependent-deadlines",
                "when": "service date is validated",
                "owner": "case_operator",
                "action": "Use the verified service date to derive answer, evidence, appeal, and review checkpoints.",
            },
        ]

        if summary["check_count"] == 0:
            return actions
        return [action for action in actions if self._action_is_relevant(action["id"], summary)]

    def _action_is_relevant(self, action_id: str, summary: dict[str, Any]) -> bool:
        if action_id == "collect-controlling-date":
            return summary["missing_date_count"] > 0
        if action_id == "same-day-escalation":
            return summary["overdue_count"] > 0 or summary["urgent_count"] > 0
        if action_id == "case-team-reminder":
            return summary["near_count"] > 0
        if action_id == "lawyer-date-review":
            return summary["lawyer_review_count"] > 0
        return True

    def _risk_bands(self) -> tuple[DeadlineRiskBand, ...]:
        return (
            DeadlineRiskBand(
                band="overdue",
                day_range="less than 0 days until due",
                reminder_required=True,
                lawyer_review_required=True,
                action="Escalate the same day and verify preservation or remedial options.",
            ),
            DeadlineRiskBand(
                band="urgent",
                day_range="0 to 3 days until due",
                reminder_required=True,
                lawyer_review_required=True,
                action="Create same-day reminder and route to lawyer review.",
            ),
            DeadlineRiskBand(
                band="near",
                day_range="4 to 7 days until due",
                reminder_required=True,
                lawyer_review_required=False,
                action="Notify the case team and confirm preparation status.",
            ),
            DeadlineRiskBand(
                band="watch",
                day_range="8 to 14 days until due",
                reminder_required=False,
                lawyer_review_required=False,
                action="Keep on timeline watch list and schedule a preparation checkpoint.",
            ),
            DeadlineRiskBand(
                band="clear",
                day_range="more than 14 days until due",
                reminder_required=False,
                lawyer_review_required=False,
                action="Use standard calendar monitoring.",
            ),
            DeadlineRiskBand(
                band="missing_date",
                day_range="date missing or invalid",
                reminder_required=False,
                lawyer_review_required=True,
                action="Collect and verify the controlling date before relying on reminders.",
            ),
        )

    def _example_deadlines(self) -> list[dict[str, Any]]:
        return [
            {
                "deadline_id": "example-service",
                "deadline_type": "service_date",
                "service_date": "2026-06-01",
            },
            {
                "deadline_id": "example-evidence",
                "deadline_type": "evidence_deadline",
                "evidence_due_date": "2026-06-10",
            },
            {
                "deadline_id": "example-appeal",
                "deadline_type": "appeal_deadline",
                "appeal_due_date": "2026-06-18",
            },
            {
                "deadline_id": "example-contract",
                "deadline_type": "contract_performance_deadline",
                "contract_performance_date": "2026-06-25",
            },
        ]

    def _safe_label(self, item: dict[str, Any], fallback: str) -> str:
        for field in ("label", "title", "name"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                cleaned = SENSITIVE_TEXT_PATTERN.sub("[redacted]", value.strip())
                if cleaned != value.strip():
                    return "[redacted]"
                return cleaned[:80]
        return fallback

    def _safe_identifier(self, value: Any) -> str:
        raw = str(value or "").strip()[:80]
        if not raw or SENSITIVE_TEXT_PATTERN.search(raw):
            return "redacted-id"
        return raw

    def _parse_reference_date(self, value: str | date | None) -> date:
        if isinstance(value, date):
            return value
        parsed = self._parse_iso_date(value)
        return parsed or REFERENCE_DATE

    def _parse_iso_date(self, value: Any) -> date | None:
        if isinstance(value, date):
            return value
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None

    def _first_present(self, item: dict[str, Any], fields: tuple[str, ...]) -> Any:
        for field in fields:
            value = item.get(field)
            if value not in (None, ""):
                return value
        return None
