from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_embedding_index_post_commit_verification_gate import (
    LegalRagEmbeddingIndexPostCommitVerificationGateService,
)
from services.model_catalog import canonical_model_id, task_default_model


SCHEMA_VERSION = "legal-rag-embedding-retrieval-diagnostics-handoff-gate-v1"
MAX_HANDOFF_ROWS = 20


class LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService:
    """Build metadata-only handoff evidence between index verification and retrieval diagnostics."""

    def __init__(
        self,
        post_commit_verification_service: LegalRagEmbeddingIndexPostCommitVerificationGateService | None = None,
    ) -> None:
        self.post_commit_verification_service = (
            post_commit_verification_service or LegalRagEmbeddingIndexPostCommitVerificationGateService()
        )

    def build_gate(
        self,
        source_rows: list[dict[str, Any]] | None = None,
        observation_rows: Any = None,
        post_commit_observations: Any = None,
        verification_gate: Any = None,
    ) -> dict[str, Any]:
        direct_gate = _verification_gate_from_direct_input(verification_gate)
        verification_gate = direct_gate or self.post_commit_verification_service.build_gate(
            source_rows,
            observation_rows,
            post_commit_observations,
        )
        verification_rows = verification_gate.get("verification_rows")
        if not isinstance(verification_rows, list):
            verification_rows = []
        verification_summary = (
            verification_gate.get("summary") if isinstance(verification_gate.get("summary"), dict) else {}
        )
        verification_linked = (
            verification_gate.get("linked_gate_summary")
            if isinstance(verification_gate.get("linked_gate_summary"), dict)
            else {}
        )
        handoff_rows = [
            self._handoff_row(index, row)
            for index, row in enumerate(verification_rows[:MAX_HANDOFF_ROWS], 1)
            if isinstance(row, dict)
        ]
        status_counts = Counter(row["handoff_status"] for row in handoff_rows)
        action_counts = Counter(row["handoff_action"] for row in handoff_rows)
        ready_rows = [row for row in handoff_rows if row["handoff_status"] == "ready_for_retrieval_diagnostics_handoff"]
        hold_rows = [row for row in handoff_rows if row["handoff_status"] == "hold_for_post_commit_review"]
        blocked_rows = [row for row in handoff_rows if row["handoff_status"] == "blocked_until_verification_ready"]
        status = (
            "retrieval_diagnostics_handoff_blocked"
            if blocked_rows
            else (
                "retrieval_diagnostics_handoff_review_required"
                if hold_rows
                else ("retrieval_diagnostics_handoff_ready" if ready_rows else "not_supplied")
            )
        )

        return {
            "id": "legal-rag-embedding-retrieval-diagnostics-handoff-gate",
            "title": "Legal RAG embedding retrieval diagnostics handoff gate",
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "summary": {
                "handoff_row_count": len(handoff_rows),
                "ready_handoff_count": len(ready_rows),
                "hold_handoff_count": len(hold_rows),
                "blocked_handoff_count": len(blocked_rows),
                "diagnostics_review_ready_count": len(ready_rows),
                "rollback_review_required_count": sum(1 for row in handoff_rows if row["rollback_required"]),
                "expected_index_entry_total": sum(row["expected_index_entry_count"] for row in handoff_rows),
                "observed_index_entry_total": sum(row["observed_index_entry_count"] for row in handoff_rows),
                "metadata_record_total": sum(row["metadata_record_count"] for row in handoff_rows),
                "retrieval_locator_total": sum(row["retrieval_locator_count"] for row in handoff_rows),
                "safe_handoff_payload_field_count": len(self._safe_payload_fields()),
                "handoff_payload_included": False,
                "query_payload_included": False,
                "retrieved_context_included": False,
                "production_retrieval_allowed_count": 0,
                "production_retrieval_allowed_by_gate": False,
                "retrieval_diagnostics_review_only": True,
                "post_commit_verification_gate_status": str(verification_gate.get("status") or "not_run"),
                "post_commit_verified_count": _non_negative_int(
                    verification_summary.get("verified_for_retrieval_diagnostics_count")
                ),
                "post_commit_review_required_count": _non_negative_int(
                    verification_summary.get("verification_review_required_count")
                ),
                "post_commit_blocked_count": _non_negative_int(verification_summary.get("verification_blocked_count")),
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "embeddings_created": False,
                "index_written": False,
                "database_written": False,
                "source_ids_returned": False,
                "raw_query_included": False,
                "retrieved_context_returned": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "embedding_vectors_included": False,
                "credentials_included": False,
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
            },
            "handoff_rows": handoff_rows,
            "handoff_status_counts": dict(sorted(status_counts.items())),
            "handoff_action_counts": dict(sorted(action_counts.items())),
            "ready_handoff_row_ids": [row["id"] for row in ready_rows],
            "hold_handoff_row_ids": [row["id"] for row in hold_rows],
            "blocked_handoff_row_ids": [row["id"] for row in blocked_rows],
            "linked_gate_summary": {
                "legal_rag_embedding_retrieval_diagnostics_handoff_gate": status,
                "legal_rag_embedding_index_post_commit_verification_gate": str(
                    verification_gate.get("status") or "not_run"
                ),
                "legal_rag_embedding_index_commit_review_packet": verification_linked.get(
                    "legal_rag_embedding_index_commit_review_packet",
                    "not_run",
                ),
                "legal_rag_embedding_batch_observation_gate": verification_linked.get(
                    "legal_rag_embedding_batch_observation_gate",
                    "not_run",
                ),
                "legal_rag_retrieval_diagnostics_gate": "downstream_metadata_only_review",
                "embedding_default_model": task_default_model("embedding"),
            },
            "input_contract": {
                "accepted_container_keys": [
                    "source_rows",
                    "sources",
                    "records",
                    "metadata_rows",
                    "observations",
                    "embedding_observations",
                    "batch_observations",
                    "observation_rows",
                    "post_commit_observations",
                    "commit_observations",
                    "verification_rows",
                    "post_commit_verification_gate",
                    "verification_gate",
                    "handoff_source_rows",
                    "post_commit_rows",
                    "rows",
                ],
                "safe_handoff_payload_fields": self._safe_payload_fields(),
                "forbidden_fields_ignored": [
                    "source_id",
                    "source_ids",
                    "approval_item_id",
                    "raw_text",
                    "raw_legal_text",
                    "raw_query",
                    "query",
                    "question",
                    "retrieved_context",
                    "raw_context",
                    "source_chunk",
                    "source_chunks",
                    "chunk_text",
                    "embedding_vector",
                    "embedding_vectors",
                    "vector",
                    "vectors",
                    "prompt",
                    "model_output",
                    "gateway_payload",
                    "gateway_response",
                    "headers",
                    "authorization",
                    "api_key",
                    "email",
                    "committer_email",
                    "committer_name",
                    "committer_identity",
                    "commit_signature",
                    "handoff_client",
                ],
                "source_id_echoed": False,
                "approval_item_id_echoed": False,
                "query_payload_collected": False,
                "retrieved_context_collected": False,
                "committer_identity_collected": False,
                "production_retrieval_enabled": False,
                "handoff_payload_materialized": False,
            },
            "handoff_policy": {
                "method": "metadata_only_embedding_to_retrieval_diagnostics_handoff",
                "requires_verified_post_commit_rows": True,
                "requires_no_post_commit_review_rows_for_global_ready": True,
                "requires_no_blocked_post_commit_rows": True,
                "allows_retrieval_diagnostics_review_only": True,
                "allows_production_retrieval": False,
                "allows_query_payload": False,
                "allows_retrieved_context_payload": False,
                "allows_source_id_payload": False,
                "allows_embedding_vector_payload": False,
                "model_call_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "retrieval_diagnostics_executed_claimed": False,
                "production_retrieval_enabled_claimed": False,
                "index_quality_claimed": False,
                "retrieval_quality_claimed": False,
                "legal_advice_claimed": False,
                "automatic_client_delivery_claimed": False,
                "allowed_claims": [
                    "The repository exposes metadata-only handoff evidence between index verification and retrieval diagnostics.",
                    "Ready handoff rows may be referenced by downstream retrieval diagnostics review without including query text or retrieved context.",
                ],
                "forbidden_claims": [
                    "Do not claim this gate executed retrieval diagnostics or enabled production retrieval.",
                    "Do not claim retrieval quality, index quality, legal answer quality, or client delivery from this handoff.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_source_ids": False,
                "returns_approval_item_ids": False,
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
                "returns_committer_identity": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "calls_model": False,
                "creates_embeddings": False,
                "writes_index": False,
                "writes_database": False,
                "writes_commit_record": False,
                "enables_production_retrieval": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(ready_rows, hold_rows, blocked_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_retrieval_diagnostics_handoff_gate.py tests/test_legal_rag_embedding_index_post_commit_verification_gate.py -q",
                "python -m pytest tests/test_legal_rag_embedding_retrieval_diagnostics_handoff_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _handoff_row(self, index: int, verification_row: dict[str, Any]) -> dict[str, Any]:
        verification_status = str(verification_row.get("verification_status") or "verification_blocked")
        rollback_required = bool(verification_row.get("rollback_required"))
        handoff_status = self._handoff_status(verification_status)
        reason_codes = self._reason_codes(verification_row, handoff_status)
        return {
            "id": f"embedding-retrieval-diagnostics-handoff-{index}-{_safe_token(verification_row.get('source_type'))}",
            "source_type": _safe_token(verification_row.get("source_type")),
            "queue_order": _non_negative_int(verification_row.get("queue_order")),
            "post_commit_verification_status": verification_status,
            "post_commit_verification_action": str(verification_row.get("verification_action") or "block_retrieval_use"),
            "post_commit_status": str(verification_row.get("post_commit_status") or "not_supplied"),
            "handoff_status": handoff_status,
            "handoff_action": self._handoff_action(handoff_status, rollback_required),
            "diagnostics_review_scope": "metadata_only_count_and_status_review",
            "retrieval_diagnostics_review_allowed": handoff_status == "ready_for_retrieval_diagnostics_handoff",
            "production_retrieval_allowed": False,
            "retrieval_query_allowed": False,
            "retrieved_context_allowed": False,
            "expected_index_entry_count": _non_negative_int(verification_row.get("expected_index_entry_count")),
            "observed_index_entry_count": _non_negative_int(verification_row.get("observed_index_entry_count")),
            "metadata_record_count": _non_negative_int(verification_row.get("metadata_record_count")),
            "retrieval_locator_count": _non_negative_int(verification_row.get("retrieval_locator_count")),
            "checksum_record_count": _non_negative_int(verification_row.get("checksum_record_count")),
            "failed_entry_count": _non_negative_int(verification_row.get("failed_entry_count")),
            "rollback_required": rollback_required,
            "rollback_action": "route_to_external_rollback_review" if rollback_required else "none",
            "safe_handoff_payload_fields": self._safe_payload_fields(),
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "legal-rag-embedding-retrieval-diagnostics-handoff-gate",
                "legal-rag-embedding-index-post-commit-verification-gate",
                "legal-rag-embedding-index-commit-review-packet",
                "legal-rag-retrieval-diagnostics-gate",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_query_returned": False,
                "retrieved_context_returned": False,
                "raw_legal_text_returned": False,
                "source_chunks_returned": False,
                "embedding_vectors_returned": False,
                "committer_identity_returned": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "production_retrieval_enabled": False,
                "credentials_returned": False,
            },
        }

    def _handoff_status(self, verification_status: str) -> str:
        if verification_status == "verified_for_retrieval_diagnostics":
            return "ready_for_retrieval_diagnostics_handoff"
        if verification_status == "verification_review_required":
            return "hold_for_post_commit_review"
        return "blocked_until_verification_ready"

    def _handoff_action(self, handoff_status: str, rollback_required: bool) -> str:
        if handoff_status == "ready_for_retrieval_diagnostics_handoff":
            return "prepare_metadata_only_retrieval_diagnostics_review"
        if handoff_status == "hold_for_post_commit_review":
            return "hold_retrieval_diagnostics_handoff"
        if rollback_required:
            return "block_handoff_and_prepare_rollback_review"
        return "block_retrieval_diagnostics_handoff"

    def _reason_codes(self, verification_row: dict[str, Any], handoff_status: str) -> list[str]:
        if handoff_status == "ready_for_retrieval_diagnostics_handoff":
            return ["retrieval_diagnostics_handoff_ready_metadata_only"]
        inherited = [
            str(code)
            for code in verification_row.get("reason_codes", [])
            if str(code).strip() and str(code) != "post_commit_verification_ready_for_diagnostics_review"
        ]
        if handoff_status == "hold_for_post_commit_review":
            inherited.append("post_commit_verification_requires_handoff_review")
        else:
            inherited.append("post_commit_verification_blocks_handoff")
        return _unique(inherited)

    def _safe_payload_fields(self) -> list[str]:
        return [
            "source_type",
            "queue_order",
            "post_commit_verification_status",
            "handoff_status",
            "handoff_action",
            "expected_index_entry_count",
            "observed_index_entry_count",
            "metadata_record_count",
            "retrieval_locator_count",
            "checksum_record_count",
            "failed_entry_count",
            "rollback_required",
            "reason_codes",
            "linked_gate_ids",
        ]

    def _recommended_actions(
        self,
        ready_rows: list[dict[str, Any]],
        hold_rows: list[dict[str, Any]],
        blocked_rows: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Keep the handoff metadata-only; do not include query text, retrieved context, source chunks, vectors, credentials, or committer identity.",
            "Use ready handoff rows only as references for retrieval diagnostics review, not as proof of production retrieval enablement.",
        ]
        if blocked_rows:
            actions.append("Block downstream diagnostics handoff for rollback, failed-entry, or upstream verification blockers.")
        if hold_rows:
            actions.append("Resolve post-commit verification review rows before preparing retrieval diagnostics evidence.")
        if ready_rows:
            actions.append("Attach ready handoff row ids to downstream retrieval diagnostics review packets with the safe payload field list.")
        return actions


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_token(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    return "".join(ch if ch.isalnum() or ch in {"_", "-", ".", ":"} else "_" for ch in text)[:80] or "unknown"


def _verification_gate_from_direct_input(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        rows = value.get("verification_rows")
        if not isinstance(rows, list):
            rows = value.get("handoff_source_rows")
        if not isinstance(rows, list):
            rows = value.get("rows")
        if isinstance(rows, list):
            return {
                "id": str(value.get("id") or "external-post-commit-verification-rows"),
                "status": str(value.get("status") or "external_verification_rows_supplied"),
                "summary": value.get("summary") if isinstance(value.get("summary"), dict) else {},
                "verification_rows": [row for row in rows if isinstance(row, dict)],
                "linked_gate_summary": value.get("linked_gate_summary")
                if isinstance(value.get("linked_gate_summary"), dict)
                else {},
            }
    if isinstance(value, list):
        return {
            "id": "external-post-commit-verification-rows",
            "status": "external_verification_rows_supplied",
            "summary": {},
            "verification_rows": [row for row in value if isinstance(row, dict)],
            "linked_gate_summary": {},
        }
    return None


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        safe = str(value or "").strip()
        if safe and safe not in seen:
            seen.add(safe)
            result.append(safe)
    return result
