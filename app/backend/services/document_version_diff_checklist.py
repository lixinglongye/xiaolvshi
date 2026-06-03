from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


REQUIRED_DIFF_FIELDS = (
    "version_id",
    "previous_version_id",
    "change_summary",
    "changed_sections",
    "reviewer_role",
    "client_visible_summary",
)
SENSITIVE_PATTERN = re.compile(
    r"(s" r"k-[A-Za-z0-9]{20,}|APP_AI_KEY=s" r"k-|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DiffChecklistItem:
    id: str
    label: str
    required: bool
    rationale: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class DocumentVersionDiffChecklistService:
    """Validate metadata needed to show client-safe document version changes."""

    def build_checklist(self, diff: dict[str, Any] | None = None) -> dict[str, Any]:
        if diff is None:
            return {
                "status": "template",
                "summary": {
                    "required_field_count": len(REQUIRED_DIFF_FIELDS),
                    "ready_for_client_visibility": False,
                    "blocking_issue_count": 0,
                },
                "checklist_items": [item.to_api() for item in self._items()],
                "diff_review": None,
                "risk_flags": [],
                "recommended_actions": ["Submit version diff metadata before client delivery."],
                "privacy_note": self._privacy_note(),
                "validation_commands": self._validation_commands(),
            }

        review = self._review_diff(diff)
        risk_flags = review["risk_flags"]
        status = "blocked" if any(flag["severity"] == "blocking" for flag in risk_flags) else "ready"
        return {
            "status": status,
            "summary": {
                "required_field_count": len(REQUIRED_DIFF_FIELDS),
                "ready_for_client_visibility": status == "ready",
                "blocking_issue_count": sum(1 for flag in risk_flags if flag["severity"] == "blocking"),
                "warning_count": sum(1 for flag in risk_flags if flag["severity"] == "warning"),
                "changed_section_count": len(review["changed_sections"]),
            },
            "checklist_items": [item.to_api() for item in self._items()],
            "diff_review": review,
            "risk_flags": risk_flags,
            "recommended_actions": self._recommended_actions(status, risk_flags),
            "privacy_note": self._privacy_note(),
            "validation_commands": self._validation_commands(),
        }

    def _items(self) -> tuple[DiffChecklistItem, ...]:
        return (
            DiffChecklistItem("version-id", "Current version id", True, "Locks the visible package version."),
            DiffChecklistItem("previous-version-id", "Previous version id", True, "Makes the comparison target explicit."),
            DiffChecklistItem("change-summary", "Change summary", True, "Explains the change without raw confidential text."),
            DiffChecklistItem("changed-sections", "Changed sections", True, "Shows which sections changed."),
            DiffChecklistItem("reviewer-role", "Reviewer role", True, "Records who reviewed the diff."),
            DiffChecklistItem("client-visible-summary", "Client visible summary", True, "Prevents internal-only notes from leaking."),
            DiffChecklistItem("risk-change-summary", "Risk change summary", False, "Highlights whether risk changed."),
            DiffChecklistItem("source-support-status", "Source support status", False, "Shows whether citations still support changes."),
        )

    def _review_diff(self, diff: dict[str, Any]) -> dict[str, Any]:
        sanitized = {key: self._sanitize(value) for key, value in diff.items() if key in ALLOWED_FIELDS}
        missing = [field for field in REQUIRED_DIFF_FIELDS if not sanitized.get(field)]
        changed_sections = sanitized.get("changed_sections")
        if not isinstance(changed_sections, list):
            changed_sections = []
        changed_sections = [self._sanitize(item) for item in changed_sections if str(item).strip()]

        risk_flags: list[dict[str, Any]] = []
        if missing:
            risk_flags.append(
                {
                    "id": "missing-required-diff-fields",
                    "severity": "blocking",
                    "fields": missing,
                }
            )
        if sanitized.get("version_id") and sanitized.get("version_id") == sanitized.get("previous_version_id"):
            risk_flags.append({"id": "version-id-not-advanced", "severity": "blocking"})
        if not changed_sections:
            risk_flags.append({"id": "changed-sections-empty", "severity": "blocking"})
        if diff.keys() - ALLOWED_FIELDS:
            risk_flags.append(
                {
                    "id": "unsupported-diff-fields-ignored",
                    "severity": "warning",
                    "fields": sorted(diff.keys() - ALLOWED_FIELDS),
                }
            )
        if sanitized.get("source_support_status") in {"missing", "unsupported", "pending"}:
            risk_flags.append({"id": "source-support-not-ready", "severity": "blocking"})

        return {
            "version_id": sanitized.get("version_id", ""),
            "previous_version_id": sanitized.get("previous_version_id", ""),
            "change_summary": sanitized.get("change_summary", ""),
            "changed_sections": changed_sections,
            "reviewer_role": sanitized.get("reviewer_role", ""),
            "client_visible_summary": sanitized.get("client_visible_summary", ""),
            "risk_change_summary": sanitized.get("risk_change_summary", ""),
            "source_support_status": sanitized.get("source_support_status", "not_supplied"),
            "risk_flags": risk_flags,
        }

    def _recommended_actions(self, status: str, risk_flags: list[dict[str, Any]]) -> list[str]:
        if status == "ready":
            return ["Attach this client-visible version diff to the delivery package manifest."]
        action_ids = {flag["id"] for flag in risk_flags}
        actions: list[str] = []
        if "missing-required-diff-fields" in action_ids:
            actions.append("Complete all required version diff fields before client delivery.")
        if "changed-sections-empty" in action_ids:
            actions.append("List changed sections using sanitized section names only.")
        if "source-support-not-ready" in action_ids:
            actions.append("Resolve source support before marking the diff client-visible.")
        return actions or ["Resolve blocking version diff issues before delivery."]

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._sanitize(item) for key, item in value.items()}
        return SENSITIVE_PATTERN.sub("[redacted]", str(value)).strip()

    def _privacy_note(self) -> str:
        return (
            "This privacy-safe checklist stores version metadata only. Do not include raw document text, client "
            "contact details, account credentials, API keys, passwords, or internal privileged notes."
        )

    def _validation_commands(self) -> list[str]:
        return [
            "python -m pytest tests/test_document_version_diff_checklist.py -q",
            "python -m compileall services/document_version_diff_checklist.py tests/test_document_version_diff_checklist.py",
        ]


ALLOWED_FIELDS = {
    "version_id",
    "previous_version_id",
    "change_summary",
    "changed_sections",
    "reviewer_role",
    "client_visible_summary",
    "risk_change_summary",
    "source_support_status",
}
