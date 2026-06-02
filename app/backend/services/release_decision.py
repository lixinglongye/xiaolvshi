"""
Unified release decision for deep review reports.

This layer turns multiple deterministic audits into a single operational
decision: whether a report is blocked, needs lawyer review, or is ready for a
spot-check workflow.
"""

from __future__ import annotations

from typing import Any


class ReleaseDecisionService:
    """Combine audit outputs into a delivery decision."""

    def evaluate(self, report: dict[str, Any]) -> dict[str, Any]:
        quality_gate = _dict(report.get("quality_gate"))
        citation_audit = _dict(report.get("citation_audit"))
        evidence_audit = _dict(report.get("evidence_audit"))
        risk_scoring = _dict(report.get("risk_scoring"))

        blocking_reasons = self._blocking_reasons(quality_gate, citation_audit, evidence_audit)
        warning_reasons = self._warning_reasons(quality_gate, citation_audit, evidence_audit, risk_scoring)
        required_actions = self._required_actions(quality_gate, citation_audit, evidence_audit)

        if blocking_reasons:
            status = "blocked"
            release_level = "internal_draft_only"
        elif warning_reasons:
            status = "lawyer_review_required"
            release_level = "lawyer_review_required"
        else:
            status = "ready_for_spot_check"
            release_level = "ready_for_lawyer_spot_check"

        readiness_score = self._readiness_score(quality_gate, citation_audit, evidence_audit, risk_scoring)
        client_delivery_allowed = status == "ready_for_spot_check"
        lawyer_review_required = status in {"blocked", "lawyer_review_required"}

        return {
            "schema_version": "release-decision-v1",
            "status": status,
            "release_level": release_level,
            "readiness_score": readiness_score,
            "client_delivery_allowed": client_delivery_allowed,
            "lawyer_review_required": lawyer_review_required,
            "triage_level": self._triage_level(status, risk_scoring, evidence_audit),
            "blocking_reasons": blocking_reasons,
            "warning_reasons": warning_reasons,
            "required_actions": required_actions,
            "decision_factors": {
                "quality_gate_status": quality_gate.get("status", "unknown"),
                "citation_audit_status": citation_audit.get("status", "unknown"),
                "evidence_audit_status": evidence_audit.get("status", "unknown"),
                "risk_score": risk_scoring.get("overall_score", 0),
                "risk_level": risk_scoring.get("overall_level", "unknown"),
                "critical_risk_count": _counts(risk_scoring).get("critical", 0),
                "high_risk_count": _counts(risk_scoring).get("high", 0),
            },
            "summary": self._summary(status, readiness_score, blocking_reasons, warning_reasons),
        }

    def _blocking_reasons(
        self,
        quality_gate: dict[str, Any],
        citation_audit: dict[str, Any],
        evidence_audit: dict[str, Any],
    ) -> list[str]:
        reasons = []
        if quality_gate.get("status") == "fail":
            gates = _list_text(quality_gate.get("blocking_gate_ids"))
            reasons.append("Quality gate failed" + (f": {', '.join(gates)}" if gates else "."))
        if citation_audit.get("status") == "fail":
            high_risks = _list_text(citation_audit.get("high_risk_without_reviewable_citation"))
            reasons.append(
                "Citation audit failed"
                + (f"; high-risk items without reviewable citation: {', '.join(high_risks)}" if high_risks else ".")
            )
        if evidence_audit.get("status") == "fail":
            high_risks = _list_text(evidence_audit.get("high_risk_without_evidence_plan"))
            reasons.append(
                "Evidence audit failed"
                + (f"; high-risk items without evidence plan: {', '.join(high_risks)}" if high_risks else ".")
            )
        return reasons

    def _warning_reasons(
        self,
        quality_gate: dict[str, Any],
        citation_audit: dict[str, Any],
        evidence_audit: dict[str, Any],
        risk_scoring: dict[str, Any],
    ) -> list[str]:
        reasons = []
        if quality_gate.get("status") == "warn":
            gates = _list_text(quality_gate.get("warning_gate_ids"))
            reasons.append("Quality gate has warnings" + (f": {', '.join(gates)}" if gates else "."))
        if citation_audit.get("status") == "warn":
            reasons.append("Citation audit requires source verification or appendix cleanup.")
        if evidence_audit.get("status") == "warn":
            reasons.append("Evidence audit requires pending fact or evidence-plan follow-up.")
        counts = _counts(risk_scoring)
        if counts.get("critical", 0) or _safe_int(risk_scoring.get("overall_score"), 0) >= 80:
            reasons.append("High risk pressure requires lawyer review before delivery.")
        return reasons

    def _required_actions(
        self,
        quality_gate: dict[str, Any],
        citation_audit: dict[str, Any],
        evidence_audit: dict[str, Any],
    ) -> list[str]:
        actions: list[str] = []
        for gate in _list_text(quality_gate.get("blocking_gate_ids")):
            actions.append(f"Resolve quality gate: {gate}")
        actions.extend(_list_text(citation_audit.get("recommended_actions")))
        actions.extend(_list_text(evidence_audit.get("recommended_actions")))
        deduped = []
        seen = set()
        for action in actions:
            key = action.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(action)
        return deduped[:8]

    def _readiness_score(
        self,
        quality_gate: dict[str, Any],
        citation_audit: dict[str, Any],
        evidence_audit: dict[str, Any],
        risk_scoring: dict[str, Any],
    ) -> int:
        quality_score = _safe_int(quality_gate.get("score"), 0)
        citation_score = _safe_int(citation_audit.get("score"), 0)
        evidence_score = _safe_int(evidence_audit.get("score"), 0)
        risk_score = _safe_int(risk_scoring.get("overall_score"), 0)
        risk_control_score = max(40, 100 - max(0, risk_score - 55))
        score = round(
            quality_score * 0.35
            + citation_score * 0.25
            + evidence_score * 0.25
            + risk_control_score * 0.15
        )
        if quality_gate.get("status") == "fail":
            score -= 20
        if citation_audit.get("status") == "fail":
            score -= 15
        if evidence_audit.get("status") == "fail":
            score -= 15
        return max(0, min(100, score))

    def _triage_level(
        self,
        status: str,
        risk_scoring: dict[str, Any],
        evidence_audit: dict[str, Any],
    ) -> str:
        counts = _counts(risk_scoring)
        if status == "blocked" or counts.get("critical", 0) or evidence_audit.get("blocking_pending_fact_count"):
            return "urgent"
        if counts.get("high", 0) or _safe_int(risk_scoring.get("overall_score"), 0) >= 70:
            return "elevated"
        return "normal"

    def _summary(
        self,
        status: str,
        readiness_score: int,
        blocking_reasons: list[str],
        warning_reasons: list[str],
    ) -> str:
        if status == "blocked":
            return f"Internal draft only. Readiness {readiness_score}/100. Blockers: {'; '.join(blocking_reasons[:3])}"
        if status == "lawyer_review_required":
            return f"Lawyer review required before delivery. Readiness {readiness_score}/100. Warnings: {'; '.join(warning_reasons[:3])}"
        return f"Ready for lawyer spot-check workflow. Readiness {readiness_score}/100."


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _counts(value: dict[str, Any]) -> dict[str, int]:
    raw = value.get("counts") if isinstance(value.get("counts"), dict) else {}
    return {
        "critical": _safe_int(raw.get("critical"), 0),
        "high": _safe_int(raw.get("high"), 0),
        "medium": _safe_int(raw.get("medium"), 0),
        "low": _safe_int(raw.get("low"), 0),
    }


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_text(value: Any) -> list[str]:
    return [_text(item) for item in _list(value) if _text(item)]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default
