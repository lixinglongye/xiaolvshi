"""
Deterministic citation and legal-source audit for deep review reports.

The audit checks whether legal sources are present, reviewable, connected back
to risk items, and strong enough for high-risk findings. It does not validate
the legal conclusion itself.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


class CitationAuditService:
    """Audit citation coverage and source reviewability in a report."""

    def evaluate(self, report: dict[str, Any]) -> dict[str, Any]:
        risk_items = _dicts(report.get("risk_items"))
        appendix = _dicts(report.get("legal_authority_appendix"))
        appendix_ids = [_source_id(item, index) for index, item in enumerate(appendix)]
        appendix_id_set = set(appendix_ids)
        appendix_by_id = {source_id: source for source_id, source in zip(appendix_ids, appendix)}
        duplicate_source_ids = sorted(source_id for source_id, count in Counter(appendix_ids).items() if count > 1)

        citations_by_risk: dict[str, list[dict[str, Any]]] = {}
        cited_source_ids: set[str] = set()
        citation_count = 0
        for index, risk in enumerate(risk_items):
            risk_id = _risk_id(risk, index)
            citations = _dicts(risk.get("citations"))
            citations_by_risk[risk_id] = citations
            citation_count += len(citations)
            for citation in citations:
                source_id = _text(citation.get("source_id"))
                if source_id:
                    cited_source_ids.add(source_id)

        missing_appendix_source_ids = sorted(cited_source_ids - appendix_id_set)
        orphan_appendix_source_ids = sorted(appendix_id_set - cited_source_ids)

        reviewable_source_ids: list[str] = []
        verified_source_ids: list[str] = []
        weak_source_ids: list[str] = []
        source_type_counts: Counter[str] = Counter()
        authority_counts: Counter[str] = Counter()
        source_quality: list[dict[str, Any]] = []

        for index, source in enumerate(appendix):
            source_id = _source_id(source, index)
            source_type = _source_type(source.get("source_type"))
            source_type_counts[source_type] += 1
            authority = _text(source.get("authority_level")) or "unknown"
            authority_counts[authority] += 1

            reviewable = _is_reviewable_source(source)
            verified = _is_verified(source)
            if reviewable:
                reviewable_source_ids.append(source_id)
            else:
                weak_source_ids.append(source_id)
            if verified:
                verified_source_ids.append(source_id)

            source_quality.append(
                {
                    "source_id": source_id,
                    "source_name": _text(source.get("source_name")),
                    "source_type": source_type,
                    "authority_level": authority,
                    "verification_status": _text(source.get("verification_status")) or "unknown",
                    "confidence": _safe_int(source.get("confidence"), 0),
                    "reviewable": reviewable,
                    "verified": verified,
                    "cited_by_risks": _list_text(source.get("cited_by_risks")),
                }
            )

        high_risk_without_reviewable_citation = []
        high_risk_without_verified_citation = []
        risks_without_any_citation = []
        for index, risk in enumerate(risk_items):
            risk_id = _risk_id(risk, index)
            citations = citations_by_risk.get(risk_id, [])
            if not citations:
                risks_without_any_citation.append(risk_id)
            if _risk_level(risk.get("risk_level")) not in {"critical", "high"}:
                continue
            resolved_citations = [_resolve_citation(citation, appendix_by_id) for citation in citations]
            if not any(_is_reviewable_source(citation) for citation in resolved_citations):
                high_risk_without_reviewable_citation.append(risk_id)
            if not any(_is_verified(citation) for citation in resolved_citations):
                high_risk_without_verified_citation.append(risk_id)

        source_count = len(appendix)
        risk_count = len(risk_items)
        cited_risk_count = sum(1 for citations in citations_by_risk.values() if citations)
        verified_ratio = round(len(verified_source_ids) / source_count, 2) if source_count else 0
        reviewable_ratio = round(len(reviewable_source_ids) / source_count, 2) if source_count else 0
        risk_citation_coverage = round(cited_risk_count / risk_count, 2) if risk_count else 0

        score = self._score(
            source_count=source_count,
            verified_ratio=verified_ratio,
            reviewable_ratio=reviewable_ratio,
            risk_citation_coverage=risk_citation_coverage,
            high_risk_without_reviewable_citation=high_risk_without_reviewable_citation,
            missing_appendix_source_ids=missing_appendix_source_ids,
            weak_source_ids=weak_source_ids,
            duplicate_source_ids=duplicate_source_ids,
        )
        status = self._status(
            source_count=source_count,
            high_risk_without_reviewable_citation=high_risk_without_reviewable_citation,
            weak_source_ids=weak_source_ids,
            missing_appendix_source_ids=missing_appendix_source_ids,
            verified_ratio=verified_ratio,
        )

        return {
            "schema_version": "citation-audit-v1",
            "status": status,
            "score": score,
            "source_count": source_count,
            "citation_count": citation_count,
            "risk_count": risk_count,
            "cited_risk_count": cited_risk_count,
            "verified_source_count": len(verified_source_ids),
            "reviewable_source_count": len(reviewable_source_ids),
            "verified_ratio": verified_ratio,
            "reviewable_ratio": reviewable_ratio,
            "risk_citation_coverage": risk_citation_coverage,
            "source_type_counts": dict(source_type_counts),
            "authority_counts": dict(authority_counts),
            "weak_source_ids": sorted(weak_source_ids),
            "verified_source_ids": sorted(verified_source_ids),
            "reviewable_source_ids": sorted(reviewable_source_ids),
            "high_risk_without_reviewable_citation": high_risk_without_reviewable_citation,
            "high_risk_without_verified_citation": high_risk_without_verified_citation,
            "risks_without_any_citation": risks_without_any_citation,
            "missing_appendix_source_ids": missing_appendix_source_ids,
            "orphan_appendix_source_ids": orphan_appendix_source_ids,
            "duplicate_source_ids": duplicate_source_ids,
            "source_quality": source_quality,
            "recommended_actions": self._actions(
                source_count=source_count,
                high_risk_without_reviewable_citation=high_risk_without_reviewable_citation,
                high_risk_without_verified_citation=high_risk_without_verified_citation,
                weak_source_ids=weak_source_ids,
                missing_appendix_source_ids=missing_appendix_source_ids,
                duplicate_source_ids=duplicate_source_ids,
            ),
        }

    def _score(
        self,
        *,
        source_count: int,
        verified_ratio: float,
        reviewable_ratio: float,
        risk_citation_coverage: float,
        high_risk_without_reviewable_citation: list[str],
        missing_appendix_source_ids: list[str],
        weak_source_ids: list[str],
        duplicate_source_ids: list[str],
    ) -> int:
        if source_count == 0:
            return 0
        score = round(
            verified_ratio * 35
            + reviewable_ratio * 30
            + risk_citation_coverage * 25
            + 10
        )
        score -= len(high_risk_without_reviewable_citation) * 18
        score -= len(missing_appendix_source_ids) * 6
        score -= len(weak_source_ids) * 5
        score -= len(duplicate_source_ids) * 4
        return max(0, min(100, score))

    def _status(
        self,
        *,
        source_count: int,
        high_risk_without_reviewable_citation: list[str],
        weak_source_ids: list[str],
        missing_appendix_source_ids: list[str],
        verified_ratio: float,
    ) -> str:
        if source_count == 0 or high_risk_without_reviewable_citation:
            return "fail"
        if weak_source_ids or missing_appendix_source_ids or verified_ratio < 0.5:
            return "warn"
        return "pass"

    def _actions(
        self,
        *,
        source_count: int,
        high_risk_without_reviewable_citation: list[str],
        high_risk_without_verified_citation: list[str],
        weak_source_ids: list[str],
        missing_appendix_source_ids: list[str],
        duplicate_source_ids: list[str],
    ) -> list[str]:
        actions = []
        if source_count == 0:
            actions.append("Add a legal authority appendix before external delivery.")
        if high_risk_without_reviewable_citation:
            actions.append(
                "Attach reviewable citations to high-risk items: "
                + ", ".join(high_risk_without_reviewable_citation[:8])
            )
        if high_risk_without_verified_citation:
            actions.append(
                "Verify cited authorities for high-risk items: "
                + ", ".join(high_risk_without_verified_citation[:8])
            )
        if weak_source_ids:
            actions.append("Complete source metadata for: " + ", ".join(weak_source_ids[:8]))
        if missing_appendix_source_ids:
            actions.append("Hydrate missing appendix sources: " + ", ".join(missing_appendix_source_ids[:8]))
        if duplicate_source_ids:
            actions.append("Deduplicate appendix source IDs: " + ", ".join(duplicate_source_ids[:8]))
        return actions[:6]


def _source_id(item: dict[str, Any], index: int) -> str:
    return _text(item.get("source_id")) or f"source-{index + 1}"


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


def _source_type(value: Any) -> str:
    raw = _text(value).lower()
    if raw in {"law", "\u6cd5\u5f8b", "LAW".lower()}:
        return "law"
    if raw in {"administrative regulation", "admin_reg", "\u884c\u653f\u6cd5\u89c4"}:
        return "admin_reg"
    if raw in {"judicial interpretation", "judicial_interpretation", "\u53f8\u6cd5\u89e3\u91ca"}:
        return "judicial_interpretation"
    if raw in {"guiding case", "guiding_case", "\u6307\u5bfc\u6027\u6848\u4f8b"}:
        return "guiding_case"
    if raw in {"reference case", "reference_case", "\u53c2\u8003\u6848\u4f8b"}:
        return "reference_case"
    if raw in {"judgment", "\u88c1\u5224\u6587\u4e66"}:
        return "judgment"
    if raw in {"template", "checklist", "\u5b9e\u52a1\u6e05\u5355", "\u5b9e\u52a1\u6a21\u677f"}:
        return "practice_reference"
    return raw or "unknown"


def _is_reviewable_source(source: dict[str, Any]) -> bool:
    return bool(
        _text(source.get("source_name"))
        and _text(source.get("source_type"))
        and _text(source.get("authority_level"))
    )


def _is_verified(source: dict[str, Any]) -> bool:
    status = _text(source.get("verification_status")).lower()
    if "verified" in status or "\u5df2\u6821\u9a8c" in status or "\u5df2\u6838\u9a8c" in status:
        return True
    confidence = _safe_int(source.get("confidence"), 0)
    return confidence >= 85 and _is_reviewable_source(source)


def _resolve_citation(citation: dict[str, Any], appendix_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_id = _text(citation.get("source_id"))
    appendix_source = appendix_by_id.get(source_id, {})
    return {**appendix_source, **citation}


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


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default
