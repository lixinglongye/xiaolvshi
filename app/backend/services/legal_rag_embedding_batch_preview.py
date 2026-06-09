from __future__ import annotations

import hashlib
import math
from typing import Any

from schemas.aihub import EmbedTextRequest, EmbedTextResponse
from services.aihub import AIHubService


SCHEMA_VERSION = "legal-rag-embedding-batch-preview-v1"
MAX_PREVIEW_CHUNKS = 5
MAX_CHARS_PER_CHUNK = 2_000


class LegalRagEmbeddingBatchPreviewValidationError(ValueError):
    """Raised when a preview request is unsafe or malformed."""


class LegalRagEmbeddingBatchPreviewService:
    """Run a small cheap-first Legal RAG embedding preview without index writes."""

    def __init__(self, aihub_service: AIHubService | None = None) -> None:
        self.aihub_service = aihub_service or AIHubService()

    async def build_preview(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request = payload or {}
        chunks = self._normalized_chunks(request.get("chunks"))
        embed_response = await self.aihub_service.embed_text(
            EmbedTextRequest(
                input=[chunk["text"] for chunk in chunks],
                model=_optional_text(request.get("model")),
                allow_over_budget_model=bool(request.get("allow_over_budget_model", False)),
                dimensions=_optional_int(request.get("dimensions")),
            )
        )
        if len(embed_response.embeddings) != len(chunks):
            raise RuntimeError("embedding_preview_vector_count_mismatch")

        rows = [
            self._preview_row(index, chunk, vector)
            for index, (chunk, vector) in enumerate(zip(chunks, embed_response.embeddings), 1)
        ]
        return {
            "id": "legal-rag-embedding-batch-preview",
            "title": "Legal RAG embedding batch preview",
            "schema_version": SCHEMA_VERSION,
            "status": "ready",
            "summary": {
                "preview_chunk_count": len(rows),
                "embedded_vector_count": len(embed_response.embeddings),
                "dimension_count": len(embed_response.embeddings[0]) if embed_response.embeddings else 0,
                "input_character_count": sum(row["input_character_count"] for row in rows),
                "estimated_token_count": sum(row["estimated_token_count"] for row in rows),
                "max_preview_chunks": MAX_PREVIEW_CHUNKS,
                "max_chars_per_chunk": MAX_CHARS_PER_CHUNK,
                "model_called": True,
                "gateway_called": True,
                "embeddings_created": True,
                "index_written": False,
                "database_written": False,
                "source_text_returned": False,
                "source_ids_returned": False,
                "embedding_vectors_returned": False,
                "credentials_returned": False,
            },
            "model": embed_response.model,
            "task": embed_response.task,
            "budget_decision": embed_response.budget_decision,
            "task_inference": embed_response.task_inference,
            "usage": embed_response.usage,
            "usage_units": embed_response.usage_units,
            "preview_rows": rows,
            "runtime_policy": {
                "method": "cheap_first_embedding_batch_preview",
                "endpoint": "/api/v1/legal-rag/embedding-batch-preview",
                "uses_aihub_embedding_runtime": True,
                "default_model": "APP_AI_EMBEDDING_MODEL",
                "max_parallel_requests": 1,
                "max_preview_chunks": MAX_PREVIEW_CHUNKS,
                "max_chars_per_chunk": MAX_CHARS_PER_CHUNK,
                "writes_index": False,
                "writes_database": False,
                "returns_source_text": False,
                "returns_embedding_vectors": False,
            },
            "privacy_boundary": {
                "metadata_only_response": True,
                "returns_chunk_text": False,
                "returns_raw_legal_text": False,
                "returns_source_ids": False,
                "returns_embedding_vectors": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "writes_index": False,
                "writes_database": False,
            },
            "recommended_actions": [
                "Use this endpoint for one-off maintainer smoke checks before any durable index commit.",
                "Keep production indexing behind approval and post-run observation gates; this preview never writes vectors.",
            ],
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_batch_preview.py tests/test_legal_rag_router.py tests/test_aihub_runtime_routing.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
            ],
        }

    def _normalized_chunks(self, chunks: Any) -> list[dict[str, str]]:
        if not isinstance(chunks, list) or not chunks:
            raise LegalRagEmbeddingBatchPreviewValidationError("embedding_preview_chunks_required")
        if len(chunks) > MAX_PREVIEW_CHUNKS:
            raise LegalRagEmbeddingBatchPreviewValidationError("embedding_preview_chunk_limit_exceeded")

        normalized: list[dict[str, str]] = []
        for index, chunk in enumerate(chunks, 1):
            if not isinstance(chunk, dict):
                raise LegalRagEmbeddingBatchPreviewValidationError("embedding_preview_chunk_must_be_object")
            text = str(chunk.get("text") or "").strip()
            if not text:
                raise LegalRagEmbeddingBatchPreviewValidationError("embedding_preview_chunk_text_required")
            if len(text) > MAX_CHARS_PER_CHUNK:
                raise LegalRagEmbeddingBatchPreviewValidationError("embedding_preview_chunk_text_too_large")
            normalized.append(
                {
                    "ordinal_ref": f"preview-chunk-{index:03d}",
                    "input_chunk_id_hash": _digest(str(chunk.get("chunk_id") or index)),
                    "text": text,
                    "text_hash": _digest(text),
                }
            )
        return normalized

    def _preview_row(self, index: int, chunk: dict[str, str], vector: list[float]) -> dict[str, Any]:
        return {
            "ordinal_ref": chunk["ordinal_ref"],
            "input_chunk_id_hash": chunk["input_chunk_id_hash"],
            "text_hash": chunk["text_hash"],
            "input_character_count": len(chunk["text"]),
            "estimated_token_count": _estimate_tokens(chunk["text"]),
            "vector_dimension_count": len(vector),
            "vector_l2_norm": round(math.sqrt(sum(value * value for value in vector)), 8),
            "vector_checksum": _vector_checksum(index, vector),
            "index_write_action": "preview_only_do_not_write_index",
        }


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _vector_checksum(index: int, vector: list[float]) -> str:
    compact = ",".join(f"{float(value):.8g}" for value in vector)
    return _digest(f"{index}:{compact}")


def _estimate_tokens(value: str) -> int:
    return max(1, math.ceil(len(value) / 4))


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise LegalRagEmbeddingBatchPreviewValidationError("embedding_preview_dimensions_must_be_int") from None
    if parsed <= 0:
        raise LegalRagEmbeddingBatchPreviewValidationError("embedding_preview_dimensions_must_be_positive")
    return parsed
