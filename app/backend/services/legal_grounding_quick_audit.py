from __future__ import annotations

from typing import Any

from services.citation_audit import CitationAuditService
from services.evidence_audit import EvidenceAuditService
from services.legal_rag_evaluation import LegalRagEvaluationService


class LegalGroundingQuickAuditService:
    """Combine citation, evidence, and RAG signals into a low-resource grounding audit."""

    def __init__(
        self,
        citation_service: CitationAuditService | None = None,
        evidence_service: EvidenceAuditService | None = None,
        rag_service: LegalRagEvaluationService | None = None,
    ) -> None:
        self.citation_service = citation_service or CitationAuditService()
        self.evidence_service = evidence_service or EvidenceAuditService()
        self.rag_service = rag_service or LegalRagEvaluationService()

    def policy(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "method": {
                "type": "legal-grounding-quick-audit-policy",
                "notes": [
                    "Runs deterministic checks only; no model, gateway, search, or dataset download is required.",
                    "Combines legal citation reviewability, evidence-plan completeness, and RAG grounding metrics.",
                    "Uses explicit rag_run metrics when supplied, otherwise infers a conservative local RAG run from report sources.",
                    "Treats unsupported high-impact claims, missing high-risk citations, and missing high-risk evidence plans as blockers.",
                ],
                "research_basis": [
                    {
                        "id": "legalbench",
                        "url": "https://arxiv.org/abs/2308.11462",
                        "signal": "Cover multiple legal reasoning and evidence task families instead of one generic QA score.",
                    },
                    {
                        "id": "ragas",
                        "url": "https://arxiv.org/abs/2309.15217",
                        "signal": "Track faithfulness, answer relevance, and context/source relevance for generated answers.",
                    },
                    {
                        "id": "crag",
                        "url": "https://arxiv.org/abs/2406.04744",
                        "signal": "Use factual QA and retrieval-style benchmark signals for grounded generation reliability.",
                    },
                ],
            },
            "component_weights": {
                "citation_audit": 30,
                "evidence_audit": 30,
                "rag_evaluation": 40,
            },
            "status_thresholds": {
                "pass": 85,
                "warn": 70,
                "fail": 0,
            },
            "required_inputs": {
                "report": ["risk_items", "legal_authority_appendix", "professional_review_framework"],
                "optional_rag_run": [
                    "expected_source_ids",
                    "retrieved_source_ids",
                    "answer_citation_source_ids",
                    "verified_claim_count",
                    "total_claim_count",
                    "unsupported_claims",
                    "stale_source_ids",
                    "pii_findings",
                ],
            },
        }

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        report = self._report(payload)
        if not report:
            return self._not_run()

        explicit_rag_run = _dict(payload.get("rag_run"))
        rag_run = explicit_rag_run or self._rag_run_from_report(report)
        citation = self.citation_service.evaluate(report)
        evidence = self.evidence_service.evaluate(report)
        rag = self.rag_service.evaluate(rag_run)
        component_scores = {
            "citation_audit": _safe_int(citation.get("score"), 0),
            "evidence_audit": _safe_int(evidence.get("score"), 0),
            "rag_evaluation": _safe_int(rag.get("score"), 0),
        }
        score = self._weighted_score(component_scores)
        blockers = self._blocking_reasons(citation, evidence, rag)
        warnings = self._warning_reasons(citation, evidence, rag, explicit_rag_run)
        status = self._status(score, blockers, warnings)
        return {
            "status": status,
            "score": score,
            "release_recommendation": self._release_recommendation(status),
            "method": self.policy()["method"],
            "summary": {
                "risk_count": _safe_int(citation.get("risk_count"), 0),
                "source_count": _safe_int(citation.get("source_count"), 0),
                "citation_score": component_scores["citation_audit"],
                "evidence_score": component_scores["evidence_audit"],
                "rag_score": component_scores["rag_evaluation"],
                "blocking_count": len(blockers),
                "warning_count": len(warnings),
                "rag_run_source": "explicit" if explicit_rag_run else "inferred_from_report",
            },
            "component_statuses": {
                "citation_audit": citation.get("status", "unknown"),
                "evidence_audit": evidence.get("status", "unknown"),
                "rag_evaluation": rag.get("status", "unknown"),
            },
            "component_scores": component_scores,
            "blocking_reasons": blockers,
            "warning_reasons": warnings,
            "grounding_gaps": self._grounding_gaps(citation, evidence, rag),
            "citation_audit": citation,
            "evidence_audit": evidence,
            "rag_evaluation": rag,
            "recommended_actions": self._recommended_actions(blockers, warnings, citation, evidence, rag),
            "privacy_note": (
                "The audit evaluates structured report metadata, source IDs, citation links, and optional normalized RAG metrics. "
                "Do not store real client documents, emails, API keys, passwords, or raw model outputs in committed audit artifacts."
            ),
        }

    def _not_run(self) -> dict[str, Any]:
        return {
            "status": "not_run",
            "score": 0,
            "release_recommendation": "submit_report_or_rag_run",
            "method": self.policy()["method"],
            "summary": {
                "risk_count": 0,
                "source_count": 0,
                "citation_score": 0,
                "evidence_score": 0,
                "rag_score": 0,
                "blocking_count": 0,
                "warning_count": 1,
                "rag_run_source": "none",
            },
            "component_statuses": {},
            "component_scores": {},
            "blocking_reasons": [],
            "warning_reasons": ["No report payload was supplied."],
            "grounding_gaps": [],
            "recommended_actions": ["Submit a deep-review report with risk_items and legal_authority_appendix."],
            "privacy_note": "No payload was evaluated.",
        }

    def _report(self, payload: dict[str, Any]) -> dict[str, Any]:
        report = _dict(payload.get("report"))
        if report:
            return report
        if any(key in payload for key in ("risk_items", "legal_authority_appendix", "professional_review_framework")):
            return payload
        return {}

    def _rag_run_from_report(self, report: dict[str, Any]) -> dict[str, Any]:
        appendix = _dicts(report.get("legal_authority_appendix"))
        risk_items = _dicts(report.get("risk_items"))
        expected_source_ids = [_source_id(source, index) for index, source in enumerate(appendix)]
        citation_source_ids = []
        cited_risk_count = 0
        verified_risk_count = 0
        for risk in risk_items:
            citations = _dicts(risk.get("citations"))
            if citations:
                cited_risk_count += 1
            citation_source_ids.extend(_text(citation.get("source_id")) for citation in citations if _text(citation.get("source_id")))
            if citations and _evidence_suggestions(risk):
                verified_risk_count += 1
        stale_source_ids = [
            _source_id(source, index)
            for index, source in enumerate(appendix)
            if _is_stale_source(source)
        ]
        pii_findings = _dicts(report.get("pii_findings"))
        privacy_scan = _dict(report.get("privacy_scan"))
        pii_findings.extend(_dicts(privacy_scan.get("findings")))
        return {
            "expected_source_ids": expected_source_ids,
            "retrieved_source_ids": expected_source_ids,
            "answer_citation_source_ids": sorted(set(citation_source_ids)),
            "verified_claim_count": verified_risk_count or cited_risk_count,
            "total_claim_count": len(risk_items),
            "unsupported_claims": _dicts(report.get("unsupported_claims")),
            "stale_source_ids": stale_source_ids,
            "pii_findings": pii_findings,
        }

    def _weighted_score(self, scores: dict[str, int]) -> int:
        weights = self.policy()["component_weights"]
        total = sum(scores[key] * weight for key, weight in weights.items())
        return round(total / max(1, sum(weights.values())))

    def _blocking_reasons(self, citation: dict[str, Any], evidence: dict[str, Any], rag: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        if citation.get("status") == "fail":
            reasons.append("Citation audit failed: high-risk findings lack reviewable legal citations.")
        if evidence.get("status") == "fail":
            reasons.append("Evidence audit failed: high-risk findings lack evidence plans.")
        reasons.extend(_list_text(rag.get("blocking_reasons")))
        return _unique(reasons)

    def _warning_reasons(
        self,
        citation: dict[str, Any],
        evidence: dict[str, Any],
        rag: dict[str, Any],
        explicit_rag_run: dict[str, Any],
    ) -> list[str]:
        reasons: list[str] = []
        if citation.get("status") == "warn":
            reasons.append("Citation audit needs source verification or appendix cleanup.")
        if evidence.get("status") == "warn":
            reasons.append("Evidence audit needs pending-fact or proof-plan follow-up.")
        if rag.get("status") == "warn":
            reasons.append("RAG evaluation score is below pass threshold.")
        if not explicit_rag_run:
            reasons.append("RAG metrics were inferred from report metadata; run explicit RAG evaluation before public release.")
        return _unique(reasons)

    def _status(self, score: int, blockers: list[str], warnings: list[str]) -> str:
        if blockers:
            return "fail"
        if score >= 85 and not warnings:
            return "pass"
        if score >= 70:
            return "warn"
        return "fail"

    def _release_recommendation(self, status: str) -> str:
        if status == "pass":
            return "ready_for_lawyer_spot_check"
        if status == "warn":
            return "review_grounding_warnings_before_release"
        if status == "not_run":
            return "submit_report_or_rag_run"
        return "block_release_until_grounding_gaps_are_fixed"

    def _grounding_gaps(self, citation: dict[str, Any], evidence: dict[str, Any], rag: dict[str, Any]) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        for risk_id in _list_text(citation.get("high_risk_without_reviewable_citation")):
            gaps.append({"type": "missing_reviewable_citation", "target": risk_id, "severity": "blocker"})
        for risk_id in _list_text(evidence.get("high_risk_without_evidence_plan")):
            gaps.append({"type": "missing_evidence_plan", "target": risk_id, "severity": "blocker"})
        for source_id in _list_text(rag.get("coverage", {}).get("missing_expected_source_ids") if isinstance(rag.get("coverage"), dict) else []):
            gaps.append({"type": "missing_expected_source", "target": source_id, "severity": "blocker"})
        for source_id in _list_text(citation.get("weak_source_ids")):
            gaps.append({"type": "weak_source_metadata", "target": source_id, "severity": "warning"})
        for fact_id in _list_text(evidence.get("blocking_pending_fact_ids")):
            gaps.append({"type": "blocking_pending_fact", "target": fact_id, "severity": "warning"})
        return gaps[:20]

    def _recommended_actions(
        self,
        blockers: list[str],
        warnings: list[str],
        citation: dict[str, Any],
        evidence: dict[str, Any],
        rag: dict[str, Any],
    ) -> list[str]:
        actions = []
        actions.extend(_list_text(citation.get("recommended_actions")))
        actions.extend(_list_text(evidence.get("recommended_actions")))
        actions.extend(_list_text(rag.get("recommended_actions")))
        if blockers:
            actions.insert(0, "Block release until citation, evidence, and unsupported-claim gaps are fixed.")
        elif warnings:
            actions.insert(0, "Run explicit RAG evaluation and lawyer spot-check before treating this report as release evidence.")
        else:
            actions.insert(0, "Grounding audit is ready for lawyer spot-check evidence.")
        return _unique(actions)[:8]


def _source_id(item: dict[str, Any], index: int) -> str:
    return _text(item.get("source_id")) or f"source-{index + 1}"


def _evidence_suggestions(risk: dict[str, Any]) -> list[str]:
    analysis = risk.get("legal_analysis") if isinstance(risk.get("legal_analysis"), dict) else {}
    suggestions = _list_text(analysis.get("evidence_suggestion"))
    suggestions.extend(_list_text(risk.get("evidence_suggestions")))
    return suggestions


def _is_stale_source(source: dict[str, Any]) -> bool:
    blob = " ".join(
        _text(source.get(key)).lower()
        for key in ("verification_status", "freshness_status", "status", "notes")
    )
    return any(marker in blob for marker in ("stale", "outdated", "expired", "\u8fc7\u671f", "\u5931\u6548"))


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _unique(items: list[str]) -> list[str]:
    seen = set()
    unique = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique
