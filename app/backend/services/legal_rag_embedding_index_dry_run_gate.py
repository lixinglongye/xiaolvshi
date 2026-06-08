from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_embedding_chunk_policy_gate import LegalRagEmbeddingChunkPolicyGateService
from services.legal_rag_embedding_readiness_gate import LegalRagEmbeddingReadinessGateService
from services.legal_rag_index_coverage_gate import LegalRagIndexCoverageGateService
from services.legal_source_durable_index_plan import LegalSourceDurableIndexPlanService
from services.legal_source_index_repository import ENTRY_PERSISTENCE_FIELDS
from services.model_catalog import canonical_model_id, task_default_model


SCHEMA_VERSION = "legal-rag-embedding-index-dry-run-gate-v1"
MAX_LAPTOP_SAFE_MANIFEST_ROWS = 64


class LegalRagEmbeddingIndexDryRunGateService:
    """Build a metadata-only dry-run manifest before any embedding index write."""

    def __init__(
        self,
        chunk_policy_service: LegalRagEmbeddingChunkPolicyGateService | None = None,
        embedding_readiness_service: LegalRagEmbeddingReadinessGateService | None = None,
        index_coverage_service: LegalRagIndexCoverageGateService | None = None,
        durable_index_plan_service: LegalSourceDurableIndexPlanService | None = None,
    ) -> None:
        self.chunk_policy_service = chunk_policy_service or LegalRagEmbeddingChunkPolicyGateService()
        self.embedding_readiness_service = embedding_readiness_service or LegalRagEmbeddingReadinessGateService()
        self.index_coverage_service = index_coverage_service or LegalRagIndexCoverageGateService()
        self.durable_index_plan_service = durable_index_plan_service or LegalSourceDurableIndexPlanService()

    def build_gate(self, source_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        chunk_gate = self.chunk_policy_service.build_gate(source_rows)
        embedding_gate = self.embedding_readiness_service.build_gate()
        index_gate = self.index_coverage_service.build_gate()
        durable_plan = self.durable_index_plan_service.build_plan()
        rows = [self._dry_run_row(index, row) for index, row in enumerate(chunk_gate["chunk_policy_rows"], 1)]
        status_counts = Counter(row["dry_run_status"] for row in rows)
        commit_counts = Counter(row["commit_action"] for row in rows)
        blocked_rows = [row for row in rows if row["dry_run_status"] == "blocked"]
        review_rows = [row for row in rows if row["dry_run_status"] == "review_required"]
        planned_chunk_total = sum(row["planned_chunk_count"] for row in rows)
        manifest_over_limit = len(rows) > MAX_LAPTOP_SAFE_MANIFEST_ROWS

        return {
            "id": "legal-rag-embedding-index-dry-run-gate",
            "title": "Legal RAG embedding index dry-run gate",
            "schema_version": SCHEMA_VERSION,
            "status": "blocked" if blocked_rows or manifest_over_limit else ("ready_with_review" if review_rows else "ready"),
            "summary": {
                "dry_run_row_count": len(rows),
                "manifest_ready_row_count": status_counts.get("ready", 0),
                "review_row_count": status_counts.get("review_required", 0),
                "blocked_row_count": status_counts.get("blocked", 0),
                "planned_chunk_total": planned_chunk_total,
                "planned_vector_slot_total": planned_chunk_total,
                "manifest_over_laptop_safe_limit": manifest_over_limit,
                "max_laptop_safe_manifest_rows": MAX_LAPTOP_SAFE_MANIFEST_ROWS,
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "chunk_policy_gate_status": chunk_gate["status"],
                "durable_index_plan_status": durable_plan["status"],
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "embeddings_created": False,
                "index_written": False,
                "database_written": False,
                "source_ids_returned": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "embedding_vectors_included": False,
                "credentials_included": False,
            },
            "dry_run_rows": rows,
            "dry_run_status_counts": dict(sorted(status_counts.items())),
            "commit_action_counts": dict(sorted(commit_counts.items())),
            "linked_gate_summary": {
                "legal_rag_embedding_chunk_policy_gate": chunk_gate["status"],
                "legal_rag_embedding_readiness_gate": embedding_gate["status"],
                "legal_rag_index_coverage_gate": index_gate["status"],
                "legal_source_durable_index_plan": durable_plan["status"],
                "legal_source_index_repository": "validates_before_upsert",
                "embedding_default_model": task_default_model("embedding"),
                "chunk_policy_schema_version": chunk_gate["schema_version"],
                "durable_index_schema_version": durable_plan["schema_version"],
            },
            "input_contract": {
                "accepted_source_fields": list(chunk_gate["input_contract"]["accepted_fields"]),
                "accepted_manifest_fields": [
                    "source_type",
                    "jurisdiction_status",
                    "freshness_status",
                    "chunk_policy_status",
                    "planned_chunk_count",
                    "embedding_model",
                    "canonical_embedding_model",
                    "release_action",
                ],
                "repository_persistence_fields": list(ENTRY_PERSISTENCE_FIELDS),
                "forbidden_fields_ignored": list(chunk_gate["input_contract"]["forbidden_fields_ignored"]),
                "source_id_echoed": False,
                "dry_run_only": True,
            },
            "dry_run_policy": {
                "method": "metadata_only_embedding_index_manifest_dry_run",
                "requires_ready_embedding_readiness_gate": True,
                "requires_ready_chunk_policy_rows": True,
                "blocks_on_blocked_chunk_policy": True,
                "review_on_review_required_chunk_policy": True,
                "max_laptop_safe_manifest_rows": MAX_LAPTOP_SAFE_MANIFEST_ROWS,
                "embedding_creation_allowed": False,
                "index_write_allowed": False,
                "database_write_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "chunk_quality_claimed": False,
                "index_quality_claimed": False,
                "index_commit_claimed": False,
                "vector_store_quality_claimed": False,
                "automatic_index_write_claimed": False,
                "allowed_claims": [
                    "The repository exposes a metadata-only dry-run manifest before embedding index writes.",
                    "Dry-run rows connect chunk-policy status, planned chunk counts, and durable-index write gates.",
                ],
                "forbidden_claims": [
                    "Do not claim that embeddings were created, vectors were stored, or durable index rows were written.",
                    "Do not claim retrieval, legal answer, or vector-store quality from the dry-run manifest.",
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
                "creates_embeddings": False,
                "writes_index": False,
                "writes_database": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows, manifest_over_limit),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_index_dry_run_gate.py tests/test_legal_rag_embedding_chunk_policy_gate.py tests/test_legal_source_durable_index_plan.py -q",
                "python -m pytest tests/test_legal_rag_embedding_index_dry_run_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _dry_run_row(self, index: int, chunk_row: dict[str, Any]) -> dict[str, Any]:
        chunk_status = str(chunk_row.get("chunk_policy_status") or "blocked")
        planned_chunks = _non_negative_int(chunk_row.get("planned_chunk_count"))
        over_manifest_limit = planned_chunks > MAX_LAPTOP_SAFE_MANIFEST_ROWS
        reason_codes = self._reason_codes(chunk_status, planned_chunks, over_manifest_limit)
        dry_run_status = self._status(reason_codes)
        return {
            "id": f"index-dry-run-row-{index}-{_safe_token(chunk_row.get('source_type'))}",
            "source_type": _safe_token(chunk_row.get("source_type")),
            "chunk_policy_status": chunk_status,
            "chunk_release_action": str(chunk_row.get("release_action") or "block_embedding_chunking"),
            "dry_run_status": dry_run_status,
            "commit_action": self._commit_action(dry_run_status),
            "estimated_token_count": _non_negative_int(chunk_row.get("estimated_token_count")),
            "planned_chunk_count": planned_chunks,
            "planned_vector_slot_count": planned_chunks,
            "over_laptop_safe_manifest_limit": over_manifest_limit,
            "embedding_model": task_default_model("embedding"),
            "canonical_embedding_model": canonical_model_id(task_default_model("embedding")),
            "manifest_fields": [
                "source_type",
                "jurisdiction_status",
                "freshness_status",
                "chunk_policy_status",
                "planned_chunk_count",
                "embedding_model",
                "canonical_embedding_model",
                "index_version",
                "metadata_hash_required",
            ],
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "legal-rag-embedding-index-dry-run-gate",
                "legal-rag-embedding-chunk-policy-gate",
                "legal-rag-embedding-readiness-gate",
                "legal-source-durable-index-plan",
                "legal-source-index-repository",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_legal_text_returned": False,
                "source_chunks_returned": False,
                "embedding_vectors_returned": False,
                "database_written": False,
                "index_written": False,
                "credentials_returned": False,
            },
        }

    def _reason_codes(
        self,
        chunk_status: str,
        planned_chunks: int,
        over_manifest_limit: bool,
    ) -> list[str]:
        codes: list[str] = []
        if planned_chunks <= 0:
            codes.append("empty_chunk_manifest")
        if chunk_status == "blocked":
            codes.append("chunk_policy_blocked")
        elif chunk_status != "ready":
            codes.append(f"chunk_policy_requires_review:{chunk_status}")
        if over_manifest_limit:
            codes.append("manifest_chunk_count_exceeds_laptop_safe_limit")
        return codes or ["embedding_index_dry_run_ready"]

    def _status(self, reason_codes: list[str]) -> str:
        if any(code in {"empty_chunk_manifest", "chunk_policy_blocked"} for code in reason_codes):
            return "blocked"
        if any(code != "embedding_index_dry_run_ready" for code in reason_codes):
            return "review_required"
        return "ready"

    def _commit_action(self, status: str) -> str:
        if status == "ready":
            return "allow_manifest_review_only"
        if status == "review_required":
            return "review_before_index_manifest"
        return "block_index_write"

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        manifest_over_limit: bool,
    ) -> list[str]:
        actions = [
            "Keep embedding index dry-runs metadata-only until chunk policy, embedding readiness, and durable index validation agree.",
            "Treat planned vector slots as estimates only; do not create embeddings or write durable index rows from this gate.",
        ]
        if blocked_rows:
            actions.append("Fix blocked chunk-policy rows before preparing any embedding index write manifest.")
        if review_rows:
            actions.append("Route review-required chunk-policy rows to maintainer review before manifest approval.")
        if manifest_over_limit:
            actions.append("Split the dry-run manifest into smaller local batches before running laptop validation.")
        return actions


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_token(value: Any) -> str:
    text = str(value or "unknown").strip()
    return "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in text)[:80] or "unknown"
