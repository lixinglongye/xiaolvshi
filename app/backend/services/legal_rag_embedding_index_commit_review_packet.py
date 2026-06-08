from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_embedding_batch_observation_gate import (
    LegalRagEmbeddingBatchObservationGateService,
)
from services.model_catalog import canonical_model_id, task_default_model


SCHEMA_VERSION = "legal-rag-embedding-index-commit-review-packet-v1"
MAX_INDEX_COMMIT_ITEMS_PER_PACKET = 20


class LegalRagEmbeddingIndexCommitReviewPacketService:
    """Build metadata-only index commit review evidence from embedding observations."""

    def __init__(
        self,
        observation_gate_service: LegalRagEmbeddingBatchObservationGateService | None = None,
    ) -> None:
        self.observation_gate_service = observation_gate_service or LegalRagEmbeddingBatchObservationGateService()

    def build_packet(
        self,
        source_rows: list[dict[str, Any]] | None = None,
        observation_rows: Any = None,
    ) -> dict[str, Any]:
        observation_gate = self.observation_gate_service.build_gate(source_rows, observation_rows)
        observation_summary = observation_gate.get("summary") if isinstance(observation_gate.get("summary"), dict) else {}
        observation_linked = (
            observation_gate.get("linked_gate_summary")
            if isinstance(observation_gate.get("linked_gate_summary"), dict)
            else {}
        )
        review_items = [
            self._review_item(index, row)
            for index, row in enumerate(observation_gate["observation_rows"][:MAX_INDEX_COMMIT_ITEMS_PER_PACKET], 1)
        ]
        status_counts = Counter(item["commit_review_status"] for item in review_items)
        action_counts = Counter(item["commit_review_action"] for item in review_items)
        ready_items = [item for item in review_items if item["commit_review_status"] == "ready_for_maintainer_commit_review"]
        review_items_pending = [item for item in review_items if item["commit_review_status"] == "hold_for_commit_review"]
        blocked_items = [item for item in review_items if item["commit_review_status"] == "blocked_until_observation_ready"]
        status = (
            "commit_review_blocked"
            if blocked_items
            else ("commit_review_required" if review_items_pending else ("commit_review_ready" if ready_items else "not_supplied"))
        )

        return {
            "id": "legal-rag-embedding-index-commit-review-packet",
            "title": "Legal RAG embedding index commit review packet",
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "summary": {
                "commit_review_item_count": len(review_items),
                "ready_for_commit_review_count": len(ready_items),
                "hold_for_commit_review_count": len(review_items_pending),
                "blocked_commit_review_count": len(blocked_items),
                "required_signoff_count": sum(len(item["required_signoffs"]) for item in review_items),
                "commit_record_written": False,
                "index_commit_allowed_by_packet": False,
                "observed_vector_slot_total": _non_negative_int(observation_summary.get("observed_vector_slot_total")),
                "expected_vector_slot_total": _non_negative_int(observation_summary.get("expected_vector_slot_total")),
                "observed_chunk_total": _non_negative_int(observation_summary.get("observed_chunk_total")),
                "expected_chunk_total": _non_negative_int(observation_summary.get("expected_chunk_total")),
                "observed_cost_usd": _safe_float(observation_summary.get("observed_cost_usd")),
                "expected_cost_usd": _safe_float(observation_summary.get("expected_cost_usd")),
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "observation_gate_status": observation_gate["status"],
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "embeddings_created": False,
                "index_written": False,
                "database_written": False,
                "source_ids_returned": False,
                "approval_item_ids_returned": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "embedding_vectors_included": False,
                "credentials_included": False,
            },
            "commit_review_items": review_items,
            "commit_review_status_counts": dict(sorted(status_counts.items())),
            "commit_review_action_counts": dict(sorted(action_counts.items())),
            "ready_item_ids": [item["id"] for item in ready_items],
            "hold_item_ids": [item["id"] for item in review_items_pending],
            "blocked_item_ids": [item["id"] for item in blocked_items],
            "linked_gate_summary": {
                "legal_rag_embedding_index_commit_review_packet": status,
                "legal_rag_embedding_batch_observation_gate": observation_gate["status"],
                "legal_rag_embedding_batch_approval_packet": observation_linked.get(
                    "legal_rag_embedding_batch_approval_packet",
                    "not_run",
                ),
                "legal_rag_embedding_batch_budget_gate": observation_linked.get(
                    "legal_rag_embedding_batch_budget_gate",
                    "not_run",
                ),
                "legal_rag_embedding_index_dry_run_gate": observation_linked.get(
                    "legal_rag_embedding_index_dry_run_gate",
                    "not_run",
                ),
                "legal_rag_embedding_chunk_policy_gate": observation_linked.get(
                    "legal_rag_embedding_chunk_policy_gate",
                    "not_run",
                ),
                "embedding_default_model": task_default_model("embedding"),
            },
            "input_contract": {
                "accepted_container_keys": list(observation_gate["input_contract"]["accepted_container_keys"]),
                "accepted_review_fields": [
                    "queue_order",
                    "source_type",
                    "observation_status",
                    "observed_vector_slot_count",
                    "expected_vector_slot_count",
                    "observed_cost_usd",
                    "expected_cost_usd",
                    "commit_review_status",
                    "commit_review_action",
                    "required_signoffs",
                ],
                "forbidden_fields_ignored": sorted(
                    set(observation_gate["input_contract"]["forbidden_fields_ignored"])
                    | {
                        "source_id",
                        "source_ids",
                        "approval_item_id",
                        "source_approval_item_id",
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
                        "commit_signature",
                    }
                ),
                "source_id_echoed": False,
                "approval_item_id_echoed": False,
                "committer_identity_collected": False,
                "commit_record_written": False,
                "review_packet_only": True,
            },
            "commit_review_policy": {
                "method": "metadata_only_embedding_index_commit_review_packet",
                "requires_ready_observation_rows": True,
                "requires_maintainer_signoff_for_ready_rows": True,
                "requires_rag_index_reviewer_for_ready_rows": True,
                "requires_no_vector_slot_mismatch": True,
                "requires_no_blocked_observation_rows": True,
                "commit_record_written": False,
                "index_commit_allowed": False,
                "embedding_creation_allowed": False,
                "model_call_allowed": False,
                "database_write_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "maintainer_commit_approval_claimed": False,
                "index_commit_claimed": False,
                "automatic_index_write_claimed": False,
                "embedding_batch_executed_claimed_by_packet": False,
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "index_quality_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claims": [
                    "The repository exposes a metadata-only commit review packet after aggregate embedding observations.",
                    "Ready rows can be handed to an external maintainer review before any real index commit.",
                ],
                "forbidden_claims": [
                    "Do not claim this packet approved maintainers, executed embeddings, stored vectors, or wrote an index.",
                    "Do not claim live pricing, retrieval quality, legal answer quality, or index quality from this packet.",
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
            "recommended_actions": self._recommended_actions(ready_items, review_items_pending, blocked_items),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_index_commit_review_packet.py tests/test_legal_rag_embedding_batch_observation_gate.py -q",
                "python -m pytest tests/test_legal_rag_embedding_index_commit_review_packet.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _review_item(self, index: int, observation_row: dict[str, Any]) -> dict[str, Any]:
        observation_status = str(observation_row.get("observation_status") or "blocked")
        commit_review_status = self._commit_review_status(observation_status)
        reason_codes = self._reason_codes(observation_row, commit_review_status)
        return {
            "id": f"embedding-index-commit-review-{index}-{_safe_token(observation_row.get('source_type'))}",
            "source_type": _safe_token(observation_row.get("source_type")),
            "queue_order": _non_negative_int(observation_row.get("queue_order")),
            "observation_status": observation_status,
            "observed_status": str(observation_row.get("observed_status") or "not_supplied"),
            "commit_review_status": commit_review_status,
            "commit_review_action": self._commit_review_action(commit_review_status),
            "expected_vector_slot_count": _non_negative_int(observation_row.get("expected_vector_slot_count")),
            "observed_vector_slot_count": _non_negative_int(observation_row.get("observed_vector_slot_count")),
            "vector_slot_delta": _safe_int(observation_row.get("vector_slot_delta")),
            "expected_chunk_count": _non_negative_int(observation_row.get("expected_chunk_count")),
            "observed_chunk_count": _non_negative_int(observation_row.get("observed_chunk_count")),
            "expected_cost_usd": _safe_float(observation_row.get("expected_cost_usd")),
            "observed_cost_usd": _safe_float(observation_row.get("observed_cost_usd")),
            "cost_delta_usd": _safe_float(observation_row.get("cost_delta_usd")),
            "embedding_model": task_default_model("embedding"),
            "canonical_embedding_model": canonical_model_id(task_default_model("embedding")),
            "required_signoffs": self._required_signoffs(commit_review_status),
            "pre_commit_checks": self._pre_commit_checks(commit_review_status),
            "blocking_reason_codes": [] if commit_review_status == "ready_for_maintainer_commit_review" else reason_codes,
            "commit_record_written": False,
            "index_commit_allowed": False,
            "database_write_allowed": False,
            "model_call_allowed": False,
            "operator_action": self._operator_action(commit_review_status),
            "reason_codes": reason_codes,
            "linked_gate_ids": [
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
                "credentials_returned": False,
            },
        }

    def _commit_review_status(self, observation_status: str) -> str:
        if observation_status == "ready_for_index_review":
            return "ready_for_maintainer_commit_review"
        if observation_status == "review_required":
            return "hold_for_commit_review"
        return "blocked_until_observation_ready"

    def _commit_review_action(self, status: str) -> str:
        if status == "ready_for_maintainer_commit_review":
            return "prepare_external_index_commit_review"
        if status == "hold_for_commit_review":
            return "hold_index_commit_for_observation_review"
        return "block_index_commit"

    def _required_signoffs(self, status: str) -> list[str]:
        if status == "ready_for_maintainer_commit_review":
            return ["maintainer_owner", "rag_index_reviewer", "privacy_reviewer"]
        if status == "hold_for_commit_review":
            return ["rag_index_reviewer"]
        return []

    def _pre_commit_checks(self, status: str) -> list[str]:
        if status == "ready_for_maintainer_commit_review":
            return [
                "confirm-observation-row-ready",
                "confirm-vector-slot-counts-match",
                "confirm-no-raw-source-chunks-or-vectors",
                "record-index-commit-approval-outside-this-service",
            ]
        if status == "hold_for_commit_review":
            return [
                "resolve-observation-review-codes",
                "confirm-cost-and-token-deltas",
                "rerun-batch-observation-gate",
            ]
        return [
            "resolve-blocked-observation-row",
            "do-not-write-index",
            "rerun-approval-and-observation-chain",
        ]

    def _operator_action(self, status: str) -> str:
        if status == "ready_for_maintainer_commit_review":
            return "Prepare an external index-commit review packet; this service does not write the index."
        if status == "hold_for_commit_review":
            return "Hold the index commit until observation review codes are resolved."
        return "Block index commit; fix approval, budget, or observation evidence first."

    def _reason_codes(self, observation_row: dict[str, Any], commit_review_status: str) -> list[str]:
        if commit_review_status == "ready_for_maintainer_commit_review":
            return ["embedding_index_commit_review_ready"]
        codes = [
            str(code)
            for code in observation_row.get("reason_codes", [])
            if str(code).strip() and str(code) != "embedding_batch_observation_ready"
        ]
        if commit_review_status == "hold_for_commit_review":
            codes.append("observation_row_requires_commit_review")
        else:
            codes.append("observation_row_blocks_index_commit")
        return _unique(codes)

    def _recommended_actions(
        self,
        ready_items: list[dict[str, Any]],
        review_items: list[dict[str, Any]],
        blocked_items: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Keep commit review packets metadata-only; write real index records only through a separate reviewed path.",
            "Never paste source chunks, embedding vectors, provider payloads, committer identity, or credentials into this packet.",
        ]
        if blocked_items:
            actions.append("Block index commits until blocked observation rows are resolved.")
        if review_items:
            actions.append("Review held rows for vector-slot mismatches, cost/token deltas, and observation review codes.")
        if ready_items:
            actions.append("Use ready item ids as references for an external maintainer commit review, not as proof of a committed index.")
        return actions


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return round(float(value), 8)
    except (TypeError, ValueError):
        return 0.0


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
