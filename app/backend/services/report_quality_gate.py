"""
Deterministic quality gates for deep legal review reports.

The gate is intentionally conservative. It does not decide whether the legal
analysis is correct; it checks whether a report is reviewable enough for a human
lawyer or legal operator to audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GateRule:
    gate_id: str
    severity: str
    description: str


GATE_RULES: tuple[GateRule, ...] = (
    GateRule("risk-items-present", "fail", "Report must contain at least one structured risk item."),
    GateRule("risks-grounded", "fail", "Every risk item should cite an original clause or issue location."),
    GateRule("high-risk-citations", "fail", "High or critical risks should include verified or reviewable citations."),
    GateRule("revision-plans", "fail", "Every risk item should include at least one replacement clause or revision plan."),
    GateRule("pending-facts", "warn", "Report should list fact gaps or explicitly explain why none are needed."),
    GateRule("legal-appendix", "warn", "Report should include a legal authority appendix for citation review."),
    GateRule("disclaimer", "fail", "Report must include an AI/legal-opinion disclaimer."),
)


class ReportQualityGate:
    def evaluate(self, report: dict[str, Any]) -> dict[str, Any]:
        risk_items = _dicts(report.get("risk_items"))
        appendix = _dicts(report.get("legal_authority_appendix"))
        pending_facts = _list(report.get("pending_facts"))
        disclaimer = _text(report.get("disclaimer"))
        quality_audit = report.get("quality_audit") if isinstance(report.get("quality_audit"), dict) else {}

        evaluations = [
            self._risk_items_present(risk_items),
            self._risks_grounded(risk_items),
            self._high_risk_citations(risk_items),
            self._revision_plans(risk_items),
            self._pending_facts(pending_facts, quality_audit),
            self._legal_appendix(appendix),
            self._disclaimer(disclaimer),
        ]
        fail_count = sum(1 for item in evaluations if item["status"] == "fail")
        warn_count = sum(1 for item in evaluations if item["status"] == "warn")
        pass_count = sum(1 for item in evaluations if item["status"] == "pass")

        if fail_count:
            status = "fail"
            release_level = "internal_draft_only"
        elif warn_count:
            status = "warn"
            release_level = "lawyer_review_required"
        else:
            status = "pass"
            release_level = "ready_for_lawyer_spot_check"

        score = max(0, min(100, 100 - fail_count * 18 - warn_count * 7))
        return {
            "status": status,
            "release_level": release_level,
            "score": score,
            "pass_count": pass_count,
            "warn_count": warn_count,
            "fail_count": fail_count,
            "evaluations": evaluations,
            "blocking_gate_ids": [item["gate_id"] for item in evaluations if item["status"] == "fail"],
            "warning_gate_ids": [item["gate_id"] for item in evaluations if item["status"] == "warn"],
        }

    def _risk_items_present(self, risk_items: list[dict[str, Any]]) -> dict[str, Any]:
        status = "pass" if risk_items else "fail"
        return _evaluation(
            "risk-items-present",
            status,
            evidence={"risk_count": len(risk_items)},
        )

    def _risks_grounded(self, risk_items: list[dict[str, Any]]) -> dict[str, Any]:
        ungrounded = []
        for item in risk_items:
            original_clause = item.get("original_clause") if isinstance(item.get("original_clause"), dict) else {}
            has_original = bool(_text(original_clause.get("text"))) or bool(_text(original_clause.get("clause_number")))
            has_issue = bool(_text(item.get("issue_location")))
            if not has_original and not has_issue:
                ungrounded.append(_risk_id(item))
        status = "pass" if not ungrounded else "fail"
        return _evaluation(
            "risks-grounded",
            status,
            evidence={"ungrounded_risk_ids": ungrounded, "risk_count": len(risk_items)},
        )

    def _high_risk_citations(self, risk_items: list[dict[str, Any]]) -> dict[str, Any]:
        missing = []
        for item in risk_items:
            if _risk_level(item.get("risk_level")) not in {"high", "critical"}:
                continue
            citations = _dicts(item.get("citations"))
            if not citations:
                missing.append(_risk_id(item))
                continue
            has_reviewable = any(_is_reviewable_citation(citation) for citation in citations)
            if not has_reviewable:
                missing.append(_risk_id(item))
        status = "pass" if not missing else "fail"
        return _evaluation(
            "high-risk-citations",
            status,
            evidence={"high_risk_ids_without_reviewable_citation": missing},
        )

    def _revision_plans(self, risk_items: list[dict[str, Any]]) -> dict[str, Any]:
        missing = []
        for item in risk_items:
            revision = item.get("revision_plan") if isinstance(item.get("revision_plan"), dict) else {}
            has_revision = any(
                bool(_text(revision.get(key)))
                for key in ("conservative_clause", "balanced_clause", "bottom_line_clause", "negotiation_strategy")
            )
            if not has_revision:
                missing.append(_risk_id(item))
        status = "pass" if not missing else "fail"
        return _evaluation(
            "revision-plans",
            status,
            evidence={"risk_ids_without_revision_plan": missing},
        )

    def _pending_facts(self, pending_facts: list[Any], quality_audit: dict[str, Any]) -> dict[str, Any]:
        warnings = [_text(item) for item in _list(quality_audit.get("warnings"))]
        explicit_no_gap = any("pending fact" in warning.lower() or "fact" in warning.lower() for warning in warnings)
        status = "pass" if pending_facts or explicit_no_gap else "warn"
        return _evaluation(
            "pending-facts",
            status,
            evidence={"pending_fact_count": len(pending_facts)},
        )

    def _legal_appendix(self, appendix: list[dict[str, Any]]) -> dict[str, Any]:
        incomplete = [
            _text(item.get("source_id")) or f"source-{index + 1}"
            for index, item in enumerate(appendix)
            if not _text(item.get("source_name")) or not _text(item.get("authority_level"))
        ]
        if not appendix:
            status = "warn"
        elif incomplete:
            status = "warn"
        else:
            status = "pass"
        return _evaluation(
            "legal-appendix",
            status,
            evidence={"source_count": len(appendix), "incomplete_source_ids": incomplete},
        )

    def _disclaimer(self, disclaimer: str) -> dict[str, Any]:
        lowered = disclaimer.lower()
        has_ai = "ai" in lowered or "artificial intelligence" in lowered
        has_legal_limit = "not legal advice" in lowered or "lawyer" in lowered or "attorney" in lowered
        has_chinese_limit = "不构成" in disclaimer or "律师" in disclaimer or "法律意见" in disclaimer
        status = "pass" if disclaimer and has_ai and (has_legal_limit or has_chinese_limit) else "fail"
        return _evaluation(
            "disclaimer",
            status,
            evidence={"has_disclaimer": bool(disclaimer), "has_ai_marker": has_ai},
        )


def _evaluation(gate_id: str, status: str, *, evidence: dict[str, Any]) -> dict[str, Any]:
    rule = next(rule for rule in GATE_RULES if rule.gate_id == gate_id)
    return {
        "gate_id": gate_id,
        "status": status,
        "severity": rule.severity,
        "description": rule.description,
        "evidence": evidence,
    }


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


def _risk_id(item: dict[str, Any]) -> str:
    return _text(item.get("risk_id")) or _text(item.get("title")) or "unknown-risk"


def _risk_level(value: Any) -> str:
    raw = _text(value).lower()
    if raw in {"critical", "major", "severe", "重大", "严重"}:
        return "critical"
    if raw in {"high", "高"}:
        return "high"
    if raw in {"low", "低"}:
        return "low"
    return "medium"


def _is_reviewable_citation(citation: dict[str, Any]) -> bool:
    status = _text(citation.get("verification_status")).lower()
    source_name = _text(citation.get("source_name"))
    source_type = _text(citation.get("source_type"))
    authority = _text(citation.get("authority_level"))
    if "verified" in status or "已校验" in status:
        return True
    return bool(source_name and source_type and authority)
