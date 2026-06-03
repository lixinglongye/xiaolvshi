from __future__ import annotations

import re
from typing import Any, Mapping


SAFE_METADATA_SCHEMA_VERSION = "case-request-metadata-v1"
SAFE_LEGAL_RAG_SCHEMA_VERSION = "legal-rag-research-safe-metadata-v1"
MAX_SOURCE_IDS = 32
MAX_REASON_CODES = 24
MAX_FRESHNESS_STATUSES = 12
MAX_NUMERIC_FIELDS = 24
SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_.-]{0,127}$")


def sanitize_case_request_metadata(value: Any) -> dict[str, Any] | None:
    """Keep only privacy-safe Legal RAG metadata from a case request payload."""
    record = _record(value)
    if not record:
        return None

    legal_rag = _record(record.get("legal_rag")) or record
    selected_source_ids = _safe_tokens(
        record.get("legal_rag_selected_source_ids") or legal_rag.get("selected_source_ids"),
        limit=MAX_SOURCE_IDS,
    )
    if not selected_source_ids:
        return None

    sanitized_legal_rag = {
        "schema_version": SAFE_LEGAL_RAG_SCHEMA_VERSION,
        "selected_source_ids": selected_source_ids,
        "selected_source_count": _safe_int(legal_rag.get("selected_source_count"), len(selected_source_ids)),
        "plan_status": _safe_token(legal_rag.get("plan_status"), "unknown"),
        "evaluation_status": _safe_token(legal_rag.get("evaluation_status"), "unknown"),
        "blocked": bool(legal_rag.get("blocked")),
        "freshness_statuses": _safe_tokens(legal_rag.get("freshness_statuses"), limit=MAX_FRESHNESS_STATUSES),
        "coverage_counts": _safe_number_record(legal_rag.get("coverage_counts")),
        "reason_codes": _safe_tokens(legal_rag.get("reason_codes"), limit=MAX_REASON_CODES),
        "metric_scores": _safe_number_record(legal_rag.get("metric_scores")),
        "unsupported_claim_count": _safe_int(legal_rag.get("unsupported_claim_count"), 0),
        "pii_finding_count": _safe_int(legal_rag.get("pii_finding_count"), 0),
        "evaluated_at": _safe_text(legal_rag.get("evaluated_at"), 64),
        "privacy_boundary": {
            "raw_legal_text_included": False,
            "user_claims_included": False,
            "pii_included": False,
        },
    }

    sanitized = {
        "schema_version": SAFE_METADATA_SCHEMA_VERSION,
        "source_component": _safe_token(record.get("source_component"), "case_detail_page"),
        "purpose": _safe_token(record.get("purpose"), "case_request"),
        "legal_rag_selected_source_ids": selected_source_ids,
        "legal_rag": sanitized_legal_rag,
        "privacy_boundary": {
            "raw_legal_text_included": False,
            "user_claims_included": False,
            "pii_included": False,
        },
    }
    document_type = _safe_text(record.get("document_type"), 80)
    if document_type:
        sanitized["document_type"] = document_type
    return sanitized


def legal_rag_metadata_prompt_lines(metadata: Mapping[str, Any] | None) -> list[str]:
    if not metadata:
        return []
    legal_rag = _record(metadata.get("legal_rag")) or {}
    source_ids = _safe_tokens(metadata.get("legal_rag_selected_source_ids"), limit=MAX_SOURCE_IDS)
    if not source_ids:
        return []
    coverage = _safe_number_record(legal_rag.get("coverage_counts"))
    metrics = _safe_number_record(legal_rag.get("metric_scores"))
    return [
        "## Legal RAG metadata context",
        f"- selected_source_ids: {', '.join(source_ids)}",
        f"- plan_status: {_safe_token(legal_rag.get('plan_status'), 'unknown')}",
        f"- evaluation_status: {_safe_token(legal_rag.get('evaluation_status'), 'unknown')}",
        f"- blocked: {bool(legal_rag.get('blocked'))}",
        f"- freshness_statuses: {', '.join(_safe_tokens(legal_rag.get('freshness_statuses'), limit=MAX_FRESHNESS_STATUSES)) or 'none'}",
        f"- reason_codes: {', '.join(_safe_tokens(legal_rag.get('reason_codes'), limit=MAX_REASON_CODES)) or 'none'}",
        f"- coverage_counts: {_format_number_record(coverage)}",
        f"- metric_scores: {_format_number_record(metrics)}",
        "- privacy: raw legal text, user claims, and PII are excluded from this metadata.",
    ]


def legal_rag_citation_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    source_ids = _safe_tokens((metadata or {}).get("legal_rag_selected_source_ids"), limit=MAX_SOURCE_IDS)
    if not source_ids:
        return {}
    return {
        "legal_rag_selected_source_ids": source_ids,
        "legal_rag_source_count": len(source_ids),
        "legal_rag_metadata_schema": SAFE_METADATA_SCHEMA_VERSION,
        "raw_legal_text_included": False,
        "user_claims_included": False,
        "pii_included": False,
    }


def _record(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _safe_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text[:limit]


def _safe_token(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower().replace(" ", "_")
    return text if SAFE_TOKEN_RE.match(text) else fallback


def _safe_tokens(value: Any, *, limit: int) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    else:
        try:
            candidates = list(value or [])
        except TypeError:
            candidates = []
    result: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        text = str(item or "").strip()
        if not SAFE_TOKEN_RE.match(text) or text in seen:
            continue
        seen.add(text)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def _safe_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(0, parsed)


def _safe_number_record(value: Any) -> dict[str, float]:
    record = _record(value)
    if not record:
        return {}
    result: dict[str, float] = {}
    for key, item in record.items():
        if len(result) >= MAX_NUMERIC_FIELDS:
            break
        safe_key = _safe_token(key, "")
        if not safe_key:
            continue
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            continue
        result[safe_key] = float(item)
    return result


def _format_number_record(value: Mapping[str, float]) -> str:
    if not value:
        return "none"
    return "; ".join(f"{key}={number:g}" for key, number in sorted(value.items()))
