from __future__ import annotations

from collections import Counter
from math import ceil
import re
from typing import Any

from services.legal_rag_embedding_readiness_gate import LegalRagEmbeddingReadinessGateService
from services.legal_rag_index_coverage_gate import LegalRagIndexCoverageGateService
from services.legal_rag_retrieval_diagnostics_gate import LegalRagRetrievalDiagnosticsGateService
from services.legal_source_durable_index_plan import (
    FORBIDDEN_FIELDS as DURABLE_INDEX_FORBIDDEN_FIELDS,
    LegalSourceDurableIndexPlanService,
)
from services.legal_source_ingestion_metadata import LegalSourceIngestionMetadataService
from services.model_catalog import canonical_model_id, task_default_model


SCHEMA_VERSION = "legal-rag-embedding-chunk-policy-gate-v1"
TARGET_CHUNK_POLICY: dict[str, dict[str, Any]] = {
    "statute": {
        "target_chunk_tokens": 512,
        "overlap_tokens": 64,
        "split_strategy": "article_or_section_boundary",
    },
    "regulation": {
        "target_chunk_tokens": 512,
        "overlap_tokens": 64,
        "split_strategy": "article_or_section_boundary",
    },
    "judicial_interpretation": {
        "target_chunk_tokens": 512,
        "overlap_tokens": 64,
        "split_strategy": "article_or_section_boundary",
    },
    "case": {
        "target_chunk_tokens": 640,
        "overlap_tokens": 80,
        "split_strategy": "issue_fact_holding_boundary",
    },
    "template": {
        "target_chunk_tokens": 384,
        "overlap_tokens": 48,
        "split_strategy": "clause_or_field_boundary",
    },
    "internal_note": {
        "target_chunk_tokens": 256,
        "overlap_tokens": 32,
        "split_strategy": "heading_or_bullet_boundary",
    },
}
MAX_LAPTOP_SAFE_CHUNKS_PER_SOURCE = 12
SUPPORTED_JURISDICTIONS = {
    "CN",
    "CN-National",
    "CN-Beijing",
    "CN-Shanghai",
    "CN-Guangdong",
    "CN-Zhejiang",
    "CN-Jiangsu",
}
FORBIDDEN_FIELDS = tuple(
    sorted(
        set(DURABLE_INDEX_FORBIDDEN_FIELDS)
        | {
            "source_text",
            "source_chunk",
            "chunk",
            "chunk_content",
            "passage",
            "embedding_values",
            "vectors",
            "source_id",
            "document_id",
            "client_id",
        }
    )
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{16,}|[^@\s]+@[^@\s]+\.[^@\s]+|password)",
    re.IGNORECASE,
)


class LegalRagEmbeddingChunkPolicyGateService:
    """Plan metadata-only source chunking before cheap Gemini embeddings."""

    def __init__(
        self,
        embedding_readiness_service: LegalRagEmbeddingReadinessGateService | None = None,
        index_coverage_service: LegalRagIndexCoverageGateService | None = None,
        retrieval_diagnostics_service: LegalRagRetrievalDiagnosticsGateService | None = None,
        durable_index_plan_service: LegalSourceDurableIndexPlanService | None = None,
        ingestion_metadata_service: LegalSourceIngestionMetadataService | None = None,
    ) -> None:
        self.embedding_readiness_service = embedding_readiness_service or LegalRagEmbeddingReadinessGateService()
        self.index_coverage_service = index_coverage_service or LegalRagIndexCoverageGateService()
        self.retrieval_diagnostics_service = retrieval_diagnostics_service or LegalRagRetrievalDiagnosticsGateService()
        self.durable_index_plan_service = durable_index_plan_service or LegalSourceDurableIndexPlanService()
        self.ingestion_metadata_service = ingestion_metadata_service or LegalSourceIngestionMetadataService()

    def build_gate(self, source_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        source_items = source_rows if isinstance(source_rows, list) else self._sample_source_rows()
        rows = [self._policy_row(index, row if isinstance(row, dict) else {}) for index, row in enumerate(source_items, 1)]
        status_counts = Counter(row["chunk_policy_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        blocked_rows = [row for row in rows if row["chunk_policy_status"] == "blocked"]
        review_rows = [row for row in rows if row["chunk_policy_status"] == "review_required"]
        embedding_gate = self.embedding_readiness_service.build_gate()
        index_gate = self.index_coverage_service.build_gate()
        diagnostics_gate = self.retrieval_diagnostics_service.build_gate()
        durable_index_plan = self.durable_index_plan_service.build_plan()
        ingestion_metadata = self.ingestion_metadata_service.build_metadata_contract()

        return {
            "id": "legal-rag-embedding-chunk-policy-gate",
            "title": "Legal RAG embedding chunk policy gate",
            "schema_version": SCHEMA_VERSION,
            "status": "blocked" if blocked_rows else ("ready_with_review" if review_rows else "ready"),
            "summary": {
                "source_row_count": len(rows),
                "ready_row_count": status_counts.get("ready", 0),
                "review_row_count": status_counts.get("review_required", 0),
                "blocked_row_count": status_counts.get("blocked", 0),
                "planned_chunk_total": sum(row["planned_chunk_count"] for row in rows),
                "estimated_token_total": sum(row["estimated_token_count"] for row in rows),
                "over_laptop_safe_chunk_limit_count": sum(1 for row in rows if row["over_laptop_safe_chunk_limit"]),
                "missing_citation_anchor_count": sum(1 for row in rows if row["citation_anchor_status"] == "missing"),
                "missing_locator_count": sum(1 for row in rows if row["retrieval_locator_status"] == "missing"),
                "forbidden_field_row_count": sum(1 for row in rows if row["forbidden_fields_present"]),
                "sensitive_value_row_count": sum(1 for row in rows if row["sensitive_value_present"]),
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "max_laptop_safe_chunks_per_source": MAX_LAPTOP_SAFE_CHUNKS_PER_SOURCE,
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "index_written": False,
                "embeddings_created": False,
                "dataset_downloaded": False,
                "source_ids_returned": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "embedding_vectors_included": False,
                "credentials_included": False,
            },
            "chunk_policy_rows": rows,
            "chunk_policy_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "target_chunk_policy": {
                source_type: dict(policy) for source_type, policy in sorted(TARGET_CHUNK_POLICY.items())
            },
            "linked_gate_summary": {
                "legal_rag_embedding_readiness_gate": embedding_gate["status"],
                "legal_rag_index_coverage_gate": index_gate["status"],
                "legal_rag_retrieval_diagnostics_gate": diagnostics_gate["status"],
                "legal_source_durable_index_plan": durable_index_plan["status"],
                "legal_source_ingestion_metadata": ingestion_metadata["status"],
                "embedding_default_model": embedding_gate["summary"]["embedding_default_model"],
                "durable_index_schema_version": durable_index_plan["schema_version"],
                "ingestion_schema_version": ingestion_metadata["schema_version"],
            },
            "input_contract": {
                "accepted_fields": [
                    "source_type",
                    "jurisdiction",
                    "freshness_status",
                    "estimated_token_count",
                    "section_count",
                    "citation_anchor_count",
                    "retrieval_locator_present",
                    "language",
                    "authority_level",
                ],
                "forbidden_fields_ignored": list(FORBIDDEN_FIELDS),
                "source_id_echoed": False,
            },
            "chunk_policy": {
                "method": "metadata_only_token_estimate_chunk_planning",
                "token_estimator": "caller_supplied_estimated_token_count",
                "max_laptop_safe_chunks_per_source": MAX_LAPTOP_SAFE_CHUNKS_PER_SOURCE,
                "requires_retrieval_locator": True,
                "requires_citation_anchor_for_ready": True,
                "stale_or_unknown_freshness_blocks_embedding": True,
                "review_due_freshness_requires_review": True,
                "index_write_allowed": False,
                "embedding_creation_allowed": False,
            },
            "claim_boundary": {
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "chunk_quality_claimed": False,
                "index_quality_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_index_write_claimed": False,
                "allowed_claims": [
                    "The repository exposes metadata-only chunk planning evidence before cheap Gemini embedding routes.",
                    "Chunk policy rows connect source metadata, token estimates, citation anchors, freshness, and locator readiness.",
                ],
                "forbidden_claims": [
                    "Do not claim live embedding creation, vector index quality, retrieval accuracy, or legal answer quality from this gate.",
                    "Do not claim that raw legal text was processed, stored, or sent to a provider.",
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
                "creates_embeddings": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_chunk_policy_gate.py tests/test_legal_rag_embedding_readiness_gate.py tests/test_legal_source_durable_index_plan.py -q",
                "python -m pytest tests/test_legal_rag_embedding_chunk_policy_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _sample_source_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "policy_row_id": "chunk-statute-sections-ready",
                "source_type": "statute",
                "jurisdiction": "CN-National",
                "freshness_status": "fresh",
                "estimated_token_count": 3200,
                "section_count": 9,
                "citation_anchor_count": 9,
                "retrieval_locator_present": True,
                "language": "zh-CN",
                "authority_level": "national_statute",
            },
            {
                "policy_row_id": "chunk-regulation-review-due",
                "source_type": "regulation",
                "jurisdiction": "CN-Beijing",
                "freshness_status": "review_due",
                "estimated_token_count": 1800,
                "section_count": 5,
                "citation_anchor_count": 2,
                "retrieval_locator_present": True,
                "language": "zh-CN",
                "authority_level": "local_regulation",
            },
            {
                "policy_row_id": "chunk-case-anchor-review",
                "source_type": "case",
                "jurisdiction": "CN-Shanghai",
                "freshness_status": "fresh",
                "estimated_token_count": 5200,
                "section_count": 4,
                "citation_anchor_count": 0,
                "retrieval_locator_present": True,
                "language": "zh-CN",
                "authority_level": "case",
            },
            {
                "policy_row_id": "chunk-template-small-ready",
                "source_type": "template",
                "jurisdiction": "CN-National",
                "freshness_status": "fresh",
                "estimated_token_count": 760,
                "section_count": 6,
                "citation_anchor_count": 3,
                "retrieval_locator_present": True,
                "language": "zh-CN",
                "authority_level": "template",
            },
            {
                "policy_row_id": "chunk-missing-locator-block",
                "source_type": "judicial_interpretation",
                "jurisdiction": "CN-National",
                "freshness_status": "fresh",
                "estimated_token_count": 900,
                "section_count": 2,
                "citation_anchor_count": 2,
                "retrieval_locator_present": False,
                "language": "zh-CN",
                "authority_level": "judicial_interpretation",
            },
            {
                "policy_row_id": "chunk-forbidden-field-block",
                "source_type": "internal_note",
                "jurisdiction": "CN",
                "freshness_status": "fresh",
                "estimated_token_count": 900,
                "section_count": 3,
                "citation_anchor_count": 2,
                "retrieval_locator_present": True,
                "raw_text": "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK",
                "embedding_vector": [0.1, 0.2],
                "language": "zh-CN",
            },
        ]

    def _policy_row(self, index: int, raw_row: dict[str, Any]) -> dict[str, Any]:
        source_type = _token(raw_row.get("source_type"), "unknown")
        policy = TARGET_CHUNK_POLICY.get(source_type, TARGET_CHUNK_POLICY["statute"])
        target_tokens = int(policy["target_chunk_tokens"])
        overlap_tokens = int(policy["overlap_tokens"])
        estimated_tokens = _non_negative_int(raw_row.get("estimated_token_count"))
        section_count = _non_negative_int(raw_row.get("section_count"))
        citation_anchor_count = _non_negative_int(raw_row.get("citation_anchor_count"))
        planned_chunks = _chunk_count(estimated_tokens, target_tokens, overlap_tokens)
        over_laptop_limit = planned_chunks > MAX_LAPTOP_SAFE_CHUNKS_PER_SOURCE
        forbidden_fields = _forbidden_paths(raw_row)
        sensitive_value_present = _contains_sensitive_value(raw_row)
        jurisdiction = _token(raw_row.get("jurisdiction"), "unknown")
        freshness_status = _token(raw_row.get("freshness_status"), "unknown")
        locator_present = bool(raw_row.get("retrieval_locator_present"))
        citation_anchor_status = "ready" if citation_anchor_count > 0 else "missing"
        retrieval_locator_status = "ready" if locator_present else "missing"
        reason_codes = self._reason_codes(
            source_type=source_type,
            jurisdiction=jurisdiction,
            freshness_status=freshness_status,
            estimated_tokens=estimated_tokens,
            citation_anchor_status=citation_anchor_status,
            retrieval_locator_status=retrieval_locator_status,
            over_laptop_limit=over_laptop_limit,
            forbidden_fields=forbidden_fields,
            sensitive_value_present=sensitive_value_present,
        )
        status = self._status(reason_codes)

        return {
            "id": _policy_row_id(raw_row, index, source_type),
            "source_type": source_type,
            "jurisdiction_status": "supported" if jurisdiction in SUPPORTED_JURISDICTIONS else "unsupported",
            "freshness_status": freshness_status,
            "estimated_token_count": estimated_tokens,
            "section_count": section_count,
            "citation_anchor_count": citation_anchor_count,
            "citation_anchor_status": citation_anchor_status,
            "retrieval_locator_status": retrieval_locator_status,
            "target_chunk_tokens": target_tokens,
            "overlap_tokens": overlap_tokens,
            "planned_chunk_count": planned_chunks,
            "over_laptop_safe_chunk_limit": over_laptop_limit,
            "split_strategy": str(policy["split_strategy"]),
            "embedding_model": task_default_model("embedding"),
            "canonical_embedding_model": canonical_model_id(task_default_model("embedding")),
            "chunk_policy_status": status,
            "release_action": self._release_action(status),
            "reason_codes": reason_codes,
            "forbidden_fields_present": forbidden_fields,
            "sensitive_value_present": sensitive_value_present,
            "linked_gate_ids": [
                "legal-rag-embedding-readiness-gate",
                "legal-rag-index-coverage-gate",
                "legal-rag-retrieval-diagnostics-gate",
                "legal-source-durable-index-plan",
                "legal-source-ingestion-metadata",
                "modelops-gemini-embedding-cheap-first-preflight",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_legal_text_returned": False,
                "source_chunks_returned": False,
                "embedding_vectors_returned": False,
                "prompt_returned": False,
                "model_output_returned": False,
                "credentials_returned": False,
            },
        }

    def _reason_codes(
        self,
        *,
        source_type: str,
        jurisdiction: str,
        freshness_status: str,
        estimated_tokens: int,
        citation_anchor_status: str,
        retrieval_locator_status: str,
        over_laptop_limit: bool,
        forbidden_fields: list[str],
        sensitive_value_present: bool,
    ) -> list[str]:
        codes: list[str] = []
        if source_type not in TARGET_CHUNK_POLICY:
            codes.append("unknown_source_type")
        if jurisdiction not in SUPPORTED_JURISDICTIONS:
            codes.append("unsupported_jurisdiction")
        if estimated_tokens <= 0:
            codes.append("empty_token_estimate")
        if retrieval_locator_status == "missing":
            codes.append("retrieval_locator_missing")
        if freshness_status in {"stale", "unknown", ""}:
            codes.append(f"freshness_blocks_embedding:{freshness_status or 'unknown'}")
        elif freshness_status != "fresh":
            codes.append(f"freshness_requires_review:{freshness_status}")
        if citation_anchor_status == "missing":
            codes.append("citation_anchor_missing")
        if over_laptop_limit:
            codes.append("chunk_count_exceeds_laptop_safe_limit")
        if forbidden_fields:
            codes.append("forbidden_field_present")
        if sensitive_value_present:
            codes.append("sensitive_value_present")
        return codes or ["chunk_policy_ready"]

    def _status(self, reason_codes: list[str]) -> str:
        blocking_prefixes = (
            "unknown_source_type",
            "unsupported_jurisdiction",
            "empty_token_estimate",
            "retrieval_locator_missing",
            "freshness_blocks_embedding",
            "forbidden_field_present",
            "sensitive_value_present",
        )
        if any(code.startswith(blocking_prefixes) for code in reason_codes):
            return "blocked"
        if any(code != "chunk_policy_ready" for code in reason_codes):
            return "review_required"
        return "ready"

    def _release_action(self, status: str) -> str:
        if status == "ready":
            return "allow_embedding_chunk_preflight"
        if status == "review_required":
            return "review_embedding_chunk_policy"
        return "block_embedding_chunking"

    def _recommended_actions(self, blocked_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Keep Legal RAG embedding chunking metadata-only until source freshness, locators, and citation anchors pass review.",
            "Use gemini-embedding-001 only after chunk policy rows avoid raw text, source ids, and embedding-vector payloads.",
        ]
        if blocked_rows:
            actions.append("Fix missing locators, unsupported jurisdictions, stale freshness, forbidden fields, or sensitive values before chunking.")
        if review_rows:
            actions.append("Review citation anchors, review-due freshness, and laptop-safe chunk limits before enabling embedding preflight.")
        return actions


def _chunk_count(estimated_tokens: int, target_tokens: int, overlap_tokens: int) -> int:
    if estimated_tokens <= 0:
        return 0
    stride = max(1, target_tokens - overlap_tokens)
    if estimated_tokens <= target_tokens:
        return 1
    return 1 + ceil((estimated_tokens - target_tokens) / stride)


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _token(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", text)[:80] or fallback


def _policy_row_id(raw_row: dict[str, Any], index: int, source_type: str) -> str:
    if "policy_row_id" in raw_row:
        return _token(raw_row.get("policy_row_id"), f"chunk-policy-row-{index}")
    return f"chunk-policy-row-{index}-{source_type}"


def _forbidden_paths(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).lower() in FORBIDDEN_FIELDS:
                paths.append(path)
            paths.extend(_forbidden_paths(nested, path))
    elif isinstance(value, list):
        for index, nested in enumerate(value[:20]):
            paths.extend(_forbidden_paths(nested, f"{prefix}[{index}]"))
    return sorted(set(paths))


def _contains_sensitive_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_sensitive_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_value(item) for item in value[:20])
    if isinstance(value, str):
        return bool(SENSITIVE_VALUE_PATTERN.search(value))
    return False
