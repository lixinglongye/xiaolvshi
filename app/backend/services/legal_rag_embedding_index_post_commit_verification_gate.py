from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_embedding_index_commit_review_packet import (
    LegalRagEmbeddingIndexCommitReviewPacketService,
)
from services.model_catalog import canonical_model_id, task_default_model


SCHEMA_VERSION = "legal-rag-embedding-index-post-commit-verification-gate-v1"
MAX_POST_COMMIT_VERIFICATION_ROWS = 20


class LegalRagEmbeddingIndexPostCommitVerificationGateService:
    """Build metadata-only post-commit verification evidence for embedding indexes."""

    def __init__(
        self,
        commit_review_packet_service: LegalRagEmbeddingIndexCommitReviewPacketService | None = None,
    ) -> None:
        self.commit_review_packet_service = commit_review_packet_service or LegalRagEmbeddingIndexCommitReviewPacketService()

    def build_gate(
        self,
        source_rows: list[dict[str, Any]] | None = None,
        observation_rows: Any = None,
        post_commit_observations: Any = None,
    ) -> dict[str, Any]:
        commit_review_packet = self.commit_review_packet_service.build_packet(source_rows, observation_rows)
        commit_summary = (
            commit_review_packet.get("summary") if isinstance(commit_review_packet.get("summary"), dict) else {}
        )
        commit_linked = (
            commit_review_packet.get("linked_gate_summary")
            if isinstance(commit_review_packet.get("linked_gate_summary"), dict)
            else {}
        )
        post_commit_rows = _post_commit_observation_map(post_commit_observations)
        commit_review_items = commit_review_packet.get("commit_review_items")
        if not isinstance(commit_review_items, list):
            commit_review_items = []
        commit_review_packet_status = str(commit_review_packet.get("status") or "not_run")
        verification_rows = [
            self._verification_row(index, item, post_commit_rows.get(_non_negative_int(item.get("queue_order"))))
            for index, item in enumerate(
                commit_review_items[:MAX_POST_COMMIT_VERIFICATION_ROWS],
                1,
            )
        ]
        status_counts = Counter(row["verification_status"] for row in verification_rows)
        action_counts = Counter(row["verification_action"] for row in verification_rows)
        verified_rows = [row for row in verification_rows if row["verification_status"] == "verified_for_retrieval_diagnostics"]
        review_rows = [row for row in verification_rows if row["verification_status"] == "verification_review_required"]
        blocked_rows = [row for row in verification_rows if row["verification_status"] == "verification_blocked"]
        status = (
            "post_commit_verification_blocked"
            if blocked_rows
            else (
                "post_commit_verification_review_required"
                if review_rows
                else ("post_commit_verification_ready" if verified_rows else "not_supplied")
            )
        )

        return {
            "id": "legal-rag-embedding-index-post-commit-verification-gate",
            "title": "Legal RAG embedding index post-commit verification gate",
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "summary": {
                "verification_row_count": len(verification_rows),
                "verified_for_retrieval_diagnostics_count": len(verified_rows),
                "verification_review_required_count": len(review_rows),
                "verification_blocked_count": len(blocked_rows),
                "expected_index_entry_total": sum(row["expected_index_entry_count"] for row in verification_rows),
                "observed_index_entry_total": sum(row["observed_index_entry_count"] for row in verification_rows),
                "expected_vector_slot_total": sum(row["expected_vector_slot_count"] for row in verification_rows),
                "observed_vector_slot_total": sum(row["observed_vector_slot_count"] for row in verification_rows),
                "metadata_record_total": sum(row["metadata_record_count"] for row in verification_rows),
                "retrieval_locator_total": sum(row["retrieval_locator_count"] for row in verification_rows),
                "checksum_record_total": sum(row["checksum_record_count"] for row in verification_rows),
                "failed_entry_total": sum(row["failed_entry_count"] for row in verification_rows),
                "rollback_required_count": sum(1 for row in verification_rows if row["rollback_required"]),
                "retrieval_diagnostics_review_only_allowed": bool(verified_rows) and not review_rows and not blocked_rows,
                "retrieval_use_allowed_by_gate": False,
                "commit_review_packet_status": commit_review_packet_status,
                "commit_record_written": False,
                "index_written_by_gate": False,
                "database_written_by_gate": False,
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "embeddings_created": False,
                "source_ids_returned": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "embedding_vectors_included": False,
                "credentials_included": False,
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
            },
            "verification_rows": verification_rows,
            "verification_status_counts": dict(sorted(status_counts.items())),
            "verification_action_counts": dict(sorted(action_counts.items())),
            "verified_row_ids": [row["id"] for row in verified_rows],
            "review_row_ids": [row["id"] for row in review_rows],
            "blocked_row_ids": [row["id"] for row in blocked_rows],
            "linked_gate_summary": {
                "legal_rag_embedding_index_post_commit_verification_gate": status,
                "legal_rag_embedding_index_commit_review_packet": commit_review_packet_status,
                "legal_rag_embedding_batch_observation_gate": commit_linked.get(
                    "legal_rag_embedding_batch_observation_gate",
                    "not_run",
                ),
                "legal_rag_embedding_batch_approval_packet": commit_linked.get(
                    "legal_rag_embedding_batch_approval_packet",
                    "not_run",
                ),
                "legal_rag_embedding_batch_budget_gate": commit_linked.get(
                    "legal_rag_embedding_batch_budget_gate",
                    "not_run",
                ),
                "legal_rag_embedding_index_dry_run_gate": commit_linked.get(
                    "legal_rag_embedding_index_dry_run_gate",
                    "not_run",
                ),
                "legal_rag_embedding_chunk_policy_gate": commit_linked.get(
                    "legal_rag_embedding_chunk_policy_gate",
                    "not_run",
                ),
                "expected_vector_slot_total_from_commit_review": _non_negative_int(
                    commit_summary.get("expected_vector_slot_total")
                ),
                "observed_vector_slot_total_from_commit_review": _non_negative_int(
                    commit_summary.get("observed_vector_slot_total")
                ),
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
                "post_commit_rows",
                "rows",
                ],
                "accepted_verification_fields": [
                    "queue_order",
                    "post_commit_status",
                    "observed_vector_slot_count",
                    "observed_index_entry_count",
                    "metadata_record_count",
                    "retrieval_locator_count",
                    "checksum_record_count",
                    "failed_entry_count",
                    "rollback_required",
                    "rollback_action",
                ],
                "forbidden_fields_ignored": [
                    "source_id",
                    "source_ids",
                    "approval_item_id",
                    "raw_text",
                    "raw_legal_text",
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
                    "approver_email",
                    "committer_email",
                    "committer_name",
                    "committer_identity",
                    "commit_signature",
                    "commit_client",
                ],
                "source_id_echoed": False,
                "approval_item_id_echoed": False,
                "committer_identity_collected": False,
                "commit_record_written": False,
                "post_commit_observation_only": True,
            },
            "post_commit_verification_policy": {
                "method": "metadata_only_embedding_index_post_commit_verification_gate",
                "requires_ready_commit_review_rows": True,
                "requires_post_commit_observation_for_ready_rows": True,
                "requires_no_rollback_signal": True,
                "requires_no_failed_entries": True,
                "requires_index_entry_count_match": True,
                "requires_vector_slot_count_match": True,
                "requires_metadata_and_locator_counts": True,
                "retrieval_diagnostics_review_only": True,
                "retrieval_use_allowed": False,
                "index_write_allowed": False,
                "database_write_allowed": False,
                "model_call_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "maintainer_commit_approval_claimed": False,
                "index_commit_executed_by_gate_claimed": False,
                "post_commit_success_claimed_without_observation": False,
                "automatic_retrieval_enablement_claimed": False,
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "index_quality_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claims": [
                    "The repository exposes metadata-only post-commit verification evidence after commit review.",
                    "Verified rows may proceed to retrieval diagnostics review only; this gate does not enable production retrieval.",
                ],
                "forbidden_claims": [
                    "Do not claim this gate wrote, approved, or repaired an embedding index.",
                    "Do not claim retrieval quality, legal answer quality, live pricing, or production enablement from this gate.",
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
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(verified_rows, review_rows, blocked_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_index_post_commit_verification_gate.py tests/test_legal_rag_embedding_index_commit_review_packet.py -q",
                "python -m pytest tests/test_legal_rag_embedding_index_post_commit_verification_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _verification_row(
        self,
        index: int,
        commit_item: dict[str, Any],
        post_commit_row: dict[str, Any] | None,
    ) -> dict[str, Any]:
        expected_vector_slots = _non_negative_int(commit_item.get("expected_vector_slot_count"))
        observed = post_commit_row or {}
        observed_status = _safe_token(
            observed.get("post_commit_status")
            or observed.get("verification_status")
            or observed.get("commit_status")
            or observed.get("observed_status")
            or observed.get("status")
            or "not_supplied"
        )
        observed_vector_slots = _non_negative_int(
            _first_present(observed, ["observed_vector_slot_count", "vector_slot_count", "vector_slots"])
        )
        observed_index_entries = _non_negative_int(
            _first_present(observed, ["observed_index_entry_count", "index_entry_count", "entry_count"])
        )
        metadata_records = _non_negative_int(
            _first_present(observed, ["metadata_record_count", "metadata_records", "metadata_count"])
        )
        retrieval_locators = _non_negative_int(
            _first_present(observed, ["retrieval_locator_count", "retrieval_locators", "locator_count"])
        )
        checksum_records = _non_negative_int(
            _first_present(
                observed,
                ["checksum_record_count", "checksum_count", "hash_record_count", "hash_count"],
            )
        )
        failed_entries = _non_negative_int(_first_present(observed, ["failed_entry_count", "error_entry_count", "failure_count"]))
        rollback_required = _safe_bool(_first_present(observed, ["rollback_required", "rollback", "rollback_requested"]))
        commit_review_status = str(commit_item.get("commit_review_status") or "blocked_until_observation_ready")
        verification_status, reason_codes = self._verification_status(
            commit_review_status=commit_review_status,
            observed_status=observed_status,
            expected_vector_slots=expected_vector_slots,
            observed_vector_slots=observed_vector_slots,
            observed_index_entries=observed_index_entries,
            metadata_records=metadata_records,
            retrieval_locators=retrieval_locators,
            checksum_records=checksum_records,
            failed_entries=failed_entries,
            rollback_required=rollback_required,
            has_observation=post_commit_row is not None,
        )
        return {
            "id": f"embedding-index-post-commit-verification-{index}-{_safe_token(commit_item.get('source_type'))}",
            "source_type": _safe_token(commit_item.get("source_type")),
            "queue_order": _non_negative_int(commit_item.get("queue_order")),
            "commit_review_status": commit_review_status,
            "commit_review_action": str(commit_item.get("commit_review_action") or "block_index_commit"),
            "post_commit_status": observed_status,
            "verification_status": verification_status,
            "verification_action": self._verification_action(verification_status, rollback_required),
            "expected_vector_slot_count": expected_vector_slots,
            "observed_vector_slot_count": observed_vector_slots,
            "expected_index_entry_count": expected_vector_slots,
            "observed_index_entry_count": observed_index_entries,
            "metadata_record_count": metadata_records,
            "retrieval_locator_count": retrieval_locators,
            "checksum_record_count": checksum_records,
            "failed_entry_count": failed_entries,
            "rollback_required": rollback_required,
            "rollback_action": self._rollback_action(verification_status, rollback_required),
            "embedding_model": task_default_model("embedding"),
            "canonical_embedding_model": canonical_model_id(task_default_model("embedding")),
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "legal-rag-embedding-index-post-commit-verification-gate",
                "legal-rag-embedding-index-commit-review-packet",
                "legal-rag-embedding-batch-observation-gate",
                "legal-rag-embedding-batch-approval-packet",
                "legal-rag-embedding-batch-budget-gate",
                "legal-rag-embedding-index-dry-run-gate",
                "legal-rag-embedding-chunk-policy-gate",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "approval_item_ids_returned": False,
                "raw_legal_text_returned": False,
                "source_chunks_returned": False,
                "embedding_vectors_returned": False,
                "committer_identity_returned": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "commit_record_written": False,
                "database_written": False,
                "index_written": False,
                "retrieval_use_enabled": False,
                "credentials_returned": False,
            },
        }

    def _verification_status(
        self,
        *,
        commit_review_status: str,
        observed_status: str,
        expected_vector_slots: int,
        observed_vector_slots: int,
        observed_index_entries: int,
        metadata_records: int,
        retrieval_locators: int,
        checksum_records: int,
        failed_entries: int,
        rollback_required: bool,
        has_observation: bool,
    ) -> tuple[str, list[str]]:
        if commit_review_status == "blocked_until_observation_ready":
            return "verification_blocked", ["commit_review_blocks_post_commit_verification"]
        if commit_review_status == "hold_for_commit_review":
            return "verification_review_required", ["commit_review_hold_blocks_verification_ready"]
        if not has_observation:
            return "verification_review_required", ["post_commit_observation_missing"]
        reason_codes: list[str] = []
        success_statuses = {"success", "succeeded", "committed", "verified", "indexed", "complete", "completed", "passed", "ready"}
        if observed_status in {"failed", "failure", "error", "blocked", "reverted", "rollback_required"}:
            reason_codes.append(f"post_commit_status_blocks_verification:{observed_status}")
        if rollback_required:
            reason_codes.append("rollback_required")
        if failed_entries > 0:
            reason_codes.append("failed_index_entries_present")
        if reason_codes:
            return "verification_blocked", _unique(reason_codes)
        if observed_status not in success_statuses:
            reason_codes.append(f"post_commit_status_requires_review:{observed_status}")
        if observed_vector_slots != expected_vector_slots:
            reason_codes.append("observed_vector_slot_count_mismatch")
        if observed_index_entries != expected_vector_slots:
            reason_codes.append("observed_index_entry_count_mismatch")
        if metadata_records < expected_vector_slots:
            reason_codes.append("metadata_record_count_below_expected")
        if retrieval_locators < expected_vector_slots:
            reason_codes.append("retrieval_locator_count_below_expected")
        if checksum_records < expected_vector_slots:
            reason_codes.append("checksum_record_count_below_expected")
        if reason_codes:
            return "verification_review_required", _unique(reason_codes)
        return "verified_for_retrieval_diagnostics", ["post_commit_verification_ready_for_diagnostics_review"]

    def _verification_action(self, status: str, rollback_required: bool) -> str:
        if status == "verified_for_retrieval_diagnostics":
            return "allow_retrieval_diagnostics_review_only"
        if status == "verification_review_required":
            return "hold_for_post_commit_review"
        if rollback_required:
            return "block_retrieval_use_and_prepare_rollback"
        return "block_retrieval_use"

    def _rollback_action(self, status: str, rollback_required: bool) -> str:
        if rollback_required:
            return "prepare_external_rollback_review"
        if status == "verification_blocked":
            return "hold_retrieval_use_until_blockers_clear"
        return "none"

    def _recommended_actions(
        self,
        verified_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        blocked_rows: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Keep post-commit verification metadata-only; do not paste source chunks, vectors, credentials, or committer identity.",
            "Treat verified rows as eligible for retrieval diagnostics review only, not as production retrieval enablement.",
        ]
        if blocked_rows:
            actions.append("Block retrieval use and prepare rollback review for failed, rollback, or upstream-blocked rows.")
        if review_rows:
            actions.append("Resolve count mismatches, missing metadata records, missing locators, or absent post-commit observations.")
        if verified_rows:
            actions.append("Attach verified row ids to retrieval diagnostics evidence after external maintainer commit records are reviewed.")
        return actions


def _post_commit_observation_map(value: Any) -> dict[int, dict[str, Any]]:
    rows = value
    if isinstance(rows, dict):
        for key in ("post_commit_observations", "commit_observations", "verification_rows", "rows", "observations"):
            candidate = rows.get(key)
            if isinstance(candidate, list):
                rows = candidate
                break
            if isinstance(candidate, dict):
                return _post_commit_observation_map(candidate)
        else:
            rows = []
    if not isinstance(rows, list):
        return {}
    mapped: dict[int, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            queue_order = _non_negative_int(row.get("queue_order"))
            if queue_order > 0:
                mapped[queue_order] = row
    return mapped


def _first_present(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "rollback", "required"}
    return False


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_token(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    return "".join(ch if ch.isalnum() or ch in {"_", "-", ".", ":"} else "_" for ch in text)[:80] or "unknown"


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        safe = str(value or "").strip()
        if safe and safe not in seen:
            seen.add(safe)
            result.append(safe)
    return result
