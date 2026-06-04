from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SUPPORTED_ACTIONS = {
    "export_report": "Export report",
    "deliver_to_client": "Deliver to client",
    "account_plan_review": "Account plan review",
}

PRIVACY_BOUNDARY = {
    "raw_document_text_included": False,
    "billing_provider_payload_included": False,
    "pii_included": False,
    "output_scope": "quota status, numeric counters, action status, and reason codes only",
}


class QuotaDeliveryDecisionService:
    """Convert quota summaries into export, delivery, and account-plan decisions."""

    def decide(
        self,
        *,
        action: str,
        quota_summary: Mapping[str, Any] | None,
        release_decision: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_action = self._action(action)
        quota = dict(quota_summary or {})
        release = dict(release_decision or {})
        reason_codes = self._quota_reasons(quota)
        release_status = str(release.get("status") or release.get("release_status") or "").strip().lower()
        if release_status in {"blocked", "fail", "failed"}:
            reason_codes.append("release_decision_blocked")
        if release.get("lawyer_review_required") is True:
            reason_codes.append("lawyer_review_required")

        status = self._status(reason_codes)
        return {
            "status": status,
            "action": normalized_action,
            "action_label": SUPPORTED_ACTIONS[normalized_action],
            "reason_codes": self._dedupe(reason_codes),
            "quota_window": quota.get("quota_window"),
            "reports_remaining": self._safe_number(quota.get("reports_remaining") or quota.get("remaining")),
            "report_quota_monthly": self._safe_number(quota.get("report_quota_monthly") or quota.get("limit")),
            "decision": self._decision_text(status, normalized_action),
            "required_next_steps": self._next_steps(status, normalized_action),
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _quota_reasons(self, quota: dict[str, Any]) -> list[str]:
        reasons = [str(item) for item in quota.get("reason_codes") or [] if str(item or "").strip()]
        decision_status = str(quota.get("decision_status") or "").strip().lower()
        can_create = quota.get("can_create_report")
        remaining = self._safe_number(quota.get("reports_remaining") or quota.get("remaining"))
        if decision_status == "blocked" or can_create is False:
            reasons.append("report_quota_blocked")
        if remaining is not None and remaining <= 0 and decision_status != "ready":
            reasons.append("report_quota_exhausted")
        return reasons

    def _status(self, reason_codes: list[str]) -> str:
        blocking = {"report_quota_blocked", "report_quota_exhausted", "release_decision_blocked"}
        if blocking.intersection(reason_codes):
            return "blocked"
        if reason_codes:
            return "review_required"
        return "ready"

    def _next_steps(self, status: str, action: str) -> list[str]:
        if status == "ready":
            return [f"{SUPPORTED_ACTIONS[action]} can proceed with current quota metadata."]
        if status == "blocked":
            return [
                "Stop automated export or delivery.",
                "Ask an authorized reviewer to resolve quota or release blockers.",
                "Record only sanitized quota metadata in audit evidence.",
            ]
        return [
            "Route the action to lawyer or account review before delivery.",
            "Keep raw legal text and billing provider payloads out of quota decision logs.",
        ]

    def _decision_text(self, status: str, action: str) -> str:
        if status == "ready":
            return f"{SUPPORTED_ACTIONS[action]} is allowed by current quota and release metadata."
        if status == "blocked":
            return f"{SUPPORTED_ACTIONS[action]} is blocked until quota or release blockers are resolved."
        return f"{SUPPORTED_ACTIONS[action]} requires manual review before proceeding."

    def _action(self, action: str) -> str:
        value = str(action or "").strip().lower().replace("-", "_")
        return value if value in SUPPORTED_ACTIONS else "export_report"

    def _safe_number(self, value: Any) -> float | int | None:
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return value
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _dedupe(self, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            clean = value.strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            result.append(clean)
        return result
