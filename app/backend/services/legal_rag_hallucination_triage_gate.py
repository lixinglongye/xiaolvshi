from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_authority_citation_gate import LegalRagAuthorityCitationGateService
from services.legal_rag_failure_fixtures import LegalRagFailureFixturesService


SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


class LegalRagHallucinationTriageGateService:
    """Build a metadata-only triage gate for Legal RAG hallucination risks."""

    def __init__(
        self,
        *,
        fixture_service: LegalRagFailureFixturesService | None = None,
        authority_gate_service: LegalRagAuthorityCitationGateService | None = None,
    ) -> None:
        self.fixture_service = fixture_service or LegalRagFailureFixturesService()
        self.authority_gate_service = authority_gate_service or LegalRagAuthorityCitationGateService()

    def build_gate(self) -> dict[str, Any]:
        fixture_suite = self.fixture_service.build_suite()
        authority_gate = self.authority_gate_service.build_gate()
        taxonomy = {item["id"]: item for item in fixture_suite["failure_taxonomy"]}
        rows = [
            self._triage_row(case, taxonomy, authority_gate)
            for case in fixture_suite["fixture_cases"]
        ]
        severity_counts = Counter(row["severity"] for row in rows)
        label_counts = Counter(label for row in rows for label in row["failure_labels"])
        blocker_rows = [row for row in rows if row["block_release"]]

        return {
            "id": "legal-rag-hallucination-triage-gate",
            "status": "ready_with_blockers" if blocker_rows else "ready",
            "title": "Legal RAG hallucination triage gate",
            "summary": {
                "triage_row_count": len(rows),
                "fixture_case_count": fixture_suite["summary"]["fixture_case_count"],
                "taxonomy_count": fixture_suite["summary"]["taxonomy_count"],
                "blocker_row_count": len(blocker_rows),
                "critical_row_count": severity_counts.get("critical", 0),
                "high_row_count": severity_counts.get("high", 0),
                "medium_row_count": severity_counts.get("medium", 0),
                "failure_label_count": len(label_counts),
                "authority_gate_status": authority_gate["status"],
                "citation_mismatch_count": authority_gate["summary"]["citation_mismatch_count"],
                "retrieval_gap_count": authority_gate["summary"]["retrieval_gap_count"],
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "raw_retrieved_context_included": False,
                "raw_legal_text_included": False,
                "prompt_included": False,
                "model_output_included": False,
                "credentials_included": False,
            },
            "triage_rows": rows,
            "failure_label_counts": dict(sorted(label_counts.items())),
            "severity_counts": dict(sorted(severity_counts.items())),
            "research_basis": [
                {
                    "id": "ragas",
                    "url": "https://arxiv.org/abs/2309.15217",
                    "signal": "Track answer faithfulness and context relevance before trusting generated answers.",
                },
                {
                    "id": "crag",
                    "url": "https://arxiv.org/abs/2406.04744",
                    "signal": "Use retrieval-failure and factual QA style checks as release blockers, not only aggregate scores.",
                },
                {
                    "id": "stanford-legal-hallucination",
                    "url": "https://reglab.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/",
                    "signal": "Legal research tools need hallucination-aware citation and professional-review gates.",
                },
                {
                    "id": "legal-rag-bench",
                    "url": "https://arxiv.org/abs/2408.10343",
                    "signal": "Legal RAG evaluation should distinguish hallucinated law, unsupported conclusions, and retrieval gaps.",
                },
            ],
            "release_policy": {
                "default_action": "block_client_delivery_until_triage_rows_are_resolved",
                "allowed_without_lawyer_review": [],
                "requires_lawyer_review": [
                    "missing_citation",
                    "stale_regulation",
                    "jurisdiction_mismatch",
                    "unsupported_conclusion",
                    "hallucinated_article",
                    "conflicting_facts",
                ],
                "linked_gate_ids": [
                    "legal-rag-failure-fixtures",
                    "legal-rag-authority-citation-gate",
                    "legal-rag-selected-source-citation-validation",
                    "legal-rag-evaluation",
                    "legal-grounding-quick-audit",
                    "case-export-readiness",
                ],
            },
            "claim_boundary": {
                "hallucination_free_claimed": False,
                "legal_answer_accuracy_claimed": False,
                "public_benchmark_score_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_client_delivery_claimed": False,
                "allowed_claims": [
                    "Metadata-only hallucination triage coverage exists for local synthetic failure modes.",
                    "The gate maps deterministic failure labels to reviewer actions and release blockers.",
                ],
                "forbidden_claims": [
                    "Do not claim hallucination-free legal answers.",
                    "Do not claim Legal RAG Bench, LegalBench, RAGAS, or CRAG benchmark scores.",
                    "Do not claim live NewAPI/Gemini execution or production accuracy.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_user_question": False,
                "returns_retrieved_context": False,
                "returns_unsafe_answer": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "network_called": False,
                "dataset_downloaded": False,
            },
            "recommended_actions": self._recommended_actions(blocker_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_hallucination_triage_gate.py tests/test_legal_rag_failure_fixtures.py tests/test_legal_rag_authority_citation_gate.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _triage_row(
        self,
        case: dict[str, Any],
        taxonomy: dict[str, dict[str, Any]],
        authority_gate: dict[str, Any],
    ) -> dict[str, Any]:
        labels = list(case["expected_failure_labels"])
        taxonomy_items = [taxonomy[label] for label in labels if label in taxonomy]
        severity = self._highest_severity(taxonomy_items)
        reviewer_actions = self._unique(
            [item["reviewer_action"] for item in taxonomy_items]
            + list(case["acceptable_actions"])
        )
        related_authority_rows = self._related_authority_rows(labels, authority_gate)
        return {
            "case_id": case["id"],
            "title": case["title"],
            "scenario": case["scenario"],
            "severity": severity,
            "failure_labels": labels,
            "evidence_signals": list(case["expected_evidence_signals"]),
            "reviewer_actions": reviewer_actions,
            "release_action": "block_client_delivery" if severity in {"critical", "high"} else "lawyer_review_required",
            "block_release": severity in {"critical", "high"},
            "linked_authority_row_ids": related_authority_rows,
            "linked_gate_ids": [
                "legal-rag-failure-fixtures",
                "legal-rag-authority-citation-gate",
                "legal-grounding-quick-audit",
            ],
            "privacy_boundary": {
                "user_question_returned": False,
                "retrieved_context_returned": False,
                "unsafe_answer_returned": False,
                "raw_legal_text_returned": False,
            },
        }

    def _highest_severity(self, taxonomy_items: list[dict[str, Any]]) -> str:
        if not taxonomy_items:
            return "medium"
        return max(
            (str(item.get("severity") or "medium") for item in taxonomy_items),
            key=lambda severity: SEVERITY_ORDER.get(severity, 0),
        )

    def _related_authority_rows(self, labels: list[str], authority_gate: dict[str, Any]) -> list[str]:
        rows = authority_gate.get("source_rows") or []
        linked: list[str] = []
        if any(label in labels for label in ("missing_citation", "hallucinated_article")):
            linked.extend(
                row["id"]
                for row in rows
                if int(row.get("citation_mismatch_count") or 0) > 0
            )
        if any(label in labels for label in ("stale_regulation", "jurisdiction_mismatch")):
            linked.extend(
                row["id"]
                for row in rows
                if row.get("freshness_status") in {"stale", "review_due", "unknown"}
            )
        if "unsupported_conclusion" in labels:
            linked.extend(
                row["id"]
                for row in rows
                if int(row.get("retrieval_gap_count") or 0) > 0
            )
        return self._unique(linked)

    def _recommended_actions(self, blocker_rows: list[dict[str, Any]]) -> list[str]:
        if blocker_rows:
            return [
                "Keep Legal RAG outputs review-required until every critical or high hallucination triage row has a reviewer action.",
                "Use local failure fixtures before broadening retrieval sources or changing cheap-first Gemini/NewAPI routes.",
                "Attach selected-source validation, authority/citation gate evidence, and grounding quick-audit results before client delivery.",
            ]
        return [
            "Maintain hallucination triage evidence on each release candidate.",
            "Re-run local failure fixtures before source-index or model-routing changes.",
        ]

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            safe = str(value or "").strip()
            if safe and safe not in seen:
                seen.add(safe)
                result.append(safe)
        return result
