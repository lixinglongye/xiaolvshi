from __future__ import annotations

from typing import Any


METRIC_WEIGHTS = {
    "retrieval_recall": 30,
    "citation_precision": 25,
    "claim_verification": 25,
    "source_freshness": 10,
    "privacy_safety": 10,
}


class LegalRagEvaluationService:
    """Scores legal RAG runs on retrieval, citation, verification, and safety."""

    def policy(self) -> dict[str, Any]:
        return {
            "status_thresholds": {
                "pass": 85,
                "warn": 65,
                "fail": 0,
            },
            "metric_weights": METRIC_WEIGHTS,
            "required_metrics": [
                "retrieval_recall",
                "citation_precision",
                "claim_verification",
                "source_freshness",
                "privacy_safety",
            ],
            "blocking_conditions": [
                "Any unsupported critical legal claim",
                "Answer has no cited legal source IDs when sources are expected",
                "Citation precision below 60%",
                "Retrieval recall below 50% for expected sources",
                "PII finding marked critical",
            ],
            "evaluation_inputs": [
                "expected_source_ids",
                "retrieved_source_ids",
                "answer_citation_source_ids",
                "verified_claim_count",
                "total_claim_count",
                "unsupported_claims",
                "stale_source_ids",
                "pii_findings",
            ],
        }

    def evaluate(self, run: dict[str, Any] | None = None) -> dict[str, Any]:
        run = run or {}
        expected_sources = _set_text(run.get("expected_source_ids"))
        retrieved_sources = _set_text(run.get("retrieved_source_ids"))
        citation_sources = _set_text(run.get("answer_citation_source_ids"))
        stale_sources = _set_text(run.get("stale_source_ids"))
        unsupported_claims = _list_dict(run.get("unsupported_claims"))
        pii_findings = _list_dict(run.get("pii_findings"))

        retrieval_recall = _ratio(len(expected_sources & retrieved_sources), len(expected_sources), default=1.0)
        citations_required = bool(expected_sources or retrieved_sources)
        missing_answer_citations = citations_required and not citation_sources
        citation_precision = (
            0.0
            if missing_answer_citations
            else _ratio(len(citation_sources & retrieved_sources), len(citation_sources), default=1.0)
        )
        verified_claim_count = _safe_int(run.get("verified_claim_count"), 0)
        total_claim_count = _safe_int(run.get("total_claim_count"), verified_claim_count)
        claim_verification = _ratio(verified_claim_count, total_claim_count, default=1.0)
        source_freshness = 1.0 - _ratio(len(stale_sources), max(len(retrieved_sources), len(stale_sources)), default=0.0)
        privacy_safety = 0.0 if any(_text(item.get("severity")).lower() == "critical" for item in pii_findings) else 1.0

        metric_scores = {
            "retrieval_recall": round(retrieval_recall, 3),
            "citation_precision": round(citation_precision, 3),
            "claim_verification": round(claim_verification, 3),
            "source_freshness": round(source_freshness, 3),
            "privacy_safety": round(privacy_safety, 3),
        }
        score = self._weighted_score(metric_scores)
        blockers = self._blockers(metric_scores, unsupported_claims, pii_findings, missing_answer_citations)
        status = self._status(score, blockers)

        return {
            "status": status,
            "score": score,
            "metric_scores": metric_scores,
            "blocking_reasons": blockers,
            "recommended_actions": self._recommended_actions(
                metric_scores,
                blockers,
                unsupported_claims,
                stale_sources,
                missing_answer_citations,
            ),
            "coverage": {
                "expected_source_count": len(expected_sources),
                "retrieved_source_count": len(retrieved_sources),
                "citation_source_count": len(citation_sources),
                "citations_required": citations_required,
                "missing_answer_citations": missing_answer_citations,
                "missing_answer_citation_source_ids": sorted(retrieved_sources or expected_sources)
                if missing_answer_citations
                else [],
                "missing_expected_source_ids": sorted(expected_sources - retrieved_sources),
                "uncited_retrieved_source_ids": sorted(retrieved_sources - citation_sources),
            },
        }

    def _weighted_score(self, metric_scores: dict[str, float]) -> int:
        total = 0.0
        for metric, weight in METRIC_WEIGHTS.items():
            total += metric_scores.get(metric, 0.0) * weight
        return round(total)

    def _blockers(
        self,
        metric_scores: dict[str, float],
        unsupported_claims: list[dict[str, Any]],
        pii_findings: list[dict[str, Any]],
        missing_answer_citations: bool,
    ) -> list[str]:
        blockers: list[str] = []
        if any(_text(item.get("severity")).lower() in {"critical", "high"} for item in unsupported_claims):
            blockers.append("Unsupported high-impact legal claim.")
        if missing_answer_citations:
            blockers.append("Answer has no cited legal source IDs when sources are expected.")
        elif metric_scores["citation_precision"] < 0.60:
            blockers.append("Citation precision is below 60%.")
        if metric_scores["retrieval_recall"] < 0.50:
            blockers.append("Retrieval recall is below 50% for expected sources.")
        if any(_text(item.get("severity")).lower() == "critical" for item in pii_findings):
            blockers.append("Critical PII finding requires remediation.")
        return blockers

    def _status(self, score: int, blockers: list[str]) -> str:
        if blockers:
            return "fail"
        if score >= 85:
            return "pass"
        if score >= 65:
            return "warn"
        return "fail"

    def _recommended_actions(
        self,
        metric_scores: dict[str, float],
        blockers: list[str],
        unsupported_claims: list[dict[str, Any]],
        stale_sources: set[str],
        missing_answer_citations: bool,
    ) -> list[str]:
        actions: list[str] = []
        if metric_scores["retrieval_recall"] < 0.85:
            actions.append("Improve retrieval source recovery before relying on the generated answer.")
        if missing_answer_citations:
            actions.append("Add answer citation source IDs for the retrieved legal sources before release.")
        if metric_scores["citation_precision"] < 0.90:
            actions.append("Verify every cited source ID against retrieved legal sources.")
        if metric_scores["claim_verification"] < 0.90 or unsupported_claims:
            actions.append("Run post-generation claim verification and remove unsupported legal conclusions.")
        if stale_sources:
            actions.append(f"Refresh stale legal sources: {', '.join(sorted(stale_sources))}.")
        if any("PII" in reason for reason in blockers):
            actions.append("Scrub sensitive personal data before storing or sharing evaluation artifacts.")
        if not actions:
            actions.append("RAG run is ready for legal reviewer spot-check.")
        return actions


def _set_text(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {_text(item) for item in value if _text(item)}


def _list_dict(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ratio(numerator: int, denominator: int, *, default: float) -> float:
    if denominator <= 0:
        return default
    return max(0.0, min(1.0, numerator / denominator))
