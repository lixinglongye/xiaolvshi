from __future__ import annotations

from collections import Counter
import hashlib
import math
import re
from typing import Any

from services.legal_rag_embedding_batch_preview import MAX_CHARS_PER_CHUNK, MAX_PREVIEW_CHUNKS
from services.model_catalog import canonical_model_id, estimate_token_cost_usd, model_profile, resolve_model


SCHEMA_VERSION = "legal-rag-embedding-batch-preflight-v1"
MAX_PREFLIGHT_CHUNKS = 25
MAX_PREFLIGHT_CHARS_PER_CHUNK = 4_000

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|authorization\s*:\s*bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._-]{16,})",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\s-]{7,}\d)(?!\d)")
ID_CARD_PATTERN = re.compile(r"(?<!\d)(?:\d{15}|\d{17}[\dXx])(?!\d)")


class LegalRagEmbeddingBatchPreflightService:
    """Inspect embedding batch inputs locally before any gateway call."""

    def build_preflight(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        request = payload or {}
        chunks_value = request.get("chunks")
        chunks = chunks_value if isinstance(chunks_value, list) else []
        requested_model = _optional_text(request.get("model")) or "auto-embedding"
        resolved_model = resolve_model(requested_model, task="embedding")
        canonical_model = canonical_model_id(resolved_model)
        profile = model_profile(resolved_model)
        rows = [self._row(index, chunk) for index, chunk in enumerate(chunks[:MAX_PREFLIGHT_CHUNKS], 1)]
        self._mark_duplicate_hashes(rows)

        request_reason_codes = self._request_reason_codes(chunks_value, chunks)
        status_counts = Counter(row["preflight_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        estimated_token_total = sum(row["estimated_token_count"] for row in rows)
        estimated_cost = estimate_token_cost_usd(resolved_model, estimated_token_total, 0)
        blocked_rows = [row for row in rows if row["preflight_status"] == "blocked"]
        review_rows = [row for row in rows if row["preflight_status"] == "review_required"]
        preview_eligible = (
            not request_reason_codes
            and not blocked_rows
            and len(rows) <= MAX_PREVIEW_CHUNKS
            and all(row["preview_eligible"] for row in rows)
        )
        status = self._status(request_reason_codes, blocked_rows, review_rows, preview_eligible)

        return {
            "id": "legal-rag-embedding-batch-preflight",
            "title": "Legal RAG embedding batch preflight",
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "summary": {
                "input_chunk_count": len(chunks) if isinstance(chunks_value, list) else 0,
                "preflight_row_count": len(rows),
                "max_preflight_chunks": MAX_PREFLIGHT_CHUNKS,
                "max_preflight_chars_per_chunk": MAX_PREFLIGHT_CHARS_PER_CHUNK,
                "max_preview_chunks": MAX_PREVIEW_CHUNKS,
                "max_preview_chars_per_chunk": MAX_CHARS_PER_CHUNK,
                "ready_row_count": status_counts.get("ready_for_preview", 0),
                "review_row_count": status_counts.get("review_required", 0),
                "blocked_row_count": status_counts.get("blocked", 0),
                "duplicate_text_hash_count": sum(1 for row in rows if row["duplicate_text_hash"]),
                "secret_signal_count": sum(row["signal_counts"].get("secret", 0) for row in rows),
                "pii_signal_count": sum(
                    sum(row["signal_counts"].get(kind, 0) for kind in ("email", "phone", "id_card"))
                    for row in rows
                ),
                "estimated_token_total": estimated_token_total,
                "estimated_cost_usd": estimated_cost,
                "pricing_estimate_available": estimated_cost is not None,
                "requested_model": requested_model,
                "resolved_model": resolved_model,
                "canonical_model": canonical_model,
                "model_cost_tier": profile.cost_tier if profile else "unknown",
                "model_status": profile.status if profile else "unknown",
                "preview_eligible": preview_eligible,
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "embeddings_created": False,
                "index_written": False,
                "database_written": False,
                "source_text_returned": False,
                "source_ids_returned": False,
                "embedding_vectors_returned": False,
                "credentials_returned": False,
            },
            "request_reason_codes": request_reason_codes,
            "preflight_rows": rows,
            "preflight_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "preflight_policy": {
                "method": "local_embedding_batch_input_audit",
                "endpoint": "/api/v1/legal-rag/embedding-batch-preflight",
                "requires_preflight_before_runtime_preview": True,
                "blocks_secret_like_inputs": True,
                "reviews_duplicate_text_hashes": True,
                "reviews_pii_signals": True,
                "reviews_preview_over_limit_batches": True,
                "model_call_allowed": False,
                "gateway_call_allowed": False,
                "embedding_creation_allowed": False,
                "index_write_allowed": False,
                "database_write_allowed": False,
            },
            "input_contract": {
                "accepted_container_key": "chunks",
                "accepted_chunk_fields": ["chunk_id", "id", "source_id", "text", "chunk_text", "content"],
                "source_identifier_hashed": True,
                "source_identifier_echoed": False,
                "raw_text_echoed": False,
                "forbidden_fields_ignored": [
                    "embedding",
                    "embedding_vector",
                    "embedding_vectors",
                    "vector",
                    "vectors",
                    "prompt",
                    "model_output",
                    "gateway_payload",
                    "gateway_response",
                    "authorization",
                    "api_key",
                    "password",
                    "secret",
                ],
            },
            "privacy_boundary": {
                "metadata_only_response": True,
                "returns_chunk_text": False,
                "returns_raw_legal_text": False,
                "returns_source_ids": False,
                "returns_sensitive_values": False,
                "returns_embedding_vectors": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "calls_model": False,
                "creates_embeddings": False,
                "writes_index": False,
                "writes_database": False,
            },
            "recommended_actions": self._recommended_actions(status, blocked_rows, review_rows, preview_eligible),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_batch_preflight.py tests/test_legal_rag_embedding_batch_preview.py tests/test_legal_rag_router.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
            ],
        }

    def _row(self, index: int, chunk: Any) -> dict[str, Any]:
        chunk_map = chunk if isinstance(chunk, dict) else {}
        text = _chunk_text(chunk_map)
        signal_counts = _signal_counts(text)
        text_hash = _digest(text) if text else None
        reason_codes = self._row_reason_codes(chunk, text, signal_counts)
        input_character_count = len(text)
        preview_eligible = (
            bool(text)
            and input_character_count <= MAX_CHARS_PER_CHUNK
            and not signal_counts.get("secret", 0)
        )
        preflight_status = self._row_status(reason_codes)
        return {
            "ordinal_ref": f"preflight-chunk-{index:03d}",
            "input_chunk_id_hash": _digest(str(_chunk_id(chunk_map) or index)),
            "text_hash": text_hash,
            "input_character_count": input_character_count,
            "estimated_token_count": _estimate_tokens(text),
            "duplicate_text_hash": False,
            "signal_counts": signal_counts,
            "sensitive_signal_types": sorted(kind for kind, count in signal_counts.items() if count),
            "preview_eligible": preview_eligible,
            "preflight_status": preflight_status,
            "release_action": self._release_action(preflight_status),
            "reason_codes": reason_codes,
            "privacy_boundary": {
                "source_id_returned": False,
                "raw_legal_text_returned": False,
                "sensitive_values_returned": False,
                "embedding_vectors_returned": False,
                "gateway_called": False,
                "model_called": False,
                "index_written": False,
                "database_written": False,
                "credentials_returned": False,
            },
        }

    def _mark_duplicate_hashes(self, rows: list[dict[str, Any]]) -> None:
        counts = Counter(row.get("text_hash") for row in rows if row.get("text_hash"))
        for row in rows:
            if row.get("text_hash") and counts[row["text_hash"]] > 1:
                row["duplicate_text_hash"] = True
                if "duplicate_text_hash" not in row["reason_codes"]:
                    row["reason_codes"].append("duplicate_text_hash")
                if row["preflight_status"] == "ready_for_preview":
                    row["preflight_status"] = "review_required"
                    row["release_action"] = self._release_action(row["preflight_status"])

    def _request_reason_codes(self, chunks_value: Any, chunks: list[Any]) -> list[str]:
        codes: list[str] = []
        if not isinstance(chunks_value, list) or not chunks:
            codes.append("embedding_preflight_chunks_required")
        if isinstance(chunks_value, list) and len(chunks) > MAX_PREFLIGHT_CHUNKS:
            codes.append("embedding_preflight_chunk_limit_exceeded")
        return codes

    def _row_reason_codes(self, chunk: Any, text: str, signal_counts: dict[str, int]) -> list[str]:
        codes: list[str] = []
        if not isinstance(chunk, dict):
            codes.append("chunk_must_be_object")
        if not text:
            codes.append("chunk_text_required")
        if len(text) > MAX_PREFLIGHT_CHARS_PER_CHUNK:
            codes.append("chunk_text_too_large_for_preflight")
        elif len(text) > MAX_CHARS_PER_CHUNK:
            codes.append("chunk_text_exceeds_runtime_preview_limit")
        if signal_counts.get("secret", 0):
            codes.append("secret_like_input_detected")
        for kind in ("email", "phone", "id_card"):
            if signal_counts.get(kind, 0):
                codes.append(f"pii_signal_detected:{kind}")
        return codes or ["embedding_batch_preflight_ready"]

    def _row_status(self, reason_codes: list[str]) -> str:
        if any(
            code
            in {
                "chunk_must_be_object",
                "chunk_text_required",
                "chunk_text_too_large_for_preflight",
                "secret_like_input_detected",
            }
            for code in reason_codes
        ):
            return "blocked"
        if reason_codes != ["embedding_batch_preflight_ready"]:
            return "review_required"
        return "ready_for_preview"

    def _status(
        self,
        request_reason_codes: list[str],
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        preview_eligible: bool,
    ) -> str:
        if request_reason_codes or blocked_rows:
            return "blocked"
        if review_rows or not preview_eligible:
            return "review_required"
        return "ready_for_preview"

    def _release_action(self, status: str) -> str:
        if status == "ready_for_preview":
            return "allow_embedding_batch_preview"
        if status == "review_required":
            return "redact_split_or_review_before_preview"
        return "block_embedding_batch_preview"

    def _recommended_actions(
        self,
        status: str,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        preview_eligible: bool,
    ) -> list[str]:
        actions = [
            "Run this local preflight before calling the embedding preview runtime.",
            "Keep source text and identifiers outside responses; use hashes and aggregate counts for review.",
        ]
        if blocked_rows:
            actions.append("Remove empty, oversized, malformed, or secret-like chunks before any gateway call.")
        if review_rows:
            actions.append("Review duplicate chunks and PII signals; redact or split before sending text to the embedding gateway.")
        if status == "ready_for_preview" and preview_eligible:
            actions.append("Proceed to a small serial runtime preview before any durable index write.")
        return actions


def _chunk_text(chunk: dict[str, Any]) -> str:
    for key in ("text", "chunk_text", "content"):
        value = chunk.get(key)
        if value is not None:
            return str(value or "").strip()
    return ""


def _chunk_id(chunk: dict[str, Any]) -> Any:
    for key in ("chunk_id", "id", "source_id"):
        value = chunk.get(key)
        if value is not None:
            return value
    return None


def _signal_counts(text: str) -> dict[str, int]:
    return {
        "secret": len(SECRET_PATTERN.findall(text)),
        "email": len(EMAIL_PATTERN.findall(text)),
        "phone": len(PHONE_PATTERN.findall(text)),
        "id_card": len(ID_CARD_PATTERN.findall(text)),
    }


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _estimate_tokens(value: str) -> int:
    if not value:
        return 0
    return max(1, math.ceil(len(value) / 4))


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None
