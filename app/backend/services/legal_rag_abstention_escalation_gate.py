from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_authority_citation_gate import LegalRagAuthorityCitationGateService
from services.legal_rag_hallucination_triage_gate import LegalRagHallucinationTriageGateService
from services.model_escalation_policy import ModelEscalationPolicyService


ANSWER_MODES = (
    "answer",
    "answer_with_warning",
    "abstain",
    "ask_clarification",
    "lawyer_review",
    "premium_exception",
)


class LegalRagAbstentionEscalationGateService:
    """Join Legal RAG quality gates into answer/abstain/escalation decisions."""

    def __init__(
        self,
        *,
        hallucination_gate_service: LegalRagHallucinationTriageGateService | None = None,
        authority_gate_service: LegalRagAuthorityCitationGateService | None = None,
        model_escalation_service: ModelEscalationPolicyService | None = None,
    ) -> None:
        self.authority_gate_service = authority_gate_service or LegalRagAuthorityCitationGateService()
        self.hallucination_gate_service = (
            hallucination_gate_service
            or LegalRagHallucinationTriageGateService(
                authority_gate_service=self.authority_gate_service
            )
        )
        self.model_escalation_service = model_escalation_service or ModelEscalationPolicyService()

    def build_gate(self) -> dict[str, Any]:
        hallucination_gate = self.hallucination_gate_service.build_gate()
        authority_gate = self.authority_gate_service.build_gate()
        model_policy = self.model_escalation_service.build_policy()
        rows = [
            self._decision_row(row, authority_gate)
            for row in hallucination_gate.get("triage_rows", [])
        ]
        rows.append(self._ready_answer_row(authority_gate))

        mode_counts = Counter(row["answer_mode"] for row in rows)
        blocker_rows = [
            row
            for row in rows
            if row["release_action"] not in {"allow_answer", "allow_answer_with_warning"}
        ]
        hallucination_blockers = [
            row for row in rows if "legal-rag-hallucination-triage-gate" in row["linked_gate_ids"] and row["block_release"]
        ]
        authority_blockers = [
            row for row in rows if row["authority_gate_status"] in {"blocked", "review_required"}
        ]
        evidence_scores = [int(row["evidence_sufficiency_score"]) for row in rows]

        return {
            "id": "legal-rag-abstention-escalation-gate",
            "status": "ready_with_blockers" if blocker_rows else "ready",
            "title": "Legal RAG abstention escalation gate",
            "summary": {
                "decision_row_count": len(rows),
                "answer_count": mode_counts.get("answer", 0),
                "answer_with_warning_count": mode_counts.get("answer_with_warning", 0),
                "abstain_count": mode_counts.get("abstain", 0),
                "ask_clarification_count": mode_counts.get("ask_clarification", 0),
                "lawyer_review_count": mode_counts.get("lawyer_review", 0),
                "premium_exception_count": mode_counts.get("premium_exception", 0),
                "cheap_first_count": sum(1 for row in rows if row["cheap_first_route"]["starts_cheap"]),
                "blocker_count": len(blocker_rows),
                "hallucination_blocker_count": len(hallucination_blockers),
                "authority_blocker_count": len(authority_blockers),
                "insufficient_evidence_count": sum(
                    1 for row in rows if row["evidence_sufficiency_status"] == "insufficient"
                ),
                "warning_evidence_count": sum(
                    1 for row in rows if row["evidence_sufficiency_status"] == "warning"
                ),
                "min_evidence_sufficiency_score": min(evidence_scores) if evidence_scores else 0,
                "hallucination_gate_status": hallucination_gate["status"],
                "authority_gate_status": authority_gate["status"],
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
            "answer_modes": {
                mode: self._mode_definition(mode)
                for mode in ANSWER_MODES
            },
            "decision_rows": rows,
            "escalation_policy": {
                "default_model_strategy": "cheap_first_metadata_only",
                "model_policy_status": model_policy["status"],
                "cheap_first_allowed_modes": ["answer", "answer_with_warning", "ask_clarification"],
                "balanced_precheck_modes": ["lawyer_review"],
                "premium_exception_modes": ["premium_exception"],
                "abstain_modes": ["abstain"],
                "gateway_call_allowed": False,
                "config_write_allowed": False,
                "operator_approval_required_for_premium": True,
                "linked_model_policy_tasks": model_policy["coverage"]["tasks"],
            },
            "linked_gate_summary": {
                "hallucination_gate_id": hallucination_gate["id"],
                "authority_gate_id": authority_gate["id"],
                "hallucination_triage_rows": hallucination_gate["summary"]["triage_row_count"],
                "authority_review_rows": authority_gate["summary"]["authority_review_count"],
                "citation_mismatch_count": authority_gate["summary"]["citation_mismatch_count"],
                "retrieval_gap_count": authority_gate["summary"]["retrieval_gap_count"],
            },
            "research_basis": [
                {
                    "id": "ragas",
                    "url": "https://arxiv.org/abs/2309.15217",
                    "signal": "Treat faithfulness and context relevance as answer-release gates instead of trusting generated text alone.",
                },
                {
                    "id": "self-rag",
                    "url": "https://arxiv.org/abs/2310.11511",
                    "signal": "Reflection-style retrieval checks motivate explicit decisions to retrieve, critique, answer, or withhold.",
                },
                {
                    "id": "crag",
                    "url": "https://arxiv.org/abs/2401.15884",
                    "signal": "Corrective RAG highlights routing when retrieval confidence is low or inconsistent.",
                },
                {
                    "id": "stanford-legal-hallucination",
                    "url": "https://reglab.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/",
                    "signal": "Legal tools need hallucination-aware professional review instead of unsupported accuracy claims.",
                },
            ],
            "claim_boundary": {
                "legal_advice_claimed": False,
                "hallucination_free_claimed": False,
                "public_benchmark_score_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_client_delivery_claimed": False,
                "allowed_claims": [
                    "The repository now exposes metadata-only answer, abstention, clarification, lawyer-review, and premium-exception routing evidence.",
                    "The gate joins local hallucination triage and authority/citation checks without running a model.",
                ],
                "forbidden_claims": [
                    "Do not claim legal-answer accuracy or hallucination-free production behavior.",
                    "Do not claim public RAGAS, CRAG, LegalBench, or Legal RAG benchmark scores.",
                    "Do not claim live NewAPI/Gemini execution or client-deliverable advice.",
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
                "returns_gateway_payloads": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(blocker_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_abstention_escalation_gate.py tests/test_legal_rag_hallucination_triage_gate.py tests/test_legal_rag_authority_citation_gate.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _decision_row(self, row: dict[str, Any], authority_gate: dict[str, Any]) -> dict[str, Any]:
        labels = [str(label) for label in row.get("failure_labels", [])]
        answer_mode = self._answer_mode(labels, str(row.get("severity") or "medium"))
        score = self._evidence_score(labels, answer_mode)
        related_authority_rows = [
            self._authority_row_status(row_id, authority_gate)
            for row_id in row.get("linked_authority_row_ids", [])
        ]
        authority_status = self._authority_status(answer_mode, related_authority_rows)
        release_action = self._release_action(answer_mode)
        premium_required = answer_mode == "premium_exception"
        lawyer_required = answer_mode in {"lawyer_review", "premium_exception"}
        abstain_required = answer_mode == "abstain"
        clarification_required = answer_mode == "ask_clarification"

        return {
            "id": f"abstention-{row['case_id']}",
            "case_id": row["case_id"],
            "title": row["title"],
            "scenario": row["scenario"],
            "user_need_ids": ["grounded-legal-output", "reviewer-visibility", "product-readiness"],
            "answer_mode": answer_mode,
            "release_action": release_action,
            "severity": row["severity"],
            "evidence_sufficiency_score": score,
            "evidence_sufficiency_status": self._evidence_status(score),
            "citation_grounding_status": self._citation_status(labels),
            "authority_gate_status": authority_status,
            "hallucination_triage_status": "blocker" if row.get("block_release") else "review",
            "block_release": release_action not in {"allow_answer", "allow_answer_with_warning"},
            "cheap_first_route": self._cheap_first_route(answer_mode, labels),
            "premium_exception_required": premium_required,
            "lawyer_review_required": lawyer_required,
            "abstain_required": abstain_required,
            "clarification_required": clarification_required,
            "reason_codes": self._reason_codes(labels, answer_mode),
            "linked_gate_ids": [
                "legal-rag-abstention-escalation-gate",
                "legal-rag-hallucination-triage-gate",
                "legal-rag-authority-citation-gate",
                "model-escalation-policy",
            ],
            "linked_authority_row_ids": row.get("linked_authority_row_ids", []),
            "linked_failure_labels": labels,
            "reviewer_actions": row.get("reviewer_actions", []),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_abstention_escalation_gate.py -q",
            ],
            "privacy_boundary": self._row_privacy_boundary(),
        }

    def _ready_answer_row(self, authority_gate: dict[str, Any]) -> dict[str, Any]:
        ready_rows = [
            row for row in authority_gate.get("source_rows", [])
            if row.get("status") == "ready" and row.get("freshness_status") == "fresh"
        ]
        source_ids = [str(row["id"]) for row in ready_rows[:2]]
        return {
            "id": "abstention-ready-authority-metadata",
            "case_id": "authority-ready-metadata",
            "title": "Fresh selected authority metadata can answer",
            "scenario": "fresh authority and citation metadata",
            "user_need_ids": ["grounded-legal-output", "plain-language-actionability"],
            "answer_mode": "answer",
            "release_action": "allow_answer",
            "severity": "low",
            "evidence_sufficiency_score": 100,
            "evidence_sufficiency_status": "sufficient",
            "citation_grounding_status": "grounded",
            "authority_gate_status": "ready",
            "hallucination_triage_status": "no_failure_fixture_label",
            "block_release": False,
            "cheap_first_route": self._cheap_first_route("answer", []),
            "premium_exception_required": False,
            "lawyer_review_required": False,
            "abstain_required": False,
            "clarification_required": False,
            "reason_codes": ["fresh_authority_metadata", "selected_source_ids_match"],
            "linked_gate_ids": [
                "legal-rag-abstention-escalation-gate",
                "legal-rag-authority-citation-gate",
                "model-escalation-policy",
            ],
            "linked_authority_row_ids": source_ids,
            "linked_failure_labels": [],
            "reviewer_actions": ["allow_answer_with_citations"],
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_abstention_escalation_gate.py -q",
            ],
            "privacy_boundary": self._row_privacy_boundary(),
        }

    def _answer_mode(self, labels: list[str], severity: str) -> str:
        label_set = set(labels)
        if "hallucinated_article" in label_set:
            return "abstain"
        if "unsupported_conclusion" in label_set:
            return "premium_exception"
        if "stale_regulation" in label_set:
            return "lawyer_review"
        if "jurisdiction_mismatch" in label_set or "missing_citation" in label_set:
            return "ask_clarification"
        if "conflicting_facts" in label_set:
            return "answer_with_warning"
        if severity in {"critical", "high"}:
            return "abstain"
        return "answer_with_warning"

    def _release_action(self, answer_mode: str) -> str:
        return {
            "answer": "allow_answer",
            "answer_with_warning": "allow_answer_with_warning",
            "ask_clarification": "ask_user_for_missing_fact_or_source",
            "lawyer_review": "queue_lawyer_review_before_answer",
            "abstain": "withhold_answer_until_grounded",
            "premium_exception": "queue_premium_exception_after_operator_approval",
        }[answer_mode]

    def _evidence_score(self, labels: list[str], answer_mode: str) -> int:
        score = 100
        penalties = {
            "missing_citation": 45,
            "stale_regulation": 35,
            "jurisdiction_mismatch": 40,
            "unsupported_conclusion": 65,
            "hallucinated_article": 70,
            "conflicting_facts": 25,
        }
        for label in labels:
            score -= penalties.get(label, 20)
        if answer_mode == "premium_exception":
            score = min(score, 35)
        if answer_mode == "abstain":
            score = min(score, 25)
        return max(0, score)

    def _evidence_status(self, score: int) -> str:
        if score >= 80:
            return "sufficient"
        if score >= 55:
            return "warning"
        return "insufficient"

    def _citation_status(self, labels: list[str]) -> str:
        label_set = set(labels)
        if label_set.intersection({"missing_citation", "hallucinated_article"}):
            return "ungrounded"
        if label_set.intersection({"stale_regulation", "jurisdiction_mismatch", "unsupported_conclusion"}):
            return "review_required"
        if "conflicting_facts" in label_set:
            return "grounded_with_conflict"
        return "grounded"

    def _authority_status(self, answer_mode: str, authority_rows: list[dict[str, Any]]) -> str:
        if any(row["status"] == "blocked" for row in authority_rows):
            return "blocked"
        if answer_mode in {"lawyer_review", "ask_clarification", "premium_exception"}:
            return "review_required"
        if answer_mode == "abstain":
            return "blocked"
        if any(row["status"] == "review_required" for row in authority_rows):
            return "review_required"
        return "ready"

    def _authority_row_status(self, row_id: str, authority_gate: dict[str, Any]) -> dict[str, Any]:
        for row in authority_gate.get("source_rows", []):
            if row.get("id") == row_id:
                return {
                    "id": row_id,
                    "status": row.get("status", "unknown"),
                    "freshness_status": row.get("freshness_status", "unknown"),
                }
        return {"id": row_id, "status": "unknown", "freshness_status": "unknown"}

    def _cheap_first_route(self, answer_mode: str, labels: list[str]) -> dict[str, Any]:
        signals = self._model_signals(answer_mode, labels)
        task = "review" if answer_mode in {"lawyer_review", "premium_exception"} else "fast"
        decision = self.model_escalation_service.evaluate(task, signals)
        next_step = decision.get("next_step") or {}
        return {
            "task": task,
            "decision": decision["decision"],
            "starts_cheap": answer_mode != "premium_exception",
            "recommended_model_alias": next_step.get("model_alias", "operator-review"),
            "requires_operator_review": bool(next_step.get("requires_operator_review")) or answer_mode == "premium_exception",
            "signals": signals,
            "model_called": False,
            "gateway_called": False,
        }

    def _model_signals(self, answer_mode: str, labels: list[str]) -> list[str]:
        label_set = set(labels)
        signals: list[str] = []
        if answer_mode in {"ask_clarification", "answer_with_warning"}:
            signals.append("needs_context")
        if answer_mode in {"lawyer_review", "premium_exception"}:
            signals.append("quality_gate_fail")
        if label_set.intersection({"missing_citation", "hallucinated_article"}):
            signals.append("citation_audit_fail")
        if "unsupported_conclusion" in label_set:
            signals.append("evidence_audit_fail")
        return self._unique(signals)

    def _reason_codes(self, labels: list[str], answer_mode: str) -> list[str]:
        return self._unique(
            [
                f"label:{label}" for label in labels
            ]
            + [
                f"answer_mode:{answer_mode}",
                f"release_action:{self._release_action(answer_mode)}",
            ]
        )

    def _mode_definition(self, mode: str) -> dict[str, Any]:
        definitions = {
            "answer": "Selected source and citation metadata are sufficient for a guarded answer.",
            "answer_with_warning": "Evidence exists but conflicts or caveats must remain visible.",
            "abstain": "The system must withhold a legal answer until grounding is repaired.",
            "ask_clarification": "The user or retriever must provide missing source, fact, or jurisdiction metadata first.",
            "lawyer_review": "A lawyer or maintainer must review authority, freshness, or legal reasoning before answer release.",
            "premium_exception": "Lower-tier checks failed; premium review is only allowed after explicit operator approval.",
        }
        return {
            "label": mode,
            "description": definitions[mode],
        }

    def _row_privacy_boundary(self) -> dict[str, bool]:
        return {
            "user_question_returned": False,
            "retrieved_context_returned": False,
            "unsafe_answer_returned": False,
            "raw_legal_text_returned": False,
            "prompt_returned": False,
            "model_output_returned": False,
            "credentials_returned": False,
        }

    def _recommended_actions(self, blocker_rows: list[dict[str, Any]]) -> list[str]:
        if blocker_rows:
            return [
                "Keep Legal RAG answer delivery blocked for abstain, lawyer-review, premium-exception, and clarification rows.",
                "Resolve hallucination triage labels and authority/citation gaps before changing model routes or broadening source indexes.",
                "Use cheap-first routes for metadata checks, and require operator approval before any premium exception.",
            ]
        return [
            "Keep the abstention gate in release readiness before each retrieval or source-index change.",
            "Re-run the hallucination and authority gates when new Legal RAG fixtures are added.",
        ]

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            safe = str(value or "").strip()
            if safe and safe not in seen:
                result.append(safe)
                seen.add(safe)
        return result
