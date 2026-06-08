from __future__ import annotations

from collections import Counter
from math import ceil
from typing import Any

from services.legal_rag_embedding_index_dry_run_gate import LegalRagEmbeddingIndexDryRunGateService
from services.model_catalog import canonical_model_id, task_default_model
from services.model_ops_gemini_embedding_cheap_first_preflight import (
    ModelOpsGeminiEmbeddingCheapFirstPreflightService,
)


SCHEMA_VERSION = "legal-rag-embedding-batch-budget-gate-v1"
MAX_LAPTOP_SAFE_CHUNKS_PER_BATCH = 8
MAX_LAPTOP_SAFE_BATCH_TOKENS = 8_000
MAX_LAPTOP_SAFE_DAILY_TOKENS = 20_000


class LegalRagEmbeddingBatchBudgetGateService:
    """Plan cheap-first Gemini embedding batches before any model or index call."""

    def __init__(
        self,
        dry_run_service: LegalRagEmbeddingIndexDryRunGateService | None = None,
        embedding_preflight_service: ModelOpsGeminiEmbeddingCheapFirstPreflightService | None = None,
    ) -> None:
        self.dry_run_service = dry_run_service or LegalRagEmbeddingIndexDryRunGateService()
        self.embedding_preflight_service = (
            embedding_preflight_service or ModelOpsGeminiEmbeddingCheapFirstPreflightService()
        )

    def build_gate(self, source_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        dry_run_gate = self.dry_run_service.build_gate(source_rows)
        embedding_preflight = self.embedding_preflight_service.build_preflight()
        batch_price = self._batch_price(embedding_preflight)
        rows = [
            self._budget_row(index, row, batch_price)
            for index, row in enumerate(dry_run_gate["dry_run_rows"], 1)
        ]
        status_counts = Counter(row["batch_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        blocked_rows = [row for row in rows if row["batch_status"] == "blocked"]
        review_rows = [row for row in rows if row["batch_status"] == "review_required"]
        estimated_token_total = sum(row["estimated_token_count"] for row in rows)
        planned_batch_total = sum(row["planned_batch_count"] for row in rows)
        estimated_cost = round(sum(row["estimated_batch_cost_usd"] for row in rows), 8)
        daily_token_over_limit = estimated_token_total > MAX_LAPTOP_SAFE_DAILY_TOKENS
        status = "blocked" if blocked_rows else ("ready_with_review" if review_rows or daily_token_over_limit else "ready")

        return {
            "id": "legal-rag-embedding-batch-budget-gate",
            "title": "Legal RAG embedding batch budget gate",
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "summary": {
                "batch_budget_row_count": len(rows),
                "ready_row_count": status_counts.get("ready", 0),
                "review_row_count": status_counts.get("review_required", 0),
                "blocked_row_count": status_counts.get("blocked", 0),
                "planned_batch_total": planned_batch_total,
                "planned_chunk_total": sum(row["planned_chunk_count"] for row in rows),
                "estimated_token_total": estimated_token_total,
                "estimated_batch_cost_usd": estimated_cost,
                "batch_input_usd_per_million_tokens": batch_price,
                "daily_token_over_laptop_safe_limit": daily_token_over_limit,
                "max_laptop_safe_chunks_per_batch": MAX_LAPTOP_SAFE_CHUNKS_PER_BATCH,
                "max_laptop_safe_batch_tokens": MAX_LAPTOP_SAFE_BATCH_TOKENS,
                "max_laptop_safe_daily_tokens": MAX_LAPTOP_SAFE_DAILY_TOKENS,
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "dry_run_gate_status": dry_run_gate["status"],
                "embedding_preflight_status": embedding_preflight["status"],
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
            "batch_budget_rows": rows,
            "batch_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "linked_gate_summary": {
                "legal_rag_embedding_index_dry_run_gate": dry_run_gate["status"],
                "legal_rag_embedding_chunk_policy_gate": dry_run_gate["linked_gate_summary"][
                    "legal_rag_embedding_chunk_policy_gate"
                ],
                "legal_rag_embedding_readiness_gate": dry_run_gate["linked_gate_summary"][
                    "legal_rag_embedding_readiness_gate"
                ],
                "modelops_gemini_embedding_cheap_first_preflight": embedding_preflight["status"],
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "source_price": "local_modelops_gemini_embedding_cheap_first_preflight",
            },
            "input_contract": {
                "accepted_source_fields": list(dry_run_gate["input_contract"]["accepted_source_fields"]),
                "accepted_batch_fields": [
                    "source_type",
                    "dry_run_status",
                    "planned_chunk_count",
                    "estimated_token_count",
                    "embedding_model",
                    "canonical_embedding_model",
                    "batch_price_usd_per_million_tokens",
                    "release_action",
                ],
                "forbidden_fields_ignored": list(dry_run_gate["input_contract"]["forbidden_fields_ignored"]),
                "source_id_echoed": False,
                "dry_run_only": True,
                "budget_only": True,
            },
            "batch_budget_policy": {
                "method": "metadata_only_embedding_batch_budget_planning",
                "pricing_basis": "local_catalog_gemini_embedding_batch_price",
                "batch_input_usd_per_million_tokens": batch_price,
                "max_laptop_safe_chunks_per_batch": MAX_LAPTOP_SAFE_CHUNKS_PER_BATCH,
                "max_laptop_safe_batch_tokens": MAX_LAPTOP_SAFE_BATCH_TOKENS,
                "max_laptop_safe_daily_tokens": MAX_LAPTOP_SAFE_DAILY_TOKENS,
                "requires_ready_dry_run_rows": True,
                "splits_over_chunk_limit": True,
                "blocks_on_blocked_dry_run_rows": True,
                "review_on_review_required_dry_run_rows": True,
                "embedding_creation_allowed": False,
                "model_call_allowed": False,
                "index_write_allowed": False,
                "database_write_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "embedding_batch_executed_claimed": False,
                "index_quality_claimed": False,
                "index_commit_claimed": False,
                "automatic_index_write_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claims": [
                    "The repository exposes metadata-only batch budget planning before cheap Gemini embedding execution.",
                    "Batch budget rows estimate chunk splits, token totals, and local price impact from dry-run metadata.",
                ],
                "forbidden_claims": [
                    "Do not claim embeddings were created, model calls were made, or index writes were committed.",
                    "Do not claim live Gemini/NewAPI pricing accuracy or retrieval quality from this budget gate.",
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
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows, daily_token_over_limit),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_batch_budget_gate.py tests/test_legal_rag_embedding_index_dry_run_gate.py tests/test_model_ops_gemini_embedding_cheap_first_preflight.py -q",
                "python -m pytest tests/test_legal_rag_embedding_batch_budget_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _budget_row(self, index: int, dry_run_row: dict[str, Any], batch_price: float) -> dict[str, Any]:
        planned_chunks = _non_negative_int(dry_run_row.get("planned_chunk_count"))
        estimated_tokens = _non_negative_int(dry_run_row.get("estimated_token_count"))
        planned_batches = _planned_batches(planned_chunks)
        estimated_tokens_per_batch = ceil(estimated_tokens / planned_batches) if planned_batches else 0
        over_chunk_limit = planned_chunks > MAX_LAPTOP_SAFE_CHUNKS_PER_BATCH
        over_token_limit = estimated_tokens_per_batch > MAX_LAPTOP_SAFE_BATCH_TOKENS
        reason_codes = self._reason_codes(
            dry_run_status=str(dry_run_row.get("dry_run_status") or "blocked"),
            planned_batches=planned_batches,
            over_chunk_limit=over_chunk_limit,
            over_token_limit=over_token_limit,
        )
        batch_status = self._status(reason_codes)
        return {
            "id": f"embedding-batch-budget-row-{index}-{_safe_token(dry_run_row.get('source_type'))}",
            "source_type": _safe_token(dry_run_row.get("source_type")),
            "dry_run_status": str(dry_run_row.get("dry_run_status") or "blocked"),
            "batch_status": batch_status,
            "release_action": self._release_action(batch_status),
            "estimated_token_count": estimated_tokens,
            "planned_chunk_count": planned_chunks,
            "planned_batch_count": planned_batches,
            "estimated_tokens_per_batch": estimated_tokens_per_batch,
            "estimated_batch_cost_usd": round(estimated_tokens * batch_price / 1_000_000, 8),
            "batch_input_usd_per_million_tokens": batch_price,
            "over_chunk_batch_limit": over_chunk_limit,
            "over_token_batch_limit": over_token_limit,
            "embedding_model": task_default_model("embedding"),
            "canonical_embedding_model": canonical_model_id(task_default_model("embedding")),
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "legal-rag-embedding-batch-budget-gate",
                "legal-rag-embedding-index-dry-run-gate",
                "legal-rag-embedding-chunk-policy-gate",
                "legal-rag-embedding-readiness-gate",
                "modelops-gemini-embedding-cheap-first-preflight",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_legal_text_returned": False,
                "source_chunks_returned": False,
                "embedding_vectors_returned": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "database_written": False,
                "index_written": False,
                "credentials_returned": False,
            },
        }

    def _batch_price(self, embedding_preflight: dict[str, Any]) -> float:
        default_model = task_default_model("embedding")
        for row in embedding_preflight.get("embedding_rows", []):
            if row.get("model_id") == default_model:
                return float(row.get("batch_input_usd_per_million_tokens") or 0)
        return 0.0

    def _reason_codes(
        self,
        *,
        dry_run_status: str,
        planned_batches: int,
        over_chunk_limit: bool,
        over_token_limit: bool,
    ) -> list[str]:
        codes: list[str] = []
        if planned_batches <= 0:
            codes.append("empty_embedding_batch_plan")
        if dry_run_status == "blocked":
            codes.append("dry_run_row_blocked")
        elif dry_run_status != "ready":
            codes.append(f"dry_run_row_requires_review:{dry_run_status}")
        if over_chunk_limit:
            codes.append("chunk_count_requires_laptop_safe_batch_split")
        if over_token_limit:
            codes.append("batch_token_count_exceeds_laptop_safe_limit")
        return codes or ["embedding_batch_budget_ready"]

    def _status(self, reason_codes: list[str]) -> str:
        if any(code in {"empty_embedding_batch_plan", "dry_run_row_blocked"} for code in reason_codes):
            return "blocked"
        if any(code != "embedding_batch_budget_ready" for code in reason_codes):
            return "review_required"
        return "ready"

    def _release_action(self, status: str) -> str:
        if status == "ready":
            return "allow_laptop_embedding_batch_preflight"
        if status == "review_required":
            return "review_or_split_before_embedding_batch"
        return "block_embedding_batch"

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        daily_token_over_limit: bool,
    ) -> list[str]:
        actions = [
            "Keep embedding batches on gemini-embedding-001 and use batch pricing estimates before any live provider call.",
            "Run small local batches first; treat batch rows as planning evidence, not proof that embeddings or indexes exist.",
        ]
        if blocked_rows:
            actions.append("Resolve blocked dry-run rows before queueing any embedding batch.")
        if review_rows:
            actions.append("Review or split rows that exceed laptop chunk limits or require dry-run review.")
        if daily_token_over_limit:
            actions.append("Split the source set across multiple local run windows before attempting live embedding.")
        return actions


def _planned_batches(planned_chunks: int) -> int:
    if planned_chunks <= 0:
        return 0
    return ceil(planned_chunks / MAX_LAPTOP_SAFE_CHUNKS_PER_BATCH)


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_token(value: Any) -> str:
    text = str(value or "unknown").strip()
    return "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in text)[:80] or "unknown"
