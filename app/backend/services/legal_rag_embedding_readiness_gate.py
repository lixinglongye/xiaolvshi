from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_index_coverage_gate import LegalRagIndexCoverageGateService
from services.legal_rag_retrieval_diagnostics_gate import LegalRagRetrievalDiagnosticsGateService
from services.model_ops_gemini_embedding_cheap_first_preflight import (
    ModelOpsGeminiEmbeddingCheapFirstPreflightService,
)


class LegalRagEmbeddingReadinessGateService:
    """Build metadata-only Legal RAG embedding readiness evidence."""

    def __init__(
        self,
        embedding_preflight_service: ModelOpsGeminiEmbeddingCheapFirstPreflightService | None = None,
        index_coverage_service: LegalRagIndexCoverageGateService | None = None,
        retrieval_diagnostics_service: LegalRagRetrievalDiagnosticsGateService | None = None,
    ) -> None:
        self.embedding_preflight_service = (
            embedding_preflight_service or ModelOpsGeminiEmbeddingCheapFirstPreflightService()
        )
        self.index_coverage_service = index_coverage_service or LegalRagIndexCoverageGateService()
        self.retrieval_diagnostics_service = retrieval_diagnostics_service or LegalRagRetrievalDiagnosticsGateService()

    def build_gate(self, _payload: Any = None) -> dict[str, Any]:
        embedding_preflight = self.embedding_preflight_service.build_preflight()
        index_gate = self.index_coverage_service.build_gate()
        diagnostics_gate = self.retrieval_diagnostics_service.build_gate()
        readiness_rows = self._readiness_rows(embedding_preflight, index_gate, diagnostics_gate)
        status_counts = Counter(row["readiness_status"] for row in readiness_rows)
        release_counts = Counter(row["release_action"] for row in readiness_rows)
        blocked_rows = [row for row in readiness_rows if row["readiness_status"] == "blocked"]
        review_rows = [row for row in readiness_rows if row["readiness_status"] == "review_required"]
        checks = self._checks(embedding_preflight, index_gate, diagnostics_gate, blocked_rows, review_rows)
        status = "ready_with_blockers" if blocked_rows else ("ready_with_review" if review_rows else "ready")

        return {
            "id": "legal-rag-embedding-readiness-gate",
            "title": "Legal RAG embedding readiness gate",
            "status": status,
            "summary": {
                "readiness_row_count": len(readiness_rows),
                "ready_row_count": status_counts.get("ready", 0),
                "review_row_count": status_counts.get("review_required", 0),
                "blocked_row_count": status_counts.get("blocked", 0),
                "embedding_default_model": embedding_preflight["summary"]["cheap_first_default_model"],
                "embedding_default_canonical_model": embedding_preflight["summary"][
                    "cheap_first_default_canonical_model"
                ],
                "embedding_model_count": embedding_preflight["summary"]["embedding_model_count"],
                "text_embedding_ready_count": embedding_preflight["summary"]["text_embedding_ready_count"],
                "multimodal_review_required_count": embedding_preflight["summary"]["multimodal_review_count"],
                "index_plan_row_count": index_gate["summary"]["index_plan_row_count"],
                "index_ready_plan_count": index_gate["summary"]["ready_plan_count"],
                "index_review_plan_count": index_gate["summary"]["review_plan_count"],
                "index_blocked_plan_count": index_gate["summary"]["blocked_plan_count"],
                "diagnostic_row_count": diagnostics_gate["summary"]["diagnostic_row_count"],
                "diagnostic_review_row_count": diagnostics_gate["summary"].get("review_row_count", 0),
                "diagnostic_blocked_row_count": diagnostics_gate["summary"].get("blocked_row_count", 0),
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "index_written": False,
                "dataset_downloaded": False,
                "raw_query_included": False,
                "raw_retrieved_context_included": False,
                "raw_legal_text_included": False,
                "raw_embedding_vectors_included": False,
                "source_ids_returned": False,
                "credentials_included": False,
            },
            "readiness_rows": readiness_rows,
            "readiness_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "checks": checks,
            "linked_gate_summary": {
                "modelops_gemini_embedding_cheap_first_preflight": embedding_preflight["status"],
                "legal_rag_index_coverage_gate": index_gate["status"],
                "legal_rag_retrieval_diagnostics_gate": diagnostics_gate["status"],
                "embedding_preflight_warning_check_ids": embedding_preflight["warning_check_ids"],
                "index_release_action_counts": index_gate["release_action_counts"],
                "retrieval_release_action_counts": diagnostics_gate["release_action_counts"],
            },
            "readiness_policy": {
                "method": "metadata_only_legal_rag_embedding_readiness",
                "cheap_first_text_embedding_default": "gemini-embedding-001",
                "text_embedding_routes_can_preflight_without_review": True,
                "multimodal_embedding_requires_operator_review": True,
                "blocks_on_empty_index_coverage": True,
                "blocks_on_missing_retrieval_locator": True,
                "blocks_on_forbidden_query_filters": True,
                "requires_retrieval_diagnostics_before_answer_claims": True,
                "index_write_allowed": False,
            },
            "input_contract": {
                "accepted_fields": [
                    "route_id",
                    "task",
                    "input_scope",
                    "default_model",
                    "index_coverage_status",
                    "retrieval_diagnostics_status",
                    "reason_codes",
                ],
                "forbidden_fields_ignored": [
                    "query",
                    "question",
                    "raw_query",
                    "retrieved_context",
                    "raw_legal_text",
                    "source_text",
                    "source_id",
                    "embedding",
                    "embedding_vector",
                    "prompt",
                    "model_output",
                    "gateway_response",
                    "authorization",
                    "api_key",
                    "email",
                ],
            },
            "claim_boundary": {
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "index_quality_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_index_write_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claims": [
                    "The repository links cheap-first Gemini text embedding preflight to metadata-only Legal RAG index and retrieval readiness evidence.",
                    "Text-only Legal RAG embedding routes can be reviewed before index writes while multimodal embedding remains explicit-review.",
                ],
                "forbidden_claims": [
                    "Do not claim live embedding quality, legal answer quality, public benchmark scores, or index creation from this gate.",
                    "Do not claim Gemini/NewAPI execution, gateway execution, or automatic client delivery.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_source_ids": False,
                "returns_raw_query": False,
                "returns_user_question": False,
                "returns_retrieved_context": False,
                "returns_raw_legal_text": False,
                "returns_source_chunks": False,
                "returns_embedding_vectors": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "returns_gateway_payloads": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "calls_model": False,
                "writes_index": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_readiness_gate.py tests/test_model_ops_gemini_embedding_cheap_first_preflight.py tests/test_legal_rag_index_coverage_gate.py tests/test_legal_rag_retrieval_diagnostics_gate.py -q",
                "python -m pytest tests/test_legal_rag_embedding_readiness_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _readiness_rows(
        self,
        embedding_preflight: dict[str, Any],
        index_gate: dict[str, Any],
        diagnostics_gate: dict[str, Any],
    ) -> list[dict[str, Any]]:
        route_rows = {row["id"]: row for row in embedding_preflight["route_rows"]}
        index_summary = index_gate["summary"]
        diagnostics_summary = diagnostics_gate["summary"]

        return [
            self._row(
                row_id="legal-rag-text-index",
                route_row=route_rows["legal-rag-text-index"],
                index_coverage_status="ready",
                retrieval_diagnostics_status="review_required"
                if diagnostics_summary.get("review_row_count", 0)
                else "ready",
                readiness_status="ready",
                release_action="allow_text_embedding_preflight",
                reason_codes=["text_embedding_default_ready", "metadata_only_preflight"],
            ),
            self._row(
                row_id="source-deduping-batch-index",
                route_row=route_rows["source-deduping-batch-index"],
                index_coverage_status="ready",
                retrieval_diagnostics_status="ready",
                readiness_status="ready",
                release_action="allow_batch_embedding_preflight",
                reason_codes=["batch_text_embedding_ready", "cheap_first_budget_ready"],
            ),
            self._row(
                row_id="multimodal-evidence-index",
                route_row=route_rows["multimodal-evidence-index"],
                index_coverage_status="review_required",
                retrieval_diagnostics_status="review_required",
                readiness_status="review_required",
                release_action="review_multimodal_embedding_route",
                reason_codes=["explicit_multimodal_embedding_review_required"],
            ),
            self._row(
                row_id="empty-index-coverage-block",
                route_row=route_rows["legal-rag-text-index"],
                index_coverage_status="blocked" if index_summary.get("blocked_plan_count", 0) else "ready",
                retrieval_diagnostics_status="blocked" if diagnostics_summary.get("blocked_row_count", 0) else "ready",
                readiness_status="blocked",
                release_action="block_embedding_index_write",
                reason_codes=["empty_or_blocked_index_coverage_blocks_write"],
            ),
        ]

    def _row(
        self,
        *,
        row_id: str,
        route_row: dict[str, Any],
        index_coverage_status: str,
        retrieval_diagnostics_status: str,
        readiness_status: str,
        release_action: str,
        reason_codes: list[str],
    ) -> dict[str, Any]:
        return {
            "id": row_id,
            "task": route_row["task"],
            "route_mode": route_row["route_mode"],
            "input_scope": list(route_row["expected_inputs"]),
            "default_model": route_row["default_model"],
            "canonical_model": route_row["canonical_model"],
            "budget_mode": route_row["budget_mode"],
            "cost_tier": route_row["cost_tier"],
            "route_status": route_row["route_status"],
            "index_coverage_status": index_coverage_status,
            "retrieval_diagnostics_status": retrieval_diagnostics_status,
            "readiness_status": readiness_status,
            "release_action": release_action,
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "modelops-gemini-embedding-cheap-first-preflight",
                "legal-rag-index-coverage-gate",
                "legal-rag-retrieval-diagnostics-gate",
                "legal-rag-index-binding",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_query_returned": False,
                "retrieved_context_returned": False,
                "raw_legal_text_returned": False,
                "embedding_vectors_returned": False,
                "prompt_returned": False,
                "model_output_returned": False,
                "credentials_returned": False,
            },
        }

    def _checks(
        self,
        embedding_preflight: dict[str, Any],
        index_gate: dict[str, Any],
        diagnostics_gate: dict[str, Any],
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "cheap-first-text-embedding-default",
                "status": "pass"
                if embedding_preflight["summary"]["cheap_first_default_model"] == "gemini-embedding-001"
                else "fail",
                "reason": "Legal RAG text embedding should default to the cataloged cheap Gemini embedding model.",
                "evidence": [embedding_preflight["summary"]["cheap_first_default_model"]],
            },
            {
                "id": "index-coverage-linked",
                "status": "warn" if index_gate["summary"]["blocked_plan_count"] else "pass",
                "reason": "Embedding readiness must surface blocked Legal RAG index coverage before writes.",
                "evidence": [index_gate["status"], str(index_gate["summary"]["blocked_plan_count"])],
            },
            {
                "id": "retrieval-diagnostics-linked",
                "status": "warn" if diagnostics_gate["summary"].get("review_row_count", 0) else "pass",
                "reason": "Embedding readiness must stay connected to retrieval diagnostics before answer claims.",
                "evidence": [diagnostics_gate["status"]],
            },
            {
                "id": "multimodal-review-boundary",
                "status": "warn" if review_rows else "pass",
                "reason": "Multimodal evidence indexing remains explicit-review before default or route claims.",
                "evidence": [row["id"] for row in review_rows] or ["no_review_rows"],
            },
            {
                "id": "metadata-only-boundary",
                "status": "pass" if blocked_rows else "pass",
                "reason": "This gate does not call providers, models, gateways, write indexes, or return raw legal content.",
                "evidence": [
                    "model_called:false",
                    "gateway_called:false",
                    "network_called:false",
                    "index_written:false",
                    "embedding_vectors_returned:false",
                ],
            },
        ]

    def _recommended_actions(self, blocked_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Keep APP_AI_EMBEDDING_MODEL on gemini-embedding-001 for text-only Legal RAG indexing preflight.",
            "Review Legal RAG index coverage blockers before enabling any durable embedding index write.",
            "Run retrieval diagnostics after index coverage passes and before any legal-answer quality claim.",
        ]
        if review_rows:
            actions.append("Keep multimodal evidence embedding routes explicit-review until modality privacy and pricing checks pass.")
        if blocked_rows:
            actions.append("Treat empty coverage, missing locators, and forbidden filters as blockers for embedding index writes.")
        return actions
