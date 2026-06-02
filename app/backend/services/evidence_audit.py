"""
Deterministic evidence and pending-fact audit for deep review reports.

The audit checks whether each risk has an evidence plan and whether unresolved
fact gaps make the report unsuitable for delivery without human follow-up.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


class EvidenceAuditService:
    """Audit evidence suggestions, proof gaps, and pending facts."""

    def evaluate(self, report: dict[str, Any]) -> dict[str, Any]:
        risk_items = _dicts(report.get("risk_items"))
        pending_facts = _list(report.get("pending_facts"))
        framework = report.get("professional_review_framework")
        framework = framework if isinstance(framework, dict) else {}
        framework_evidence = _list_text(framework.get("evidence_checklist"))

        risk_evidence = []
        risks_without_evidence_plan = []
        high_risk_without_evidence_plan = []
        all_suggestions = []
        for index, risk in enumerate(risk_items):
            risk_id = _risk_id(risk, index)
            suggestions = _evidence_suggestions(risk)
            all_suggestions.extend(_normalize_key(item) for item in suggestions)
            has_plan = bool(suggestions)
            if not has_plan:
                risks_without_evidence_plan.append(risk_id)
            if _risk_level(risk.get("risk_level")) in {"critical", "high"} and not has_plan:
                high_risk_without_evidence_plan.append(risk_id)

            risk_evidence.append(
                {
                    "risk_id": risk_id,
                    "risk_level": _risk_level(risk.get("risk_level")),
                    "suggestion_count": len(suggestions),
                    "has_evidence_plan": has_plan,
                    "sample_suggestions": suggestions[:3],
                }
            )

        duplicates = sorted(
            suggestion
            for suggestion, count in Counter(item for item in all_suggestions if item).items()
            if count > 2
        )
        pending_fact_items = [self._pending_fact_item(item, index) for index, item in enumerate(pending_facts)]
        blocking_pending_fact_ids = [
            item["fact_id"]
            for item in pending_fact_items
            if item["blocking"]
        ]

        risk_count = len(risk_items)
        risk_with_evidence_count = sum(1 for item in risk_evidence if item["has_evidence_plan"])
        risk_evidence_coverage = round(risk_with_evidence_count / risk_count, 2) if risk_count else 0
        evidence_suggestion_count = sum(item["suggestion_count"] for item in risk_evidence)

        score = self._score(
            risk_evidence_coverage=risk_evidence_coverage,
            framework_evidence_count=len(framework_evidence),
            pending_fact_count=len(pending_fact_items),
            blocking_pending_fact_count=len(blocking_pending_fact_ids),
            high_risk_without_evidence_plan=high_risk_without_evidence_plan,
            duplicate_suggestions=duplicates,
        )
        status = self._status(
            high_risk_without_evidence_plan=high_risk_without_evidence_plan,
            blocking_pending_fact_ids=blocking_pending_fact_ids,
            risk_evidence_coverage=risk_evidence_coverage,
        )

        return {
            "schema_version": "evidence-audit-v1",
            "status": status,
            "score": score,
            "risk_count": risk_count,
            "risk_with_evidence_count": risk_with_evidence_count,
            "risk_evidence_coverage": risk_evidence_coverage,
            "evidence_suggestion_count": evidence_suggestion_count,
            "framework_evidence_count": len(framework_evidence),
            "pending_fact_count": len(pending_fact_items),
            "blocking_pending_fact_count": len(blocking_pending_fact_ids),
            "risks_without_evidence_plan": risks_without_evidence_plan,
            "high_risk_without_evidence_plan": high_risk_without_evidence_plan,
            "blocking_pending_fact_ids": blocking_pending_fact_ids,
            "duplicate_evidence_suggestions": duplicates,
            "risk_evidence": risk_evidence,
            "pending_fact_items": pending_fact_items,
            "evidence_tasks": self._tasks(risk_evidence, pending_fact_items, framework_evidence),
            "recommended_actions": self._actions(
                high_risk_without_evidence_plan=high_risk_without_evidence_plan,
                risks_without_evidence_plan=risks_without_evidence_plan,
                blocking_pending_fact_ids=blocking_pending_fact_ids,
                framework_evidence_count=len(framework_evidence),
            ),
        }

    def _pending_fact_item(self, item: Any, index: int) -> dict[str, Any]:
        if isinstance(item, dict):
            field = _text(item.get("field")) or _text(item.get("name")) or f"pending-fact-{index + 1}"
            reason = _text(item.get("reason"))
            impact = _text(item.get("impact"))
        else:
            field = _text(item) or f"pending-fact-{index + 1}"
            reason = ""
            impact = ""
        blob = f"{field}\n{reason}\n{impact}".lower()
        blocking = any(
            marker in blob
            for marker in (
                "critical",
                "material",
                "must",
                "required",
                "\u5fc5\u987b",
                "\u5173\u952e",
                "\u91cd\u8981",
                "\u5f71\u54cd\u98ce\u9669",
                "\u65e0\u6cd5\u5224\u65ad",
            )
        )
        return {
            "fact_id": f"PF-{index + 1:03d}",
            "field": field,
            "reason": reason,
            "impact": impact,
            "blocking": blocking,
        }

    def _score(
        self,
        *,
        risk_evidence_coverage: float,
        framework_evidence_count: int,
        pending_fact_count: int,
        blocking_pending_fact_count: int,
        high_risk_without_evidence_plan: list[str],
        duplicate_suggestions: list[str],
    ) -> int:
        score = round(risk_evidence_coverage * 70)
        score += min(15, framework_evidence_count * 3)
        score += 10 if pending_fact_count else 5
        score -= blocking_pending_fact_count * 10
        score -= len(high_risk_without_evidence_plan) * 15
        score -= min(10, len(duplicate_suggestions) * 2)
        return max(0, min(100, score))

    def _status(
        self,
        *,
        high_risk_without_evidence_plan: list[str],
        blocking_pending_fact_ids: list[str],
        risk_evidence_coverage: float,
    ) -> str:
        if high_risk_without_evidence_plan:
            return "fail"
        if blocking_pending_fact_ids or risk_evidence_coverage < 0.75:
            return "warn"
        return "pass"

    def _tasks(
        self,
        risk_evidence: list[dict[str, Any]],
        pending_fact_items: list[dict[str, Any]],
        framework_evidence: list[str],
    ) -> list[dict[str, Any]]:
        tasks = []
        for item in risk_evidence:
            if item["has_evidence_plan"]:
                continue
            tasks.append(
                {
                    "task_id": f"EV-{len(tasks) + 1:03d}",
                    "type": "risk_evidence_plan",
                    "target": item["risk_id"],
                    "priority": "high" if item["risk_level"] in {"critical", "high"} else "normal",
                    "description": "Add concrete evidence preservation and proof suggestions for this risk.",
                }
            )
        for item in pending_fact_items:
            if not item["blocking"]:
                continue
            tasks.append(
                {
                    "task_id": f"EV-{len(tasks) + 1:03d}",
                    "type": "pending_fact",
                    "target": item["fact_id"],
                    "priority": "high",
                    "description": f"Resolve pending fact before external delivery: {item['field']}",
                }
            )
        if not framework_evidence:
            tasks.append(
                {
                    "task_id": f"EV-{len(tasks) + 1:03d}",
                    "type": "framework_evidence_checklist",
                    "target": "professional_review_framework.evidence_checklist",
                    "priority": "normal",
                    "description": "Add matter-specific evidence checklist to the review framework.",
                }
            )
        return tasks[:12]

    def _actions(
        self,
        *,
        high_risk_without_evidence_plan: list[str],
        risks_without_evidence_plan: list[str],
        blocking_pending_fact_ids: list[str],
        framework_evidence_count: int,
    ) -> list[str]:
        actions = []
        if high_risk_without_evidence_plan:
            actions.append(
                "Add evidence plans for high-risk items: "
                + ", ".join(high_risk_without_evidence_plan[:8])
            )
        elif risks_without_evidence_plan:
            actions.append(
                "Complete evidence plans for risk items: "
                + ", ".join(risks_without_evidence_plan[:8])
            )
        if blocking_pending_fact_ids:
            actions.append(
                "Resolve blocking pending facts: "
                + ", ".join(blocking_pending_fact_ids[:8])
            )
        if framework_evidence_count == 0:
            actions.append("Add a matter-specific evidence checklist to the review framework.")
        return actions[:6]


def _evidence_suggestions(risk: dict[str, Any]) -> list[str]:
    analysis = risk.get("legal_analysis") if isinstance(risk.get("legal_analysis"), dict) else {}
    suggestions = _list_text(analysis.get("evidence_suggestion"))
    suggestions.extend(_list_text(risk.get("evidence_suggestions")))
    seen = set()
    unique = []
    for item in suggestions:
        key = _normalize_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _risk_id(item: dict[str, Any], index: int) -> str:
    return _text(item.get("risk_id")) or _text(item.get("risk_no")) or f"R-{index + 1:03d}"


def _risk_level(value: Any) -> str:
    raw = _text(value).lower()
    if raw in {"critical", "major", "severe", "\u91cd\u5927", "\u4e25\u91cd"}:
        return "critical"
    if raw in {"high", "\u9ad8"}:
        return "high"
    if raw in {"low", "\u4f4e"}:
        return "low"
    return "medium"


def _normalize_key(value: Any) -> str:
    return "".join(_text(value).lower().split())


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _list_text(value: Any) -> list[str]:
    return [_text(item) for item in _list(value) if _text(item)]
