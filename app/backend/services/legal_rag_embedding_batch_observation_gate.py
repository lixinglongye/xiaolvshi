from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_embedding_batch_approval_packet import (
    MAX_PARALLEL_EMBEDDING_REQUESTS,
    LegalRagEmbeddingBatchApprovalPacketService,
)
from services.model_catalog import canonical_model_id, task_default_model


SCHEMA_VERSION = "legal-rag-embedding-batch-observation-gate-v1"
MAX_OBSERVATION_ROWS = 20
COST_REVIEW_MULTIPLIER = 1.2
TOKEN_REVIEW_MULTIPLIER = 1.25


class LegalRagEmbeddingBatchObservationGateService:
    """Evaluate aggregate embedding batch observations without handling vectors."""

    def __init__(
        self,
        approval_packet_service: LegalRagEmbeddingBatchApprovalPacketService | None = None,
    ) -> None:
        self.approval_packet_service = approval_packet_service or LegalRagEmbeddingBatchApprovalPacketService()

    def build_gate(
        self,
        source_rows: list[dict[str, Any]] | None = None,
        observation_rows: Any = None,
    ) -> dict[str, Any]:
        approval_packet = self.approval_packet_service.build_packet(source_rows)
        observations = self._observations(observation_rows)
        observation_map = self._observation_map(observations)
        rows = [
            self._observation_row(index, approval_item, observation_map)
            for index, approval_item in enumerate(approval_packet["approval_items"], 1)
        ]
        status_counts = Counter(row["observation_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        ready_rows = [row for row in rows if row["observation_status"] == "ready_for_index_review"]
        review_rows = [row for row in rows if row["observation_status"] == "review_required"]
        blocked_rows = [row for row in rows if row["observation_status"] == "blocked"]
        pending_observations = [
            row
            for row in rows
            if row["approval_status"] == "ready_for_maintainer_approval"
            and "embedding_batch_observation_missing" in row["reason_codes"]
        ]
        status = (
            "index_commit_blocked"
            if blocked_rows
            else ("observation_review_required" if review_rows else ("ready_for_index_review" if ready_rows else "not_supplied"))
        )

        return {
            "id": "legal-rag-embedding-batch-observation-gate",
            "title": "Legal RAG embedding batch observation gate",
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "summary": {
                "observation_row_count": len(rows),
                "ready_for_index_review_count": len(ready_rows),
                "review_row_count": len(review_rows),
                "blocked_row_count": len(blocked_rows),
                "pending_observation_count": len(pending_observations),
                "observed_batch_total": sum(row["observed_batch_count"] for row in rows),
                "expected_batch_total": sum(row["expected_batch_count"] for row in rows),
                "observed_chunk_total": sum(row["observed_chunk_count"] for row in rows),
                "expected_chunk_total": sum(row["expected_chunk_count"] for row in rows),
                "observed_vector_slot_total": sum(row["observed_vector_slot_count"] for row in rows),
                "expected_vector_slot_total": sum(row["expected_vector_slot_count"] for row in rows),
                "observed_token_total": sum(row["observed_token_count"] for row in rows),
                "expected_token_total": sum(row["expected_token_count"] for row in rows),
                "observed_cost_usd": round(sum(row["observed_cost_usd"] for row in rows), 8),
                "expected_cost_usd": round(sum(row["expected_cost_usd"] for row in rows), 8),
                "max_cost_delta_usd": max(0.0, max((row["cost_delta_usd"] for row in rows), default=0.0)),
                "max_parallel_embedding_requests": MAX_PARALLEL_EMBEDDING_REQUESTS,
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "approval_packet_status": approval_packet["status"],
                "approval_record_written": False,
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "embeddings_created_by_gate": False,
                "index_written": False,
                "database_written": False,
                "source_ids_returned": False,
                "source_approval_item_ids_returned": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "embedding_vectors_included": False,
                "credentials_included": False,
            },
            "observation_rows": rows,
            "observation_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "ready_row_ids": [row["id"] for row in ready_rows],
            "review_row_ids": [row["id"] for row in review_rows],
            "blocked_row_ids": [row["id"] for row in blocked_rows],
            "linked_gate_summary": {
                "legal_rag_embedding_batch_observation_gate": status,
                "legal_rag_embedding_batch_approval_packet": approval_packet["status"],
                "legal_rag_embedding_batch_budget_gate": approval_packet["linked_gate_summary"][
                    "legal_rag_embedding_batch_budget_gate"
                ],
                "legal_rag_embedding_index_dry_run_gate": approval_packet["linked_gate_summary"][
                    "legal_rag_embedding_index_dry_run_gate"
                ],
                "legal_rag_embedding_chunk_policy_gate": approval_packet["linked_gate_summary"][
                    "legal_rag_embedding_chunk_policy_gate"
                ],
                "modelops_gemini_embedding_cheap_first_preflight": approval_packet["linked_gate_summary"][
                    "modelops_gemini_embedding_cheap_first_preflight"
                ],
                "embedding_default_model": task_default_model("embedding"),
            },
            "input_contract": {
                "accepted_container_keys": [
                    "observations",
                    "embedding_observations",
                    "batch_observations",
                    "observation_rows",
                    "rows",
                ],
                "accepted_observation_fields": [
                    "queue_order",
                    "source_type",
                    "observed_status",
                    "observed_batch_count",
                    "observed_chunk_count",
                    "observed_vector_slot_count",
                    "observed_token_count",
                    "observed_cost_usd",
                    "reason_codes",
                    "signals",
                ],
                "forbidden_fields_ignored": sorted(
                    set(approval_packet["input_contract"]["forbidden_fields_ignored"])
                    | {
                        "source_id",
                        "source_ids",
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
                        "approver_name",
                        "approval_signature",
                    }
                ),
                "source_id_echoed": False,
                "source_approval_item_id_echoed": False,
                "approval_identity_collected": False,
                "approval_record_written": False,
                "aggregate_observations_only": True,
            },
            "observation_policy": {
                "method": "metadata_only_embedding_batch_observation_gate",
                "requires_external_approval_before_run": True,
                "requires_external_batch_observation": True,
                "requires_vector_slot_match": True,
                "requires_cost_within_review_multiplier": COST_REVIEW_MULTIPLIER,
                "requires_token_within_review_multiplier": TOKEN_REVIEW_MULTIPLIER,
                "max_parallel_embedding_requests": MAX_PARALLEL_EMBEDDING_REQUESTS,
                "embedding_creation_allowed": False,
                "model_call_allowed": False,
                "index_write_allowed": False,
                "database_write_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "maintainer_approval_claimed": False,
                "embedding_batch_executed_claimed_by_gate": False,
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "index_quality_claimed": False,
                "index_commit_claimed": False,
                "automatic_index_write_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claims": [
                    "The repository can evaluate sanitized aggregate embedding batch observations after an external run.",
                    "The gate maps observed counts, vector-slot totals, and cost deltas to index-review actions.",
                ],
                "forbidden_claims": [
                    "Do not claim this gate executed embeddings, stored vectors, approved maintainers, or committed an index.",
                    "Do not claim live pricing, retrieval quality, legal answer quality, or vector quality from aggregate observations.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_source_ids": False,
                "returns_source_approval_item_ids": False,
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
                "returns_approver_identity": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "calls_model": False,
                "creates_embeddings": False,
                "writes_index": False,
                "writes_database": False,
                "writes_approval_record": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(ready_rows, review_rows, blocked_rows, pending_observations),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_batch_observation_gate.py tests/test_legal_rag_embedding_batch_approval_packet.py -q",
                "python -m pytest tests/test_legal_rag_embedding_batch_observation_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _observation_row(
        self,
        index: int,
        approval_item: dict[str, Any],
        observation_map: dict[int, dict[str, Any]],
    ) -> dict[str, Any]:
        observation = observation_map.get(_non_negative_int(approval_item.get("queue_order"))) or {}
        expected_batches = _non_negative_int(approval_item.get("planned_batch_count"))
        expected_chunks = _non_negative_int(approval_item.get("planned_chunk_count"))
        expected_tokens = _non_negative_int(approval_item.get("estimated_token_count"))
        expected_cost = _safe_float(approval_item.get("estimated_batch_cost_usd"))
        observed_batches = _non_negative_int(observation.get("observed_batch_count") or observation.get("batch_count"))
        observed_chunks = _non_negative_int(observation.get("observed_chunk_count") or observation.get("chunk_count"))
        observed_vector_slots = _non_negative_int(
            observation.get("observed_vector_slot_count")
            or observation.get("vector_slot_count")
            or observation.get("observed_vector_count")
        )
        observed_tokens = _non_negative_int(observation.get("observed_token_count") or observation.get("token_count"))
        observed_cost = _safe_float(observation.get("observed_cost_usd") or observation.get("cost_usd"))
        reason_codes = self._reason_codes(
            approval_item=approval_item,
            observation=observation,
            expected_batches=expected_batches,
            expected_chunks=expected_chunks,
            expected_tokens=expected_tokens,
            expected_cost=expected_cost,
            observed_batches=observed_batches,
            observed_chunks=observed_chunks,
            observed_vector_slots=observed_vector_slots,
            observed_tokens=observed_tokens,
            observed_cost=observed_cost,
        )
        observation_status = self._observation_status(reason_codes)
        return {
            "id": f"embedding-batch-observation-{index}-{_safe_token(approval_item.get('source_type'))}",
            "source_type": _safe_token(approval_item.get("source_type")),
            "queue_order": _non_negative_int(approval_item.get("queue_order")),
            "approval_status": str(approval_item.get("approval_status") or "blocked_until_budget_ready"),
            "approval_run_action": str(approval_item.get("run_action") or "block_embedding_run"),
            "observed_status": self._observed_status(observation),
            "observation_status": observation_status,
            "release_action": self._release_action(observation_status),
            "expected_batch_count": expected_batches,
            "observed_batch_count": observed_batches,
            "batch_count_delta": observed_batches - expected_batches,
            "expected_chunk_count": expected_chunks,
            "observed_chunk_count": observed_chunks,
            "chunk_count_delta": observed_chunks - expected_chunks,
            "expected_vector_slot_count": expected_chunks,
            "observed_vector_slot_count": observed_vector_slots,
            "vector_slot_delta": observed_vector_slots - expected_chunks,
            "expected_token_count": expected_tokens,
            "observed_token_count": observed_tokens,
            "token_delta": observed_tokens - expected_tokens,
            "expected_cost_usd": expected_cost,
            "observed_cost_usd": observed_cost,
            "cost_delta_usd": round(observed_cost - expected_cost, 8),
            "max_parallel_embedding_requests": MAX_PARALLEL_EMBEDDING_REQUESTS,
            "embedding_model": task_default_model("embedding"),
            "canonical_embedding_model": canonical_model_id(task_default_model("embedding")),
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "legal-rag-embedding-batch-observation-gate",
                "legal-rag-embedding-batch-approval-packet",
                "legal-rag-embedding-batch-budget-gate",
                "legal-rag-embedding-index-dry-run-gate",
                "legal-rag-embedding-chunk-policy-gate",
                "modelops-gemini-embedding-cheap-first-preflight",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "source_approval_item_ids_returned": False,
                "raw_legal_text_returned": False,
                "source_chunks_returned": False,
                "embedding_vectors_returned": False,
                "approver_identity_returned": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "approval_record_written": False,
                "database_written": False,
                "index_written": False,
                "credentials_returned": False,
            },
        }

    def _reason_codes(
        self,
        *,
        approval_item: dict[str, Any],
        observation: dict[str, Any],
        expected_batches: int,
        expected_chunks: int,
        expected_tokens: int,
        expected_cost: float,
        observed_batches: int,
        observed_chunks: int,
        observed_vector_slots: int,
        observed_tokens: int,
        observed_cost: float,
    ) -> list[str]:
        codes: list[str] = []
        approval_status = str(approval_item.get("approval_status") or "")
        observed_status = self._observed_status(observation)
        if approval_status == "blocked_until_budget_ready":
            codes.append("approval_packet_blocked")
        elif approval_status != "ready_for_maintainer_approval":
            codes.append(f"approval_packet_not_ready:{approval_status or 'unknown'}")
        if not observation:
            codes.append("embedding_batch_observation_missing")
        elif observed_status in {"failed", "blocked", "error"}:
            codes.append(f"embedding_batch_observed_failure:{observed_status}")
        elif observed_status not in {"success", "completed", "ready"}:
            codes.append(f"embedding_batch_observed_review:{observed_status}")
        if observation:
            if observed_batches <= 0:
                codes.append("observed_batch_count_missing")
            if expected_batches and observed_batches and observed_batches != expected_batches:
                codes.append("observed_batch_count_mismatch")
            if expected_chunks and observed_chunks and observed_chunks != expected_chunks:
                codes.append("observed_chunk_count_mismatch")
            if expected_chunks and observed_vector_slots != expected_chunks:
                codes.append("observed_vector_slot_count_mismatch")
            if expected_tokens and observed_tokens > int(expected_tokens * TOKEN_REVIEW_MULTIPLIER):
                codes.append("observed_token_over_review_limit")
            if expected_cost and observed_cost > round(expected_cost * COST_REVIEW_MULTIPLIER, 8):
                codes.append("observed_cost_over_review_limit")
        for code in self._list_value(observation, "reason_codes", "signals"):
            codes.append(f"operator_signal:{_safe_token(code)}")
        return _unique(codes) or ["embedding_batch_observation_ready"]

    def _observation_status(self, reason_codes: list[str]) -> str:
        if any(
            code.startswith("approval_packet_blocked") or code.startswith("embedding_batch_observed_failure")
            for code in reason_codes
        ):
            return "blocked"
        if reason_codes != ["embedding_batch_observation_ready"]:
            return "review_required"
        return "ready_for_index_review"

    def _release_action(self, observation_status: str) -> str:
        if observation_status == "ready_for_index_review":
            return "allow_index_commit_review_only"
        if observation_status == "review_required":
            return "hold_for_observation_review"
        return "block_index_commit"

    def _observed_status(self, observation: dict[str, Any]) -> str:
        value = str(observation.get("observed_status") or observation.get("status") or "").strip().lower()
        if value in {"success", "completed", "ready", "partial", "review", "review_required", "failed", "blocked", "error"}:
            return value
        if observation:
            return "unknown"
        return "not_supplied"

    def _observations(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [row for row in payload[:MAX_OBSERVATION_ROWS] if isinstance(row, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("embedding_observations", "batch_observations", "observations", "observation_rows", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value[:MAX_OBSERVATION_ROWS] if isinstance(row, dict)]
        return []

    def _observation_map(self, rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
        result: dict[int, dict[str, Any]] = {}
        for row in rows:
            queue_order = _non_negative_int(row.get("queue_order") or row.get("batch_queue_order"))
            if queue_order > 0 and queue_order not in result:
                result[queue_order] = row
        return result

    def _list_value(self, row: dict[str, Any], *keys: str) -> list[Any]:
        for key in keys:
            value = row.get(key)
            if isinstance(value, list):
                return value[:24]
            if isinstance(value, str):
                return [value]
        return []

    def _recommended_actions(
        self,
        ready_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        blocked_rows: list[dict[str, Any]],
        pending_observations: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Keep embedding observations aggregate-only; do not paste vectors, source chunks, raw legal text, or provider payloads.",
            "Use ready rows only as input to a separate index-commit review; this gate never writes the index.",
        ]
        if blocked_rows:
            actions.append("Block index commits for rows with blocked approval packets or failed observed embedding batches.")
        if review_rows:
            actions.append("Review vector-slot mismatches, cost/token overruns, missing observations, or held approval rows before index work.")
        if pending_observations:
            actions.append("Submit sanitized external batch observations for ready approval rows before claiming embedding-run evidence.")
        if ready_rows:
            actions.append("Attach ready observation row ids to the maintainer index-review packet, not to client-facing claims.")
        return actions


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return round(max(0.0, float(value)), 8)
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
