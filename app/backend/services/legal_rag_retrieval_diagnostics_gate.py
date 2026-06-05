from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_abstention_escalation_gate import LegalRagAbstentionEscalationGateService
from services.legal_rag_authority_citation_gate import LegalRagAuthorityCitationGateService
from services.legal_rag_evaluation import LegalRagEvaluationService
from services.model_escalation_policy import ModelEscalationPolicyService


class LegalRagRetrievalDiagnosticsGateService:
    """Build metadata-only diagnostics for Legal RAG retrieval quality."""

    def __init__(
        self,
        *,
        authority_gate_service: LegalRagAuthorityCitationGateService | None = None,
        abstention_gate_service: LegalRagAbstentionEscalationGateService | None = None,
        evaluation_service: LegalRagEvaluationService | None = None,
        model_escalation_service: ModelEscalationPolicyService | None = None,
    ) -> None:
        self.authority_gate_service = authority_gate_service or LegalRagAuthorityCitationGateService()
        self.abstention_gate_service = abstention_gate_service or LegalRagAbstentionEscalationGateService(
            authority_gate_service=self.authority_gate_service
        )
        self.evaluation_service = evaluation_service or LegalRagEvaluationService()
        self.model_escalation_service = model_escalation_service or ModelEscalationPolicyService()

    def build_gate(self) -> dict[str, Any]:
        authority_gate = self.authority_gate_service.build_gate()
        abstention_gate = self.abstention_gate_service.build_gate()
        evaluation_policy = self.evaluation_service.policy()
        rows = [
            self._row_from_scenario(scenario, authority_gate, abstention_gate)
            for scenario in self._diagnostic_scenarios()
        ]
        status_counts = Counter(row["retrieval_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        source_counts = Counter(row["source_coverage_status"] for row in rows)
        depth_gap_rows = [row for row in rows if row["top_k_depth_status"] != "sufficient"]
        jurisdiction_gap_rows = [row for row in rows if row["jurisdiction_status"] != "matched"]
        freshness_gap_rows = [row for row in rows if row["freshness_status"] != "fresh"]
        blocked_rows = [row for row in rows if row["release_action"] == "block_retrieval_use"]
        review_rows = [row for row in rows if row["release_action"] == "review_before_answer"]

        return {
            "id": "legal-rag-retrieval-diagnostics-gate",
            "status": "ready_with_blockers" if blocked_rows else ("ready_with_review" if review_rows else "ready"),
            "title": "Legal RAG retrieval diagnostics gate",
            "summary": {
                "diagnostic_row_count": len(rows),
                "ready_row_count": status_counts.get("ready", 0),
                "review_row_count": len(review_rows),
                "blocked_row_count": len(blocked_rows),
                "authority_coverage_ready_count": source_counts.get("ready", 0),
                "authority_coverage_partial_count": source_counts.get("partial", 0),
                "authority_coverage_gap_count": source_counts.get("gap", 0),
                "retrieval_depth_gap_count": len(depth_gap_rows),
                "jurisdiction_gap_count": len(jurisdiction_gap_rows),
                "freshness_gap_count": len(freshness_gap_rows),
                "cheap_first_retry_count": sum(1 for row in rows if row["cheap_first_action"]["decision"] in {"verify", "escalate"}),
                "retrieval_recall_weight": evaluation_policy["metric_weights"]["retrieval_recall"],
                "citation_precision_weight": evaluation_policy["metric_weights"]["citation_precision"],
                "authority_gate_status": authority_gate["status"],
                "abstention_gate_status": abstention_gate["status"],
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "raw_query_included": False,
                "raw_retrieved_context_included": False,
                "raw_legal_text_included": False,
                "prompt_included": False,
                "model_output_included": False,
                "credentials_included": False,
            },
            "diagnostic_rows": rows,
            "retrieval_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "linked_gate_summary": {
                "legal_rag_index_binding": "metadata-only retrieval-plan contract",
                "authority_gate_id": authority_gate["id"],
                "abstention_gate_id": abstention_gate["id"],
                "authority_review_rows": authority_gate["summary"]["authority_review_count"],
                "authority_citation_mismatch_count": authority_gate["summary"]["citation_mismatch_count"],
                "authority_retrieval_gap_count": authority_gate["summary"]["retrieval_gap_count"],
                "abstention_decision_rows": abstention_gate["summary"]["decision_row_count"],
                "abstention_blocker_count": abstention_gate["summary"]["blocker_count"],
            },
            "diagnostic_policy": {
                "method": "metadata_only_retrieval_diagnostic_rows",
                "minimum_ready_selected_source_count": 2,
                "minimum_top_k_depth": 3,
                "requires_jurisdiction_filter": True,
                "requires_fresh_or_review_due_sources": True,
                "blocks_on_empty_index_coverage": True,
                "blocks_on_forbidden_query_filters": True,
                "premium_exception_default_allowed": False,
                "cheap_first_default": True,
            },
            "research_basis": [
                {
                    "id": "ragchecker",
                    "url": "https://arxiv.org/abs/2408.08067",
                    "signal": "Use fine-grained retrieval and generation diagnostics rather than a single aggregate RAG score.",
                },
                {
                    "id": "ragas",
                    "url": "https://arxiv.org/abs/2309.15217",
                    "signal": "Context relevance and faithfulness need explicit evaluation before answer release.",
                },
                {
                    "id": "ares",
                    "url": "https://arxiv.org/abs/2311.09476",
                    "signal": "Automated RAG evaluation should track answer support and context quality with reusable rubrics.",
                },
                {
                    "id": "legal-rag-bench",
                    "url": "https://arxiv.org/abs/2603.01710",
                    "signal": "Legal RAG quality depends strongly on retrieval quality and grounded legal source selection.",
                },
            ],
            "claim_boundary": {
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "public_benchmark_score_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_client_delivery_claimed": False,
                "allowed_claims": [
                    "The repository exposes metadata-only retrieval diagnostic rows for local Legal RAG review.",
                    "The gate links source coverage, top-k depth, jurisdiction, freshness, and cheap-first routing boundaries.",
                ],
                "forbidden_claims": [
                    "Do not claim public Legal RAG Bench, RAGAS, ARES, or RAGChecker scores.",
                    "Do not claim live retrieval accuracy, legal answer accuracy, or production quality.",
                    "Do not claim NewAPI/Gemini execution or automatic client delivery.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_raw_query": False,
                "returns_user_question": False,
                "returns_retrieved_context": False,
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
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_retrieval_diagnostics_gate.py tests/test_legal_rag_index_binding.py tests/test_legal_rag_evaluation.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _diagnostic_scenarios(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "retrieval-contract-primary-authority",
                "query_intent": "contract_primary_authority",
                "expected_source_count": 3,
                "selected_source_count": 3,
                "top_k_depth": 5,
                "jurisdiction_match": True,
                "freshness_status": "fresh",
                "citation_gap": False,
                "retrieval_gap": False,
                "signals": [],
            },
            {
                "id": "retrieval-review-due-local-rule",
                "query_intent": "local_rule_review_due",
                "expected_source_count": 3,
                "selected_source_count": 2,
                "top_k_depth": 3,
                "jurisdiction_match": True,
                "freshness_status": "review_due",
                "citation_gap": False,
                "retrieval_gap": False,
                "signals": ["review_due_source"],
            },
            {
                "id": "retrieval-jurisdiction-drift",
                "query_intent": "same_topic_cross_jurisdiction",
                "expected_source_count": 3,
                "selected_source_count": 2,
                "top_k_depth": 4,
                "jurisdiction_match": False,
                "freshness_status": "fresh",
                "citation_gap": False,
                "retrieval_gap": False,
                "signals": ["jurisdiction_mismatch"],
            },
            {
                "id": "retrieval-shallow-top-k",
                "query_intent": "ambiguous_deadline_top_k_gap",
                "expected_source_count": 4,
                "selected_source_count": 2,
                "top_k_depth": 2,
                "jurisdiction_match": True,
                "freshness_status": "fresh",
                "citation_gap": False,
                "retrieval_gap": True,
                "signals": ["needs_context"],
            },
            {
                "id": "retrieval-citation-source-mismatch",
                "query_intent": "unselected_cited_source",
                "expected_source_count": 2,
                "selected_source_count": 2,
                "top_k_depth": 3,
                "jurisdiction_match": True,
                "freshness_status": "unknown",
                "citation_gap": True,
                "retrieval_gap": False,
                "signals": ["citation_audit_fail"],
            },
            {
                "id": "retrieval-empty-index-coverage",
                "query_intent": "no_index_coverage",
                "expected_source_count": 2,
                "selected_source_count": 0,
                "top_k_depth": 0,
                "jurisdiction_match": False,
                "freshness_status": "unknown",
                "citation_gap": True,
                "retrieval_gap": True,
                "signals": ["needs_context", "quality_gate_fail"],
            },
        ]

    def _row_from_scenario(
        self,
        scenario: dict[str, Any],
        authority_gate: dict[str, Any],
        abstention_gate: dict[str, Any],
    ) -> dict[str, Any]:
        selected = int(scenario["selected_source_count"])
        expected = max(1, int(scenario["expected_source_count"]))
        recall = round(selected / expected, 3)
        source_coverage_status = self._source_coverage_status(recall)
        top_k_depth_status = self._top_k_depth_status(int(scenario["top_k_depth"]), expected)
        jurisdiction_status = "matched" if scenario["jurisdiction_match"] else "mismatch"
        freshness_status = str(scenario["freshness_status"])
        retrieval_gap = bool(scenario["retrieval_gap"]) or source_coverage_status == "gap"
        citation_gap = bool(scenario["citation_gap"])
        retrieval_status = self._retrieval_status(
            source_coverage_status=source_coverage_status,
            top_k_depth_status=top_k_depth_status,
            jurisdiction_status=jurisdiction_status,
            freshness_status=freshness_status,
            citation_gap=citation_gap,
            retrieval_gap=retrieval_gap,
        )
        release_action = self._release_action(retrieval_status)
        reason_codes = self._reason_codes(
            source_coverage_status=source_coverage_status,
            top_k_depth_status=top_k_depth_status,
            jurisdiction_status=jurisdiction_status,
            freshness_status=freshness_status,
            citation_gap=citation_gap,
            retrieval_gap=retrieval_gap,
        )
        cheap_first_action = self._cheap_first_action(retrieval_status, list(scenario["signals"]))
        return {
            "id": scenario["id"],
            "query_intent": scenario["query_intent"],
            "retrieval_status": retrieval_status,
            "release_action": release_action,
            "source_coverage_status": source_coverage_status,
            "source_coverage_score": recall,
            "expected_source_count": expected,
            "selected_source_count": selected,
            "top_k_depth": int(scenario["top_k_depth"]),
            "top_k_depth_status": top_k_depth_status,
            "jurisdiction_status": jurisdiction_status,
            "freshness_status": freshness_status,
            "citation_gap": citation_gap,
            "retrieval_gap": retrieval_gap,
            "cheap_first_action": cheap_first_action,
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "legal-rag-retrieval-diagnostics-gate",
                "legal-rag-index-binding",
                "legal-rag-authority-citation-gate",
                "legal-rag-abstention-escalation-gate",
                "model-escalation-policy",
            ],
            "linked_authority_row_ids": self._linked_authority_rows(
                authority_gate,
                freshness_status=freshness_status,
                citation_gap=citation_gap,
                retrieval_gap=retrieval_gap,
                jurisdiction_status=jurisdiction_status,
            ),
            "linked_abstention_modes": self._linked_abstention_modes(abstention_gate, release_action),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_retrieval_diagnostics_gate.py -q",
            ],
            "privacy_boundary": self._row_privacy_boundary(),
        }

    def _source_coverage_status(self, recall: float) -> str:
        if recall >= 1.0:
            return "ready"
        if recall >= 0.5:
            return "partial"
        return "gap"

    def _top_k_depth_status(self, top_k_depth: int, expected_source_count: int) -> str:
        if top_k_depth >= max(3, expected_source_count):
            return "sufficient"
        if top_k_depth > 0:
            return "shallow"
        return "empty"

    def _retrieval_status(
        self,
        *,
        source_coverage_status: str,
        top_k_depth_status: str,
        jurisdiction_status: str,
        freshness_status: str,
        citation_gap: bool,
        retrieval_gap: bool,
    ) -> str:
        if source_coverage_status == "gap" or top_k_depth_status == "empty" or (citation_gap and retrieval_gap):
            return "blocked"
        if jurisdiction_status != "matched" or freshness_status in {"review_due", "unknown", "stale"}:
            return "review_required"
        if top_k_depth_status != "sufficient" or retrieval_gap or citation_gap:
            return "review_required"
        return "ready"

    def _release_action(self, retrieval_status: str) -> str:
        if retrieval_status == "ready":
            return "allow_retrieval_use"
        if retrieval_status == "review_required":
            return "review_before_answer"
        return "block_retrieval_use"

    def _reason_codes(
        self,
        *,
        source_coverage_status: str,
        top_k_depth_status: str,
        jurisdiction_status: str,
        freshness_status: str,
        citation_gap: bool,
        retrieval_gap: bool,
    ) -> list[str]:
        codes: list[str] = []
        if source_coverage_status != "ready":
            codes.append(f"source_coverage:{source_coverage_status}")
        if top_k_depth_status != "sufficient":
            codes.append(f"top_k_depth:{top_k_depth_status}")
        if jurisdiction_status != "matched":
            codes.append("jurisdiction_mismatch")
        if freshness_status != "fresh":
            codes.append(f"freshness:{freshness_status}")
        if citation_gap:
            codes.append("citation_gap")
        if retrieval_gap:
            codes.append("retrieval_gap")
        return codes or ["retrieval_ready"]

    def _cheap_first_action(self, retrieval_status: str, signals: list[str]) -> dict[str, Any]:
        task = "fast" if retrieval_status != "blocked" else "review"
        decision = self.model_escalation_service.evaluate(task, signals)
        next_step = decision.get("next_step") or {}
        return {
            "task": task,
            "decision": decision["decision"],
            "starts_cheap": retrieval_status != "blocked",
            "recommended_model_alias": next_step.get("model_alias", "operator-review"),
            "signals": signals,
            "requires_operator_review": bool(next_step.get("requires_operator_review")) or retrieval_status == "blocked",
            "model_called": False,
            "gateway_called": False,
        }

    def _linked_authority_rows(
        self,
        authority_gate: dict[str, Any],
        *,
        freshness_status: str,
        citation_gap: bool,
        retrieval_gap: bool,
        jurisdiction_status: str,
    ) -> list[str]:
        rows = authority_gate.get("source_rows") or []
        linked: list[str] = []
        for row in rows:
            if citation_gap and int(row.get("citation_mismatch_count") or 0) > 0:
                linked.append(str(row["id"]))
            if retrieval_gap and int(row.get("retrieval_gap_count") or 0) > 0:
                linked.append(str(row["id"]))
            if freshness_status != "fresh" and row.get("freshness_status") in {"review_due", "stale", "unknown"}:
                linked.append(str(row["id"]))
            if jurisdiction_status != "matched" and row.get("jurisdiction") not in {"CN-National", "unknown"}:
                linked.append(str(row["id"]))
        return self._unique(linked)[:5]

    def _linked_abstention_modes(self, abstention_gate: dict[str, Any], release_action: str) -> list[str]:
        modes: list[str] = []
        for row in abstention_gate.get("decision_rows", []):
            mode = str(row.get("answer_mode") or "")
            if release_action == "block_retrieval_use" and mode in {"abstain", "premium_exception"}:
                modes.append(mode)
            if release_action == "review_before_answer" and mode in {"ask_clarification", "lawyer_review"}:
                modes.append(mode)
            if release_action == "allow_retrieval_use" and mode in {"answer", "answer_with_warning"}:
                modes.append(mode)
        return self._unique(modes)

    def _row_privacy_boundary(self) -> dict[str, bool]:
        return {
            "raw_query_returned": False,
            "retrieved_context_returned": False,
            "raw_legal_text_returned": False,
            "prompt_returned": False,
            "model_output_returned": False,
            "credentials_returned": False,
        }

    def _recommended_actions(self, blocked_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]]) -> list[str]:
        if blocked_rows:
            return [
                "Block Legal RAG answer release when source coverage is empty, top-k depth is empty, or citation and retrieval gaps overlap.",
                "Repair index metadata and authority/citation rows before using premium models as an exception path.",
                "Keep diagnostic rows metadata-only until real retrieval logs are normalized and privacy-reviewed.",
            ]
        if review_rows:
            return [
                "Route partial coverage, shallow top-k, jurisdiction mismatch, and review-due freshness rows to maintainer review.",
                "Use cheap-first metadata checks before any model escalation.",
            ]
        return [
            "Keep retrieval diagnostics in release readiness before each index or source-ingestion change.",
            "Re-run authority citation and abstention gates when query-intent coverage changes.",
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
