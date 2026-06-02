"""
Deterministic risk scoring for deep review reports.

The scorer ranks report risks without another model call. It is designed to be
stable enough for regression tests while still exposing the factors that drove a
score so lawyers and operators can audit the ordering.
"""

from __future__ import annotations

from statistics import mean
from typing import Any


LEVEL_SCORES = {
    "critical": 100,
    "high": 78,
    "medium": 52,
    "low": 24,
}

DIMENSION_SCORES = {
    "very_high": 95,
    "high": 78,
    "medium": 52,
    "low": 24,
    "unknown": 45,
}

RISK_WEIGHTS = {
    "level": 0.50,
    "severity": 0.30,
    "probability": 0.20,
}


class RiskScoringService:
    """Score and rank structured risk items in a deep review report."""

    def score_report(self, report: dict[str, Any]) -> dict[str, Any]:
        risk_items = _dicts(report.get("risk_items"))
        matrix_by_id = {
            _risk_id(item, index): item
            for index, item in enumerate(_dicts(report.get("risk_matrix")))
        }

        scored_items = [
            self._score_risk_item(item, matrix_by_id.get(_risk_id(item, index)), index)
            for index, item in enumerate(risk_items)
        ]
        scored_items.sort(
            key=lambda item: (
                -item["score"],
                _safe_int(item.get("source_priority"), 9999),
                item["risk_id"],
            )
        )
        for rank, item in enumerate(scored_items, start=1):
            item["priority_rank"] = rank

        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for item in scored_items:
            counts[item["normalized_level"]] += 1

        scores = [item["score"] for item in scored_items]
        top3 = scores[:3]
        if scores:
            count_pressure = min(12, counts["critical"] * 4 + counts["high"] * 2 + counts["medium"])
            overall_score = round(
                min(
                    100,
                    scores[0] * 0.55
                    + mean(top3) * 0.30
                    + mean(scores) * 0.15
                    + count_pressure,
                )
            )
        else:
            overall_score = 0

        return {
            "schema_version": "risk-scoring-v1",
            "overall_score": overall_score,
            "overall_level": _level_from_score(overall_score),
            "risk_count": len(scored_items),
            "counts": counts,
            "top_risk_ids": [item["risk_id"] for item in scored_items[:5]],
            "score_distribution": {
                "max": max(scores) if scores else 0,
                "average": round(mean(scores), 2) if scores else 0,
                "top3_average": round(mean(top3), 2) if top3 else 0,
            },
            "calibration": {
                "method": "weighted deterministic score",
                "weights": RISK_WEIGHTS,
                "penalties": {
                    "ungrounded": 5,
                    "high_risk_without_reviewable_citation": 4,
                    "missing_revision_plan": 3,
                },
            },
            "risk_scores": scored_items,
        }

    def apply_to_report(self, report: dict[str, Any], scoring: dict[str, Any]) -> dict[str, Any]:
        score_by_id = {
            item["risk_id"]: item
            for item in _dicts(scoring.get("risk_scores"))
            if _text(item.get("risk_id"))
        }

        def enrich(item: dict[str, Any], index: int) -> dict[str, Any]:
            score = score_by_id.get(_risk_id(item, index))
            if not score:
                return item
            item["risk_score"] = score["score"]
            item["risk_score_rank"] = score["priority_rank"]
            item["risk_score_level"] = score["score_level"]
            item["risk_score_explanation"] = score["explanation"]
            item["evidence_confidence_score"] = score["evidence_confidence_score"]
            return item

        risk_items = [enrich(item, index) for index, item in enumerate(_dicts(report.get("risk_items")))]
        report["risk_items"] = sorted(
            risk_items,
            key=lambda item: (_safe_int(item.get("risk_score_rank"), 9999), _safe_int(item.get("priority"), 9999)),
        )

        matrix_items = [enrich(item, index) for index, item in enumerate(_dicts(report.get("risk_matrix")))]
        for item in matrix_items:
            if item.get("risk_score_rank"):
                item["priority"] = item["risk_score_rank"]
        report["risk_matrix"] = sorted(
            matrix_items,
            key=lambda item: (_safe_int(item.get("risk_score_rank"), 9999), _safe_int(item.get("priority"), 9999)),
        )
        return report

    def _score_risk_item(
        self,
        risk: dict[str, Any],
        matrix_item: dict[str, Any] | None,
        index: int,
    ) -> dict[str, Any]:
        merged = {**(matrix_item or {}), **risk}
        risk_id = _risk_id(merged, index)
        level = _risk_level(merged.get("risk_level"))
        severity = _dimension_level(merged.get("severity"))
        probability = _dimension_level(merged.get("probability"))

        level_score = LEVEL_SCORES[level]
        severity_score = DIMENSION_SCORES[severity]
        probability_score = DIMENSION_SCORES[probability]
        base_score = (
            level_score * RISK_WEIGHTS["level"]
            + severity_score * RISK_WEIGHTS["severity"]
            + probability_score * RISK_WEIGHTS["probability"]
        )

        citation_score = _citation_score(merged)
        grounding_score = _grounding_score(merged)
        revision_score = _revision_score(merged)
        evidence_confidence_score = round(
            citation_score * 0.45 + grounding_score * 0.35 + revision_score * 0.20
        )

        penalty = 0
        if grounding_score < 50:
            penalty += 5
        if level in {"critical", "high"} and citation_score < 65:
            penalty += 4
        if revision_score < 50:
            penalty += 3

        score = round(max(0, min(100, base_score - penalty)))
        return {
            "risk_id": risk_id,
            "title": _text(merged.get("title")),
            "normalized_level": level,
            "score": score,
            "score_level": _level_from_score(score),
            "level_score": level_score,
            "severity_score": severity_score,
            "probability_score": probability_score,
            "citation_score": citation_score,
            "grounding_score": grounding_score,
            "revision_score": revision_score,
            "evidence_confidence_score": evidence_confidence_score,
            "penalty": penalty,
            "source_priority": _safe_int(merged.get("priority"), index + 1),
            "explanation": (
                "Weighted by risk level, severity, probability, citation reviewability, "
                "source grounding, and revision-plan completeness."
            ),
        }


def _risk_level(value: Any) -> str:
    raw = _text(value).lower()
    if raw in {
        "critical",
        "major",
        "severe",
        "\u91cd\u5927",
        "\u4e25\u91cd",
        "\u9ad8\u5371",
    }:
        return "critical"
    if raw in {"high", "\u9ad8", "\u8f83\u9ad8"}:
        return "high"
    if raw in {"low", "\u4f4e", "\u8f83\u4f4e"}:
        return "low"
    return "medium"


def _dimension_level(value: Any) -> str:
    raw = _text(value).lower()
    if raw in {"very_high", "very high", "extreme", "\u6781\u9ad8", "\u5f88\u9ad8"}:
        return "very_high"
    if raw in {"high", "\u9ad8", "\u8f83\u9ad8"}:
        return "high"
    if raw in {"low", "\u4f4e", "\u8f83\u4f4e"}:
        return "low"
    if raw in {"medium", "\u4e2d", "\u4e00\u822c"}:
        return "medium"
    return "unknown"


def _citation_score(item: dict[str, Any]) -> int:
    citations = _dicts(item.get("citations"))
    if not citations:
        return 20
    best = 40
    for citation in citations:
        status = _text(citation.get("verification_status")).lower()
        has_reviewable_fields = bool(
            _text(citation.get("source_name"))
            and _text(citation.get("source_type"))
            and _text(citation.get("authority_level"))
        )
        confidence = _safe_int(citation.get("confidence"), 0)
        if (
            "verified" in status
            or "\u5df2\u6821\u9a8c" in status
            or "\u5df2\u6838\u9a8c" in status
        ):
            best = max(best, 100 if confidence >= 80 else 92)
        elif has_reviewable_fields:
            best = max(best, 75)
        elif _text(citation.get("source_name")):
            best = max(best, 55)
    return best


def _grounding_score(item: dict[str, Any]) -> int:
    original = item.get("original_clause") if isinstance(item.get("original_clause"), dict) else {}
    has_original_text = bool(_text(original.get("text")) or _text(original.get("original_text")))
    has_location = bool(
        _text(original.get("clause_number"))
        or _text(item.get("clause_reference"))
        or _text(item.get("issue_location"))
    )
    if has_original_text and has_location:
        return 100
    if has_original_text or has_location:
        return 72
    return 25


def _revision_score(item: dict[str, Any]) -> int:
    revision = item.get("revision_plan") if isinstance(item.get("revision_plan"), dict) else {}
    strong_keys = ("conservative_clause", "balanced_clause", "bottom_line_clause", "negotiation_strategy")
    has_strong_revision = any(bool(_text(revision.get(key))) for key in strong_keys)
    has_action_list = any(_has_content(revision.get(key)) for key in ("delete", "add", "replace"))
    if has_strong_revision and has_action_list:
        return 100
    if has_strong_revision:
        return 85
    if has_action_list:
        return 65
    return 25


def _has_content(value: Any) -> bool:
    if isinstance(value, list):
        return any(bool(_text(item)) for item in value)
    return bool(_text(value))


def _level_from_score(score: int | float) -> str:
    if score >= 88:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _risk_id(item: dict[str, Any], index: int) -> str:
    return _text(item.get("risk_id")) or _text(item.get("risk_no")) or f"R-{index + 1:03d}"


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


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default
