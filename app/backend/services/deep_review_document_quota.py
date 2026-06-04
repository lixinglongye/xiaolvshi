from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.billing_entitlement_quota_binding import (
    BillingEntitlementQuotaBindingService,
    build_quota_subject_hash,
)

DEEP_REVIEW_DOCUMENT_QUOTA_SOURCE = "deep_review.generate_document"
DEEP_REVIEW_DOCUMENT_QUOTA_UNITS = 1


class DeepReviewDocumentQuotaError(Exception):
    """Raised when first-principles document generation is blocked by report quota."""

    def __init__(self, summary: dict[str, Any]):
        self.summary = summary
        usage_event = summary.get("last_usage_event") or {}
        self.detail = {
            "code": "report_quota_blocked",
            "decision_status": usage_event.get("decision_status") or summary.get("decision_status"),
            "reason_codes": summary.get("reason_codes") or usage_event.get("reason_codes") or [],
            "quota_window": summary.get("quota_window"),
            "reports_remaining": summary.get("reports_remaining"),
        }
        super().__init__("deep_review_document_report_quota_blocked")


def _hash_text(value: Any) -> str:
    normalized = str(value or "").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def _input_shape(value: Any, *, depth: int = 0) -> dict[str, Any]:
    if depth >= 2:
        return {"type": type(value).__name__}
    if isinstance(value, dict):
        keys = sorted(str(key) for key in value.keys())
        return {
            "type": "dict",
            "size": len(keys),
            "key_hashes": [_hash_text(key) for key in keys[:30]],
            "value_types": sorted({type(item).__name__ for item in value.values()}),
        }
    if isinstance(value, list):
        return {
            "type": "list",
            "size": len(value),
            "item_types": sorted({type(item).__name__ for item in value[:30]}),
        }
    return {"type": type(value).__name__}


def deep_review_document_quota_event_id(
    *,
    user_id: str,
    doc_type: str,
    title: str,
    input_data: dict[str, Any] | None,
    language: str,
) -> str:
    payload = {
        "schema": "deep-review-document-generation-quota.v1",
        "quota_subject_hash": build_quota_subject_hash(user_id),
        "doc_type_hash": _hash_text(doc_type),
        "title_hash": _hash_text(title),
        "language_hash": _hash_text(language),
        "input_shape": _input_shape(input_data or {}),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"deep_review_document_{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:32]}"


def safe_deep_review_document_quota_summary(summary: dict[str, Any]) -> dict[str, Any]:
    usage_event = summary.get("last_usage_event") or {}
    return {
        "decision_status": usage_event.get("decision_status") or summary.get("decision_status"),
        "reason_codes": list(usage_event.get("reason_codes") or summary.get("reason_codes") or []),
        "quota_window": summary.get("quota_window"),
        "reports_remaining": summary.get("reports_remaining"),
        "privacy_boundary": {
            "raw_document_text_included": False,
            "input_data_included": False,
            "title_included": False,
            "pii_included": False,
        },
    }


async def consume_deep_review_document_quota(
    db: AsyncSession,
    *,
    current_user: Any,
    doc_type: str,
    title: str,
    input_data: dict[str, Any] | None,
    language: str,
) -> dict[str, Any]:
    user_id = str(current_user.id)
    summary = await BillingEntitlementQuotaBindingService(db).consume_report_usage(
        user_id=user_id,
        user_role=getattr(current_user, "role", "user"),
        quota_subject_hash=build_quota_subject_hash(user_id),
        source=DEEP_REVIEW_DOCUMENT_QUOTA_SOURCE,
        event_id=deep_review_document_quota_event_id(
            user_id=user_id,
            doc_type=doc_type,
            title=title,
            input_data=input_data,
            language=language,
        ),
        units=DEEP_REVIEW_DOCUMENT_QUOTA_UNITS,
    )
    usage_event = summary.get("last_usage_event") or {}
    if usage_event.get("decision_status") == "blocked":
        raise DeepReviewDocumentQuotaError(summary)
    return safe_deep_review_document_quota_summary(summary)
